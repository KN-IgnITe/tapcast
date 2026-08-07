package scheduler

import (
	"context"
	"log"
	"time"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"
)

//go:generate mockgen -source=weather_job.go -destination=./mocks/db_mock.go -package=mocks
type DB interface {
	Upsert(ctx context.Context, value any) error
}

type WeatherJob struct {
	weatherConfig
	weather weather.WeatherClient
	db      DB
}

func NewWeatherJob(weatherClient weather.WeatherClient, db DB, opts ...WeatherOption) *WeatherJob {
	config := weatherConfig{
		forecastDays: defaultForecastDays,
		lat:          weather.DefaultLat,
		lon:          weather.DefaultLon,
		locationID:   1,
	}

	for _, opt := range opts {
		opt(&config)
	}

	return &WeatherJob{
		weatherConfig: config,
		weather:       weatherClient,
		db:            db,
	}

}

func (w *WeatherJob) Run(ctx context.Context) {
	forecastDate := time.Now()

	weatherSummaries, err := w.weather.FetchFutureWeather(ctx, w.lat, w.lon, w.forecastDays)
	if err != nil {
		log.Printf("failed to fetch weather forecast: %v", err)
		return
	}

	for _, weatherDay := range weatherSummaries {
		if err := w.saveForecast(ctx, weatherDay, forecastDate); err != nil {
			log.Printf("failed to save weather forecast: %v", err)
		}
	}
}

func (w *WeatherJob) saveForecast(ctx context.Context, weatherDay weather.WeatherSummary, forecastDate time.Time) error {
	weatherDate, err := time.Parse("2006-01-02", weatherDay.Date)
	if err != nil {
		return err
	}
	forecast := models.WeatherForecast{
		WeatherDate:   weatherDate,
		LocationID:    w.locationID,
		AvgTemp:       weatherDay.AvgTemp,
		TempAmplitude: weatherDay.TempAmplitude,
		Rain:          weatherDay.Rain,
		ForecastDate:  forecastDate,
	}

	return w.db.Upsert(ctx, &forecast)
}
