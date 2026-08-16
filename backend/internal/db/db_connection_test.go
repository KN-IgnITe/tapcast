//go:build integration

package db

import (
	"os"
	"testing"

	"github.com/m1kus3q/pubpredictor/backend/internal/db/client"
)

func TestDatabaseConnectionWithClient(t *testing.T) {
	config, err := client.NewDBConfig()

	if err != nil {
		t.Fatal(err)
	}

	db_client, err := client.NewDBClient(config)
	if err != nil {
		t.Fatal(err)
	}
	myDB := db_client.GetDB()

	sqlDb, err := myDB.DB()
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

	database, err := Connect(host, user, pass, name, port)

	if err != nil {
		t.Fatalf("db.Connect() failed: %v", err)
	}

	if database == nil {
		t.Fatal("db.Connect() returned nil database object")
	}
}
