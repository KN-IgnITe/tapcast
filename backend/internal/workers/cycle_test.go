//go:build integration

package workers

import (
	"context"
	"log"
	"net/http"
	"os"
	"testing"
	"time"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	dbclient "github.com/m1kus3q/pubpredictor/backend/internal/db/client"
	"github.com/m1kus3q/pubpredictor/backend/internal/handlers"
	"github.com/m1kus3q/pubpredictor/backend/internal/message_channel"
	"github.com/m1kus3q/pubpredictor/backend/internal/minio"
	minioClient "github.com/m1kus3q/pubpredictor/backend/internal/minio/client"
	"github.com/m1kus3q/pubpredictor/backend/internal/testutils"
)

func simulateHandler(t *testing.T, handler *handlers.UploadHandler) {
	t.Helper()

	fileName := "przyklad_pos.xlsx"
	filePath := "../parser/test/przyklad_pos.xlsx"
	content, err := os.ReadFile(filePath)
	if err != nil {
		t.Fatalf("failed to read test file %q: %v", filePath, err)
	}

	req, rec := testutils.CreateUploadRequest(t, fileName, content)

	handler.HandleXLSX(rec, req)

	if rec.Code != http.StatusAccepted {
		t.Fatalf("expected HTTP status %d, got %d", http.StatusAccepted, rec.Code)
	}
}

func TestWorker(t *testing.T) {
	ctx := context.Background()
	weatherClient := weather.NewClient()

	dbConfig, err := dbclient.NewDBConfig()
	if err != nil {
		t.Fatalf("failed to load DB config: %v", err)
	}

	dbClient, err := dbclient.NewDBClient(dbConfig)
	if err != nil {
		t.Fatalf("failed to connect to DB: %v", err)
	}

	minioClient, err := minioClient.NewMinIOClientFromEnv(ctx)
	if err != nil {
		log.Fatalf("Failed to create MinIO client: %v", err)
	}

	uploadBucket := "tests"
	if err := minioClient.CreateBucketIfNotExists(ctx, uploadBucket); err != nil {
		t.Fatalf("failed to create bucket %q: %v", uploadBucket, err)
	}

	jobs_size := 10
	queue := message_channel.NewLocalQueue(jobs_size)

	handler := &handlers.UploadHandler{
		StorageClient:    minioClient,
		UploadBucketName: uploadBucket,
		Queue:            queue,
	}

	worker := &UploadWorker{
		StorageClient: minioClient,
		BucketName:    uploadBucket,
		Queue:         queue,
		DBClient:      dbClient,
		WeatherClient: weatherClient,
	}

	go worker.Run()
	simulateHandler(t, handler)

	defer func() {
		if err := minioClient.ClearBucket(ctx, uploadBucket); err != nil {
			t.Logf("failed to clear bucket: %v", err)
		}
	}()

	deadline := time.Now().Add(time.Minute)

	keys, err := minioClient.ListObjectsKeys(ctx, uploadBucket)
	if err != nil {
		t.Fatalf("failed to list uploaded objects: %v", err)
	}

	if len(keys) != 1 {
		t.Fatalf("expected exactly one uploaded object, got %d", len(keys))
	}

	key := keys[0]
	for time.Now().Before(deadline) {
		status, err := minioClient.GetTag(ctx, uploadBucket, key, minio.TagStatus)
		if err == nil && status != nil && *status == minio.StatusParsed {
			break
		}

		time.Sleep(100 * time.Millisecond)
	}

	status, err := minioClient.GetTag(
		ctx,
		uploadBucket,
		keys[0],
		minio.TagStatus,
	)
	if err != nil {
		t.Fatalf("failed to read object status: %v", err)
	}

	if status == nil {
		t.Fatal("expected object status tag")
	}

	if *status != minio.StatusParsed {
		t.Fatalf(
			"expected object status %q, got %q",
			minio.StatusParsed,
			*status,
		)
	}
}
