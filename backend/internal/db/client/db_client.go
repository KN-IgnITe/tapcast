package client

import (
	"context"
	"fmt"
	"os"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type Query string

type DBClient struct {
	db      *gorm.DB
	queries map[string]Query
}

func (c *DBClient) GetDB() *gorm.DB {
	return c.db
}

func (client *DBClient) LoadQueryFromAbsPath(name string, queryPath string) error {
	query, err := os.ReadFile(queryPath)
	if err != nil {
		return err
	}
	client.queries[name] = Query(query)
	return nil
}

func (client *DBClient) SaveQuery(name string, querySQL string) {
	client.queries[name] = Query(querySQL)
}

func NewDBClientFromDB(db *gorm.DB) *DBClient {
	return &DBClient{
		db:      db,
		queries: make(map[string]Query),
	}
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

	return &DBClient{db: db, queries: make(map[string]Query)}, nil
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

func (client *DBClient) ExecuteQuery(ctx context.Context, queryName string, dest any, args ...any) error {
	query, ok := client.queries[queryName]
	if !ok {
		return fmt.Errorf("query %s not found", queryName)
	}
	return client.db.WithContext(ctx).Raw(string(query), args...).Scan(dest).Error
}
