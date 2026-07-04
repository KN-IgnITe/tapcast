package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/google/uuid"
	"github.com/m1kus3q/pubpredictor/backend/internal/message_channel"

	"context"
	"io"

	"github.com/m1kus3q/pubpredictor/backend/internal/minio"
)

type Storage interface {
	UploadObject(ctx context.Context, bucketName string, key string, body io.Reader) error
	SetTag(ctx context.Context, bucketName string, key string, tagKey string, tagValue string) error
	RemoveObject(ctx context.Context, bucketName string, key string) error
}

// Holds DB and Weather API dependencies.
type UploadHandler struct {
	StorageClient    Storage
	UploadBucketName string
	Queue            message_channel.MessageQueue //channel to communication
}

func (h *UploadHandler) HandleXLSX(w http.ResponseWriter, r *http.Request) {

	// Get file from multipart form
	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "Failed to read file", http.StatusBadRequest)
		return
	}

	defer func() { _ = file.Close() }()

	ctx := r.Context()

	objectKey := header.Filename + "_" + uuid.New().String()
	err = h.StorageClient.UploadObject(ctx, h.UploadBucketName, objectKey, file)
	if err != nil {
		http.Error(w, "Failed to save file in storage", http.StatusInternalServerError)
		return
	}

	err = h.StorageClient.SetTag(ctx, h.UploadBucketName, objectKey, minio.TagStatus, minio.StatusQueued)
	if err != nil {
		_ = h.StorageClient.RemoveObject(ctx, h.UploadBucketName, objectKey)
		http.Error(w, "Failed to queue file for processing", http.StatusInternalServerError)
		return
	}

	err = h.Queue.Publish(objectKey)
	if err != nil {
		_ = h.StorageClient.RemoveObject(ctx, h.UploadBucketName, objectKey)
		http.Error(w, "Failed to save file", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusAccepted)
	if err := json.NewEncoder(w).Encode(map[string]string{
		"status": "accepted", "message": "file uploaded and queued for processing",
	}); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
	}
}
