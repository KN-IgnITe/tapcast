//go:build integration

package tests

import (
	"fmt"
	"os"
	"testing"

	"github.com/m1kus3q/pubpredictor/backend/internal/db"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func TestDatabaseConnection(t *testing.T) {
	requiredEnvVars := []string{"DB_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD", "DB_NAME", "DB_PORT"}
	for _, envVar := range requiredEnvVars {
		if os.Getenv(envVar) == "" {
			t.Fatalf("required environment variable %s is not set", envVar)
		}
	}

	dsn := fmt.Sprintf(
		"host=%s user=%s password=%s dbname=%s port=%s sslmode=disable",
		os.Getenv("DB_HOST"), os.Getenv("POSTGRES_USER"), os.Getenv("POSTGRES_PASSWORD"), os.Getenv("DB_NAME"), os.Getenv("DB_PORT"),
	)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})

	if err != nil {
		t.Fatalf("failed to connect to database: %v", err)
	}

	sqlDb, err := db.DB()
	if err != nil {
		t.Fatalf("failed to get sql.DB, %v", err)
	}

	err = sqlDb.Ping()
	if err != nil {
		t.Fatalf("database ping failed: %v", err)
	}

}

func TestConnectFunction(t *testing.T) {

	host := os.Getenv("DB_HOST")
	user := os.Getenv("POSTGRES_USER")
	pass := os.Getenv("POSTGRES_PASSWORD")
	name := os.Getenv("DB_NAME")
	port := os.Getenv("DB_PORT")

	if host == "" || user == "" || name == "" || pass == "" || port == "" {
		t.Fatal("Required environment variables are not set for integration test")
	}

	database, err := db.Connect(host, user, pass, name, port)

	if err != nil {
		t.Fatalf("db.Connect() failed: %v", err)
	}

	if database == nil {
		t.Fatal("db.Connect() returned nil database object")
	}
}
