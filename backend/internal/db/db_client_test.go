//go:build integration

package db

import (
	"context"
	"errors"
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

	testClient := &DBClient{
		db:    tx,
		query: client.query,
	}

	return fn(ctx, testClient)
}

func createExampleDates(ctx context.Context, dbClient *DBClient) error {

	days := []models.Day{
		{DayDate: time.Date(2026, 4, 1, 0, 0, 0, 0, time.UTC), IsWorking: true},
		{DayDate: time.Date(2026, 4, 2, 0, 0, 0, 0, time.UTC), IsWorking: true},
		{DayDate: time.Date(2026, 4, 3, 0, 0, 0, 0, time.UTC), IsWorking: true},
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
		{BarID: 1, Plu: 101, Category: 5},
		{BarID: 1, Plu: 102, Category: 6},
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

		err := createExampleDates(ctx, testClient)
		if err != nil {
			return err
		}
		queryData, err := testClient.GetQuery(ctx, 1)
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
