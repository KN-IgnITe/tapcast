package minio

import (
	"context"
	"errors"
	"io"
	"slices"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/smithy-go/ptr"

	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type MinIOClient struct {
	client *s3.Client
}

func NewMinIOClientFromEnv(ctx context.Context) (*MinIOClient, error) {
	minIOConfig, err := NewMinIOConfig()
	if err != nil {
		return nil, err
	}
	return NewMinIOClientFromConfig(minIOConfig, ctx)
}

func NewMinIOClientFromConfig(minIOConfig *MinIOConfig, ctx context.Context) (*MinIOClient, error) {
	s3Config, err := config.LoadDefaultConfig(ctx,
		config.WithRegion(minIOConfig.Region),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(
			minIOConfig.User, minIOConfig.Password, "",
		),
		),
	)
	if err != nil {
		return nil, err
	}

	client := s3.NewFromConfig(
		s3Config,
		func(o *s3.Options) {
			o.BaseEndpoint = &minIOConfig.Endpoint
			o.UsePathStyle = true
		},
	)

	return &MinIOClient{
		client: client,
	}, nil
}

func (minIOClient *MinIOClient) CreateBucket(ctx context.Context, bucketName string) error {
	_, err := minIOClient.client.CreateBucket(
		ctx,
		&s3.CreateBucketInput{
			Bucket: ptr.String(bucketName),
		},
	)

	return err
}

func (minIOClient *MinIOClient) CreateBucketIfNotExists(ctx context.Context, bucketName string) error {
	bucketList, err := minIOClient.ListBuckets(ctx)
	if err != nil {
		return err
	}
	if slices.Contains(bucketList, bucketName) {
		return nil
	}

	return minIOClient.CreateBucket(ctx, bucketName)
}

func (minIOClient *MinIOClient) RemoveBucket(ctx context.Context, bucketName string) error {
	_, err := minIOClient.client.DeleteBucket(
		ctx,
		&s3.DeleteBucketInput{
			Bucket: ptr.String(bucketName),
		},
	)
	return err
}

func (minIOClient *MinIOClient) ListBuckets(ctx context.Context) ([]string, error) {
	output, err := minIOClient.client.ListBuckets(ctx, &s3.ListBucketsInput{})
	if err != nil {
		return nil, err
	}

	var bucketNames []string
	for _, bucket := range output.Buckets {
		if bucket.Name == nil {
			return nil, errors.New("found bucket without name")

		}
		bucketNames = append(bucketNames, *bucket.Name)
	}
	return bucketNames, nil
}

func (minIOClient *MinIOClient) UploadObject(ctx context.Context, bucketName string, key string, body io.Reader) error {
	_, err := minIOClient.client.PutObject(
		ctx,
		&s3.PutObjectInput{
			Bucket: ptr.String(bucketName),
			Key:    ptr.String(key),
			Body:   body,
		},
	)
	return err
}

func (minIOClient *MinIOClient) RemoveObject(ctx context.Context, bucketName string, key string) error {
	_, err := minIOClient.client.DeleteObject(
		ctx,
		&s3.DeleteObjectInput{
			Bucket: ptr.String(bucketName),
			Key:    ptr.String(key),
		},
	)

	return err
}

func (minIOClient *MinIOClient) GetObject(ctx context.Context, bucketName string, key string) (io.ReadCloser, error) {
	object, err := minIOClient.client.GetObject(
		ctx,
		&s3.GetObjectInput{
			Bucket: ptr.String(bucketName),
			Key:    ptr.String(key),
		},
	)
	if err != nil {
		return nil, err
	}
	return object.Body, nil
}
