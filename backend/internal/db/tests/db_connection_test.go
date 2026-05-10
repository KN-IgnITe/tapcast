//go:build integration

package test

import (
	"testing"

	"github.com/m1kus3q/pubpredictor/backend/internal/db"
)

func TestDatabaseConnection(t *testing.T) {
	config, err := db.NewDBConfig()

	if err != nil {
		t.Fatal(err)
	}

	db_client, err := db.NewDBClient(config)
	if err != nil {
		t.Fatal(err)
	}
	myDB := db_client.GetDB()
	/*
		dsn := fmt.Sprintf(
			"host=%s user=%s password=%s dbname=%s port=%s sslmode=disable",
			config.Host, config.User, config.Password, config.DBName, config.Port,
		)
		db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	*/
	if err != nil {
		t.Fatalf("failed to connect to database: %v", err)
	}

	sqlDb, err := myDB.DB()
	if err != nil {
		t.Fatalf("failed to get sql.DB, %v", err)
	}
	err = sqlDb.Ping()
	if err != nil {
		t.Fatalf("database ping failed: %v", err)
	}
}
