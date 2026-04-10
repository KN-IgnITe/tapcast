package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	//"github.com/m1kus3q/pubpredictor/backend/pkg/parser"

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

type UploadResponseXLSX struct {
	Message  string `json:"message"`
	Filename string `json:"filename"`
	Size     int64  `json:"size_bytes"`
}

func uploadHandlerXLSX(w http.ResponseWriter, r *http.Request) {

	if r.Method != http.MethodPost {
		http.Error(w, "Metoda niedozwolona", http.StatusMethodNotAllowed)
		return
	}

	//z fronta wysylaja FormData
	file, header, err := r.FormFile("file") //nazwa file to klucz tu musi byc tak jak w froncie
	if err != nil {
		http.Error(w, "Błąd pobierania pliku", http.StatusBadRequest)
		return
	}
	defer file.Close()

	//tu juz mamy nasz plik file

	if ext := filepath.Ext(header.Filename); ext != ".xlsx" {
		http.Error(w, "Dozwolone są tylko pliki .xlsx", http.StatusBadRequest)
		return
	}

	size, err := io.Copy(io.Discard, file)
	if err != nil {
		http.Error(w, "Błąd podczas odczytu pliku", http.StatusInternalServerError)
		return
	}

	//przewijamy strumiej na poczatek bo wczesniej przeszlismy przez caly zeby zczytac rozmiar
	_, err = file.Seek(0, io.SeekStart)
	if err != nil {
		http.Error(w, "Błąd resetowania pliku", http.StatusInternalServerError)
		return
	}

	// tu przekazujemy plik do jakies funkcji ktora go przemieli
	//err = processExcelFile(file)

	fmt.Printf("Otrzymano plik: %s (Rozmiar: %d bajtów)\n", header.Filename, size)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(UploadResponseXLSX{
		Message:  "Plik przyjęty pomyślnie",
		Filename: header.Filename,
		Size:     size,
	})
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
	defer conn.Close()

	app := &App{
		logger:     log.New(os.Stdout, "", log.LstdFlags),
		pingClient: pb.NewPingServiceClient(conn),
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

	r.Post("/uploadXLSX", uploadHandlerXLSX)


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
