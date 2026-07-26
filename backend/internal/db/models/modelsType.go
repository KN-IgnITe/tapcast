package models

import (
	"time"
)

type Day struct {
	DayDate   time.Time `gorm:"primaryKey;type:date"`
	IsWorking bool      `gorm:"not null"`

	Weather         []Weather         `gorm:"foreignKey:WeatherDate;references:DayDate"`
	WeatherForecast []WeatherForecast `gorm:"foreignKey:WeatherDate;references:DayDate"`

	Sales []Sale `gorm:"foreignKey:SaleDate;references:DayDate"`
}

func (Day) TableName() string { return "day" }

type Location struct {
	LocationID int    `gorm:"primaryKey"`
	Name       string `gorm:"type:text;not null"`

	Weather         []Weather         `gorm:"foreignKey:LocationID;references:LocationID"`
	WeatherForecast []WeatherForecast `gorm:"foreignKey:LocationID;references:LocationID"`
	Bar             []Bar             `gorm:"foreignKey:LocationID;references:LocationID"`
}

func (Location) TableName() string { return "location" }

type Bar struct {
	BarID      int    `gorm:"primaryKey"`
	LocationID int    `gorm:"not null"`
	Name       string `gorm:"type:text"`

	Article []Article `gorm:"foreignKey:BarID;references:BarID"`
}

func (Bar) TableName() string { return "bar" }

type Weather struct {
	WeatherDate   time.Time `gorm:"primaryKey;type:date"`
	LocationID    int       `gorm:"primaryKey"`
	AvgTemp       float64   `gorm:"not null"`
	TempAmplitude float64   `gorm:"not null"`
	Rain          float64   `gorm:"not null;default:0;check:rain>=0"`
}

func (Weather) TableName() string { return "weather" }

type WeatherForecast struct {
	WeatherDate   time.Time `gorm:"primaryKey;type:date"`
	LocationID    int       `gorm:"primaryKey"`
	AvgTemp       float64   `gorm:"not null"`
	TempAmplitude float64   `gorm:"not null"`
	Rain          float64   `gorm:"not null;default:0;check:rain>=0"`
	ForecastDate  time.Time `gorm:"not null;type:date"`
}

func (WeatherForecast) TableName() string { return "weather_forecast" }

type Article struct {
	BarID    int    `gorm:"primaryKey"`
	Plu      int    `gorm:"primaryKey"`
	Category string `gorm:"type:text;not null"`

	Sales []Sale `gorm:"foreignKey:BarID,Plu;references:BarID,Plu"`
}

func (Article) TableName() string { return "article" }

type Sale struct {
	SaleDate time.Time `gorm:"primaryKey;type:date"`
	BarID    int       `gorm:"primaryKey"`
	Plu      int       `gorm:"primaryKey"`
	Amount   int       `gorm:"not null;check:amount>=0"`
	Day      Day       `gorm:"foreignKey:SaleDate;references:DayDate"`
}

func (Sale) TableName() string { return "sale" }

type Query1Row struct {
	Date             time.Time `json:"date"`
	DayOfWeek        int       `json:"day_of_week"`
	IsWorking        bool      `json:"is_working"`
	IsNextDayWorking *bool     `json:"is_next_day_working"`

	AvgTemp       *float64 `json:"avg_temp"`
	TempAmplitude *float64 `json:"temp_amplitude"`
	Rain          *float64 `json:"rain"`

	PLU             int    `json:"PLU"`
	Category        string `json:"category"`
	Amount          int    `json:"amount" db:"PLU"`
	YesterdayDemand *int   `json:"yesterday_demand"`
	WeekAgoDemand   *int   `json:"week_ago_demand"`
}
