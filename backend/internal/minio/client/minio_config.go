package minio

import (
	"github.com/m1kus3q/pubpredictor/backend/internal/utils"
)

const (
	EnvS3Host = "S3_HOST"
	EnvS3Port = "S3_PORT"

	EnvMinIORootUser     = "MINIO_ROOT_USER"
	EnvMinIORootPassword = "MINIO_ROOT_PASSWORD"
	EnvS3Region          = "S3_REGION"
	protocol             = "http://"
)

type MinIOConfig struct {
	Endpoint string
	User     string
	Password string
	Region   string
}

// NewMinIOConfig creates config using only environment variables.
func NewMinIOConfig() (*MinIOConfig, error) {
	return NewCustomMinIOConfig("", "", "", "")
}

// NewCustomMinIOConfig creates new MinIO config with custom parameters, empty string
// means value from env.
func NewCustomMinIOConfig(endpoint string, user string, password string,
	region string) (*MinIOConfig, error) {

	if endpoint == "" {

		host, err := utils.RequireEnv(EnvS3Host)
		if err != nil {
			return nil, err
		}

		port, err := utils.RequireEnv(EnvS3Port)
		if err != nil {
			return nil, err
		}

		endpoint = protocol + host + ":" + port
	}

	user, err := utils.GetEnvOrValue(EnvMinIORootUser, user)
	if err != nil {
		return nil, err
	}

	password, err = utils.GetEnvOrValue(EnvMinIORootPassword, password)
	if err != nil {
		return nil, err
	}

	region, err = utils.GetEnvOrValue(EnvS3Region, region)
	if err != nil {
		return nil, err
	}

	return &MinIOConfig{
		Endpoint: endpoint,
		User:     user,
		Password: password,
		Region:   region,
	}, nil
}
