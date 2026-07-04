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
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
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

func (c *MinIOClient) CreateBucket(ctx context.Context, bucketName string) error {
	_, err := c.client.CreateBucket(
		ctx,
		&s3.CreateBucketInput{
			Bucket: ptr.String(bucketName),
		},
	)

	return err
}

func (c *MinIOClient) CreateBucketIfNotExists(ctx context.Context, bucketName string) error {
	bucketList, err := c.ListBuckets(ctx)
	if err != nil {
		return err
	}
	if slices.Contains(bucketList, bucketName) {
		return nil
	}

	return c.CreateBucket(ctx, bucketName)
}

func (c *MinIOClient) RemoveBucket(ctx context.Context, bucketName string) error {
	_, err := c.client.DeleteBucket(
		ctx,
		&s3.DeleteBucketInput{
			Bucket: ptr.String(bucketName),
		},
	)
	return err
}

func (c *MinIOClient) ListBuckets(ctx context.Context) ([]string, error) {
	output, err := c.client.ListBuckets(ctx, &s3.ListBucketsInput{})
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

func (c *MinIOClient) UploadObject(ctx context.Context, bucketName string, key string, body io.Reader) error {
	_, err := c.client.PutObject(
		ctx,
		&s3.PutObjectInput{
			Bucket: ptr.String(bucketName),
			Key:    ptr.String(key),
			Body:   body,
		},
	)
	return err
}

func (c *MinIOClient) RemoveObject(ctx context.Context, bucketName string, key string) error {
	_, err := c.client.DeleteObject(
		ctx,
		&s3.DeleteObjectInput{
			Bucket: ptr.String(bucketName),
			Key:    ptr.String(key),
		},
	)

	return err
}
func (c *MinIOClient) ListObjectsKeys(ctx context.Context, bucketName string) ([]string, error) {
	output, err := c.client.ListObjectsV2(
		ctx,
		&s3.ListObjectsV2Input{
			Bucket: ptr.String(bucketName),
		},
	)
	if err != nil {
		return nil, err
	}

	keys := make([]string, 0, len(output.Contents))

	for _, obj := range output.Contents {
		keys = append(keys, *obj.Key)
	}

	return keys, nil
}

func (c *MinIOClient) GetObject(ctx context.Context, bucketName string, key string) (io.ReadCloser, error) {
	object, err := c.client.GetObject(
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

func (c *MinIOClient) SetTags(ctx context.Context, bucketName string, key string, tags []types.Tag) error {
	tagging := &types.Tagging{
		TagSet: tags,
	}
	_, err := c.client.PutObjectTagging(
		ctx,
		&s3.PutObjectTaggingInput{
			Bucket:  ptr.String(bucketName),
			Key:     ptr.String(key),
			Tagging: tagging,
		},
	)
	return err
}

func (c *MinIOClient) GetTags(ctx context.Context, bucketName string, key string) ([]types.Tag, error) {
	object, err := c.client.GetObjectTagging(
		ctx,
		&s3.GetObjectTaggingInput{
			Bucket: ptr.String(bucketName),
			Key:    ptr.String(key),
		},
	)

	if err != nil {
		return nil, err
	}
	return object.TagSet, nil
}

func (c *MinIOClient) SetTag(ctx context.Context, bucketName string, key string,
	newTagKey string, newTagValue string) error {
	tags, err := c.GetTags(ctx, bucketName, key)
	if err != nil {
		return err
	}
	found := false
	for i := range tags {
		if newTagKey == *tags[i].Key {
			tags[i].Value = &newTagValue
			found = true
			break
		}
	}
	if !found {
		tags = append(tags, types.Tag{
			Key:   &newTagKey,
			Value: &newTagValue,
		})
	}

	err = c.SetTags(ctx, bucketName, key, tags)
	return err
}

func (c *MinIOClient) GetTag(ctx context.Context, bucketName string,
	objectKey string, tagKey string) (*string, error) {
	tags, err := c.GetTags(ctx, bucketName, objectKey)
	if err != nil {
		return nil, err
	}

	for _, tag := range tags {
		if tagKey == *tag.Key {
			return tag.Value, nil
		}
	}
	return nil, nil
}

func (c *MinIOClient) ClearBucket(ctx context.Context, bucketName string) error {
	keys, err := c.ListObjectsKeys(ctx, bucketName)
	if err != nil {
		return err
	}

	for _, key := range keys {
		if err == nil {
			err = c.RemoveObject(ctx, bucketName, key)
		} else {
			_ = c.RemoveObject(ctx, bucketName, key)
		}
	}
	return err
}
