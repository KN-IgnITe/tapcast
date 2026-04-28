package class

import (
	"fmt"
	"os"
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

// newNotFoundError creates an error for missing environment variable.
func newNotFoundError(envName string) error {
	return fmt.Errorf("missing env variable %s", envName)
}

// NewDBConfig creates config using only environment variables.
func NewDBConfig() (*DBConfig, error) {
	return NewCustomDBConfig("", "", "", "", "")
}

// getEnv returns custom value or tries to return environment variable.
func getEnv(envName string, val string) (string, error) {
	if val == "" {
		if val = os.Getenv(envName); val == "" {
			return "", newNotFoundError(envName)
		}
	}
	return val, nil
}

// NewCustomDBConfig creates new DB config with custom parameters, empty string means value from env.
func NewCustomDBConfig(host string, user string, password string,
	name string, port string) (*DBConfig, error) {

	host, err := getEnv(EnvDBHost, host)
	if err != nil {
		return nil, err
	}

	user, err = getEnv(EnvDBUser, user)
	if err != nil {
		return nil, err
	}

	password, err = getEnv(EnvDBPassword, password)
	if err != nil {
		return nil, err
	}

	name, err = getEnv(EnvDBName, name)
	if err != nil {
		return nil, err
	}

	port, err = getEnv(EnvDBPort, port)
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
