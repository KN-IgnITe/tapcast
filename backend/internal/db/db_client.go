package db

import (
	"fmt"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type DBClient struct {
	db *gorm.DB
}

func (c *DBClient) GetDB() *gorm.DB {
	return c.db
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

	return &DBClient{db}, nil

}
