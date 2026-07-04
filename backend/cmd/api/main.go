package main

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	api "github.com/m1kus3q/pubpredictor/backend/internal/handlers"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	dbclient "github.com/m1kus3q/pubpredictor/backend/internal/db/client"
	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"
	"github.com/m1kus3q/pubpredictor/backend/internal/message_channel"
	"github.com/m1kus3q/pubpredictor/backend/internal/workers"

	minio "github.com/m1kus3q/pubpredictor/backend/internal/minio/client"
	pb "github.com/m1kus3q/pubpredictor/backend/pkg/pb/ping/v1"
)

type App struct {
	logger     *log.Logger
	pingClient pb.PingServiceClient
}

func (a *App) pingHandler(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), time.Second)
	defer cancel()

	grpcResp, err := a.pingClient.Ping(ctx, &pb.PingRequest{
		Message: "ping",
	})

	if err != nil {
		a.logger.Printf("gRPC Ping error: %v", err)
		http.Error(w, "failed to ping grpc server", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(grpcResp); err != nil {
		http.Error(w, "internal server error", http.StatusInternalServerError)
	}
}

func main() {
	inferenceHost := os.Getenv("INFERENCE_HOST")
	inferencePort := os.Getenv("INFERENCE_PORT")
	backend_port := os.Getenv("BACKEND_PORT")

	if inferenceHost == "" || inferencePort == "" || backend_port == "" {
		log.Fatal("INFERENCE_HOST, INFERENCE_PORT and BACKEND_PORT environment variables must be set")
		return
	}

	grpcTarget := inferenceHost + ":" + inferencePort

	// Connect to the gRPC server
	conn, err := grpc.NewClient(grpcTarget, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Failed to connect to gRPC server: %v", err)
	}
	defer func() { _ = conn.Close() }()

	app := &App{
		logger:     log.New(os.Stdout, "", log.LstdFlags),
		pingClient: pb.NewPingServiceClient(conn),
	}

	// Setup DB
	dbConfig, err := dbclient.NewDBConfig()
	if err != nil {
		log.Fatalf("Missing DB env variables: %v", err)
	}

	dbClientInstance, err := dbclient.NewDBClient(dbConfig)
	if err != nil {
		log.Fatalf("Failed to connect to DB: %v", err)
	}

	err = dbClientInstance.GetDB().AutoMigrate(
		&models.Day{},
		&models.Location{},
		&models.Bar{},
		&models.Weather{},
		&models.Article{},
		&models.Sale{},
	)

	if err != nil {
		log.Fatalf("Failed to auto-migrate database: %v", err)
	}

	// Setup
	ctx := context.Background()
	weatherClientInstance := weather.NewClient()
	minioClient, err := minio.NewMinIOClientFromEnv(ctx)
	if err != nil {
		log.Fatalf("Failed to create MinIO client: %v", err)
	}

	uploadBucketName := "files"

	jobs_size := 10
	queue := message_channel.NewLocalQueue(jobs_size)

	err = minioClient.CreateBucketIfNotExists(ctx, uploadBucketName)
	if err != nil {
		log.Fatalf("Failed to create bucket %q: %v", uploadBucketName, err)
	}

	uploadHandler := &api.UploadHandler{
		StorageClient:    minioClient,
		UploadBucketName: uploadBucketName,
		Queue:            queue,
	}

	worker := &workers.UploadWorker{
		StorageClient: minioClient,
		BucketName:    uploadBucketName,
		Queue:         queue,
		DBClient:      dbClientInstance,
		WeatherClient: weatherClientInstance,
	}

	r := chi.NewRouter()

	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(60 * time.Second))

	r.Use(cors.Handler(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders: []string{"Content-Type"},
	}))

	r.Get("/api/ping", app.pingHandler)

	r.Post("/uploadXLSX", uploadHandler.HandleXLSX)
	go worker.Run()

	srv := &http.Server{
		Addr:         ":" + backend_port,
		Handler:      r,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	go func() {
		app.logger.Printf("Starting Chi server on %s", srv.Addr)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			app.logger.Fatalf("Server error: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	<-quit

	app.logger.Println("Shutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		app.logger.Fatalf("Shutdown error: %v", err)
	}
}
