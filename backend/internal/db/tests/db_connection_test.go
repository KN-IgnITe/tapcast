//go:build integration

package test

import (
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
