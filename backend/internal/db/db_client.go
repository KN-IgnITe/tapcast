package db

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type DBClient struct {
	db    *gorm.DB
	query string
}

func (c *DBClient) GetDB() *gorm.DB {
	return c.db
}

func loadQuery() (string, error) {
	_, thisFilePath, _, ok := runtime.Caller(0)
	if !ok {
		return "", errors.New("cannot get caller")
	}
	dir := filepath.Dir(thisFilePath)

	queryPath := filepath.Join(dir, "..", "..", "..", "infrastructure", "postgres", "query.sql")

	query, err := os.ReadFile(queryPath)
	if err != nil {
		return "", err
	}

	return string(query), nil
}

func NewDBClient(config *DBConfig) (*DBClient, error) {
	dsn := fmt.Sprintf(
		"host=%s user=%s password=%s dbname=%s port=%s sslmode=disable",
		config.Host, config.User, config.Password, config.DBName, config.Port,
	)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})

	if err != nil {
		return nil, err
	}

	data, err := loadQuery()
	if err != nil {
		return nil, err
	}

	return &DBClient{db: db, query: data}, nil
}

func (client *DBClient) Create(ctx context.Context, value any) error {
	return client.db.WithContext(ctx).Create(value).Error
}

func (client *DBClient) FindAll(ctx context.Context, destination any) error {
	return client.db.WithContext(ctx).Find(destination).Error
}

func (client *DBClient) Save(ctx context.Context, value any) error {
	return client.db.WithContext(ctx).Save(value).Error
}

func (client *DBClient) DeleteWhere(ctx context.Context, model any, query string, args ...any) error {
	return client.db.WithContext(ctx).Where(query, args...).Delete(model).Error
}

func (client *DBClient) GetQuery(ctx context.Context, bar_id int) ([]models.Query1Row, error) {
	var result []models.Query1Row

	err := client.db.WithContext(ctx).Raw(client.query, bar_id).Scan(&result).Error
	if err != nil {
		return nil, err
	}

	return result, nil
}
