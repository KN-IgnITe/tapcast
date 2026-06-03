package client

import (
	"github.com/m1kus3q/pubpredictor/backend/internal/utils"
)

const (
	EnvDBHost     = "DB_HOST"
	EnvDBUser     = "POSTGRES_USER"
	EnvDBPassword = "POSTGRES_PASSWORD"
	EnvDBName     = "DB_NAME"
	EnvDBPort     = "DB_PORT"
)

type DBConfig struct {
	DBName   string
	Host     string
	User     string
	Password string
	Port     string
}

// NewDBConfig creates config using only environment variables.
func NewDBConfig() (*DBConfig, error) {
	return NewCustomDBConfig("", "", "", "", "")
}

// NewCustomDBConfig creates new DB config with custom parameters, empty string means value from env.
func NewCustomDBConfig(host string, user string, password string,
	name string, port string) (*DBConfig, error) {

	host, err := utils.GetEnvOrValue(EnvDBHost, host)
	if err != nil {
		return nil, err
	}

	user, err = utils.GetEnvOrValue(EnvDBUser, user)
	if err != nil {
		return nil, err
	}

	password, err = utils.GetEnvOrValue(EnvDBPassword, password)
	if err != nil {
		return nil, err
	}

	name, err = utils.GetEnvOrValue(EnvDBName, name)
	if err != nil {
		return nil, err
	}

	port, err = utils.GetEnvOrValue(EnvDBPort, port)
	if err != nil {
		return nil, err
	}

	return &DBConfig{
		Host:     host,
		User:     user,
		Password: password,
		DBName:   name,
		Port:     port,
	}, nil
}
