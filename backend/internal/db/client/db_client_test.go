//go:build integration

package client

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"testing"

	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"

	"time"
)

func RunTestOperation(ctx context.Context, client *DBClient, fn func(context.Context, *DBClient) error) error {
	tx := client.GetDB().Begin()
	if tx.Error != nil {
		return tx.Error
	}
	defer tx.Rollback()

	testClient := NewDBClientFromDB(tx)

	return fn(ctx, testClient)
}

func createExampleData(ctx context.Context, dbClient *DBClient) error {

	days := []models.Day{
		{DayDate: time.Date(2026, 4, 1, 0, 0, 0, 0, time.UTC), IsWorking: false},
		{DayDate: time.Date(2026, 4, 2, 0, 0, 0, 0, time.UTC), IsWorking: true},
		{DayDate: time.Date(2026, 4, 3, 0, 0, 0, 0, time.UTC), IsWorking: false},
		{DayDate: time.Date(2026, 4, 8, 0, 0, 0, 0, time.UTC), IsWorking: true},
		{DayDate: time.Date(2026, 4, 9, 0, 0, 0, 0, time.UTC), IsWorking: true},
		{DayDate: time.Date(2026, 4, 10, 0, 0, 0, 0, time.UTC), IsWorking: true},
	}
	if err := dbClient.Create(ctx, days); err != nil {
		return err
	}

	location := models.Location{
		LocationID: 1,
		Name:       "Warszawa Centralna",
	}
	if err := dbClient.Create(ctx, &location); err != nil {
		return err
	}

	bar := models.Bar{
		BarID:      1,
		LocationID: 1,
		Name:       "Bar pod Złotym Łukiem",
	}
	if err := dbClient.Create(ctx, &bar); err != nil {
		return err
	}

	weather := models.Weather{
		WeatherDate:   time.Date(2026, 4, 10, 0, 0, 0, 0, time.UTC),
		LocationID:    1,
		AvgTemp:       15.5,
		TempAmplitude: 5.0,
		Rain:          0.2,
	}

	if err := dbClient.Create(ctx, &weather); err != nil {
		return err
	}

	articles := []models.Article{
		{BarID: 1, Plu: 101, Category: "5"},
		{BarID: 1, Plu: 102, Category: "6"},
	}

	if err := dbClient.Create(ctx, articles); err != nil {
		return err
	}

	sales := []models.Sale{

		{SaleDate: time.Date(2026, 4, 3, 0, 0, 0, 0, time.UTC), BarID: 1, Plu: 101, Amount: 50},
		{SaleDate: time.Date(2026, 4, 9, 0, 0, 0, 0, time.UTC), BarID: 1, Plu: 101, Amount: 60},
		{SaleDate: time.Date(2026, 4, 10, 0, 0, 0, 0, time.UTC), BarID: 1, Plu: 101, Amount: 100},

		{SaleDate: time.Date(2026, 4, 3, 0, 0, 0, 0, time.UTC), BarID: 1, Plu: 102, Amount: 60},
		{SaleDate: time.Date(2026, 4, 9, 0, 0, 0, 0, time.UTC), BarID: 1, Plu: 102, Amount: 70},
		{SaleDate: time.Date(2026, 4, 10, 0, 0, 0, 0, time.UTC), BarID: 1, Plu: 102, Amount: 110},
	}

	if err := dbClient.Create(ctx, sales); err != nil {
		return err
	}

	return nil
}

func TestLoadQueryFromInvalidPath(t *testing.T) {
	client := NewDBClientFromDB(nil)

	err := client.LoadQueryFromAbsPath("test", "non_existing_file.sql")

	if err == nil {
		t.Fatal("expected error")
	}
}

func TestSaveQuery(t *testing.T) {
	client := NewDBClientFromDB(nil)

	client.SaveQuery("test", "SELECT 1")

	query, ok := client.queries["test"]

	if !ok {
		t.Fatal("query not saved")
	}

	if string(query) != "SELECT 1" {
		t.Fatalf("expected SELECT 1, got %s", string(query))
	}
}

func TestLoadQueryFromAbsPath(t *testing.T) {
	//create temporary file
	dir := t.TempDir()
	path := filepath.Join(dir, "test_query.sql")
	err := os.WriteFile(path, []byte("SELECT 2"), 0644)
	if err != nil {
		t.Fatal(err)
	}
	client := NewDBClientFromDB(nil)

	err = client.LoadQueryFromAbsPath("test", path)
	if err != nil {
		t.Fatal("query not saved")
	}
	query, ok := client.queries["test"]

	if !ok {
		t.Fatal("query not saved")
	}
	if string(query) != "SELECT 2" {
		t.Fatalf("expected SELECT 2, got %s", string(query))
	}
}
func TestDBClient(t *testing.T) {
	config, err := NewDBConfig()
	if err != nil {
		t.Fatal(err)
	}

	dbClient, err := NewDBClient(config)
	if err != nil {
		t.Fatal(err)
	}

	err = dbClient.GetDB().AutoMigrate(
		&models.Day{},
		&models.Location{},
		&models.Bar{},
		&models.Weather{},
		&models.Article{},
		&models.Sale{},
	)
	if err != nil {
		t.Fatal(err)
	}

	tables, err := dbClient.GetDB().Migrator().GetTables()
	if err != nil {
		t.Fatal(err)
	}

	t.Log(tables)

	ctx := context.Background()
	err = RunTestOperation(ctx, dbClient, func(ctx context.Context, testClient *DBClient) error {

		err := createExampleData(ctx, testClient)
		if err != nil {
			return err
		}

		err = testClient.LoadQueryFromAbsPath("main", "../../../../infrastructure/postgres/query.sql")
		if err != nil {
			return err
		}

		var queryData []models.Query1Row
		err = testClient.ExecuteQuery(ctx, "main", &queryData, 1)
		if err != nil {
			return err
		}
		if len(queryData) == 0 {
			return errors.New("expected non-empty query result")
		}
		for _, row := range queryData {
			t.Logf("%+v", row)
		}
		return nil
	})

	if err != nil {
		t.Fatal(err)
	}
}
