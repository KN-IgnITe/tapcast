package tests

import (
	"fmt"
	"os"
	"testing"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func TestDatabaseConnection(t *testing.T) {

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
