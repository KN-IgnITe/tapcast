// Package testutils contains reusable testing helpers that cannot be
// shared through *_test.go files because they are used by multiple packages

package testutils

import (
	"bytes"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"testing"
)

const (
	DefaultFileName = "report.xlsx"
	DefaultFileText = "test text"
)

func CreateUploadRequest(
	t *testing.T,
	fileName string,
	content []byte,
) (*http.Request, *httptest.ResponseRecorder) {
	t.Helper()

	var body bytes.Buffer
	writer := multipart.NewWriter(&body)

	part, err := writer.CreateFormFile("file", fileName)
	if err != nil {
		t.Fatalf("failed to create multipart form file: %v", err)
	}

	if _, err := part.Write(content); err != nil {
		t.Fatalf("failed to write test file content: %v", err)
	}

	if err := writer.Close(); err != nil {
		t.Fatalf("failed to close multipart writer: %v", err)
	}

	req := httptest.NewRequest(http.MethodPost, "/uploadXLSX", &body)
	req.Header.Set("Content-Type", writer.FormDataContentType())

	rec := httptest.NewRecorder()

	return req, rec
}

func CreateDefaultUploadRequest(t *testing.T) (*http.Request, *httptest.ResponseRecorder) {
	t.Helper()
	return CreateUploadRequest(t, DefaultFileName, []byte(DefaultFileText))
}
