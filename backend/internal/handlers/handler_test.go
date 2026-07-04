package handlers

import (
	"context"
	"io"
	"net/http"
	"slices"
	"strings"
	"testing"

	"github.com/m1kus3q/pubpredictor/backend/internal/message_channel"
	"github.com/m1kus3q/pubpredictor/backend/internal/minio"
	"github.com/m1kus3q/pubpredictor/backend/internal/testutils"
)

type tag struct {
	tagKey   string
	tagValue string
}

type storageMock struct {
	keys []string
	tags map[string]tag
}

func (m *storageMock) UploadObject(ctx context.Context, bucket, key string, body io.Reader) error {
	m.keys = append(m.keys, key)
	return nil
}

func (m *storageMock) SetTag(ctx context.Context, bucket, key, tagKey, tagValue string) error {
	m.tags[key] = tag{tagKey: tagKey, tagValue: tagValue}
	return nil
}

func (m *storageMock) RemoveObject(ctx context.Context, bucket, key string) error {
	idx := slices.Index(m.keys, key)
	if idx != -1 {
		m.keys = slices.Delete(m.keys, idx, idx+1)
		delete(m.tags, key)
	}
	return nil
}

func TestHandleXLSX_Success(t *testing.T) {
	storage := &storageMock{
		tags: make(map[string]tag),
	}

	handler := &UploadHandler{
		StorageClient:    storage,
		UploadBucketName: "files",
		Queue:            message_channel.NewLocalQueue(10),
	}

	req, rec := testutils.CreateDefaultUploadRequest(t)
	handler.HandleXLSX(rec, req)

	if rec.Code != http.StatusAccepted {
		t.Fatalf("expected HTTP status %d, got %d", http.StatusAccepted, rec.Code)
	}

	if len(storage.keys) != 1 {
		t.Fatalf("expected exactly one uploaded object, got %d", len(storage.keys))
	}
	key := storage.keys[0]

	if !strings.HasPrefix(key, testutils.DefaultFileName+"_") {
		t.Fatalf("expected object key to start with %q, got %q", testutils.DefaultFileName+"_", key)
	}

	expectedTag := tag{
		tagKey:   minio.TagStatus,
		tagValue: minio.StatusQueued,
	}

	if storage.tags[key] != expectedTag {
		t.Fatalf("expected object tag %+v, got %+v", expectedTag, storage.tags[key])
	}
}

func TestMultipeHandlerChanel(t *testing.T) {
	storage := &storageMock{
		tags: make(map[string]tag),
	}

	handler := &UploadHandler{
		StorageClient:    storage,
		UploadBucketName: "files",
		Queue:            message_channel.NewLocalQueue(10),
	}

	req, rec := testutils.CreateDefaultUploadRequest(t)
	handler.HandleXLSX(rec, req)

	req, rec = testutils.CreateUploadRequest(
		t,
		testutils.DefaultFileName,
		[]byte("new"+testutils.DefaultFileName),
	)

	handler.HandleXLSX(rec, req)

	req, rec = testutils.CreateUploadRequest(t, "file 2", []byte("text 2"))
	handler.HandleXLSX(rec, req)

	if len(storage.keys) != 3 {
		t.Fatalf("expected exactly one uploaded object, got %d", len(storage.keys))
	}

	jobs, err := handler.Queue.Subscribe()
	if err != nil {
		t.Fatalf("failed to subscribe to queue: %v", err)
	}

	for _, expected := range storage.keys {
		select {
		case job := <-jobs:
			if job != expected {
				t.Fatalf("expected queued object %q, got %q", expected, job)
			}
		default:
			t.Fatal("expected object to be available in queue")
		}
	}
}
