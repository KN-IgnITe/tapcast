package minio

import (
	"context"
	"io"
	"slices"
	"strings"
	"testing"
)

/*
go test -v -run TestCreateClientFromEnv ./internal/minio
go test -v -run TestBucketOperationFromEnv ./internal/minio
go test -v -run TestFileOperationFromEnv ./internal/minio
go test -v -run TestBucketsListFromEnv ./internal/minio
go test -v -run TestCreateBucketsFromEnv ./internal/minio


*/

const (
	bucketName = "test-bucket"
	keyName    = "test-file"

	bucket1Name = "test-bucket-1"
	bucket2Name = "test-bucket-2"
)

func TestCreateClientFromEnv(t *testing.T) {
	minIOConfig, err := NewMinIOConfig()
	if err != nil {
		t.Fatal(err)
	}
	_, err = NewMinIOClientFromConfig(minIOConfig, context.Background())
	if err != nil {
		t.Fatal(err)
	}
}

func TestCreateBucketsFromEnv(t *testing.T) {
	ctx := context.Background()

	minioClient, err := NewMinIOClientFromEnv(ctx)
	if err != nil {
		t.Fatal(err)
	}

	err = minioClient.CreateBucketIfNotExists(ctx, bucketName)
	if err != nil {
		t.Fatal(err)
	}

}

func TestBucketsListFromEnv(t *testing.T) {
	ctx := context.Background()

	minioClient, err := NewMinIOClientFromEnv(ctx)
	if err != nil {
		t.Fatal(err)
	}

	bucketList, err := minioClient.ListBuckets(ctx)
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("list bucket: %v", bucketList)
}

func deferRemoveBucket(ctx context.Context, t *testing.T, minioClient *MinIOClient, bucketName string) {
	err := minioClient.RemoveBucket(ctx, bucketName)
	if err != nil {
		t.Error(err)
	}
}

// uwagi: brak usuniecia - poblem dla create przyszlego
func TestBucketOperationFromEnv(t *testing.T) {
	ctx := context.Background()

	minioClient, err := NewMinIOClientFromEnv(ctx)
	if err != nil {
		t.Fatal(err)
	}

	err = minioClient.CreateBucketIfNotExists(ctx, bucket1Name)
	if err != nil {
		t.Fatal(err)
	}
	defer deferRemoveBucket(ctx, t, minioClient, bucket1Name)

	err = minioClient.CreateBucketIfNotExists(ctx, bucket2Name)
	if err != nil {
		t.Fatal(err)
	}
	defer deferRemoveBucket(ctx, t, minioClient, bucket2Name)

	bucketList, err := minioClient.ListBuckets(ctx)
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("list bucket: %v", bucketList)
	if !slices.Contains(bucketList, bucket1Name) || !slices.Contains(bucketList, bucket2Name) {
		t.Fatalf("got %v instead of [%s, %s]", bucketList, bucket1Name, bucket2Name)
	}
}

func TestFileOperationFromEnv(t *testing.T) {
	ctx := context.Background()
	minioClient, err := NewMinIOClientFromEnv(ctx)
	if err != nil {
		t.Fatal(err)
	}

	err = minioClient.CreateBucketIfNotExists(ctx, bucketName)
	if err != nil {
		t.Fatal(err)
	}
	defer deferRemoveBucket(ctx, t, minioClient, bucketName)

	uploadContent := "test string"
	reader := strings.NewReader(uploadContent)
	err = minioClient.UploadObject(ctx, bucketName, keyName, reader)
	if err != nil {
		t.Fatal(err)
	}

	defer func() {
		err = minioClient.RemoveObject(ctx, bucketName, keyName)
		if err != nil {
			t.Error(err)
		}
	}()

	readerCloser, err := minioClient.GetObject(ctx, bucketName, keyName)
	if err != nil {
		t.Fatal(err)
	}

	defer func() {
		err := readerCloser.Close()
		if err != nil {
			t.Error(err)
		}
	}()

	data, err := io.ReadAll(readerCloser)
	if err != nil {
		t.Fatal(err)
	}

	loadContent := string(data)
	t.Log(loadContent)

	if loadContent != uploadContent {
		t.Fatalf("wrong load data: %v instead of %v", loadContent, uploadContent)
	}

}
