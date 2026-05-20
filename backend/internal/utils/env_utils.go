package utils

import (
	"fmt"
	"os"
)

// newNotFoundError creates an error for missing environment variable.
func EnvNotFoundError(envName string) error {
	return fmt.Errorf("missing env variable %s", envName)
}

// GetEnvOrValue returns custom value or tries to return environment variable.
func GetEnvOrValue(envName string, val string) (string, error) {
	if val == "" {
		if val = os.Getenv(envName); val == "" {
			return "", EnvNotFoundError(envName)
		}
	}
	return val, nil
}

// RequireEnv returns environment variable or error  if it is not set.
func RequireEnv(envName string) (string, error) {
	if val := os.Getenv(envName); val != "" {
		return val, nil
	}
	return "", EnvNotFoundError(envName)
}
