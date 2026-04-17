package models

import (
	"os"
	"testing"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func TestDatabaseConnection(t *testing.T) {
	dsn := os.Getenv("DATABASE_URL")

	if dsn == "" {
		t.Fatal("DATABASE_URL is not set")
	}

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
