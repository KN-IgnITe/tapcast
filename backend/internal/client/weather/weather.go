package weather

import (
	"context"
	"fmt"
	"time"
)

const (
	// Base URL for current and future forecasts
	OpenMeteoForecastURL = "https://api.open-meteo.com/v1/forecast"
	// Base URL for historical data
	OpenMeteoArchiveURL = "https://archive-api.open-meteo.com/v1/archive"
	// default localization for Wroclaw
	DefaultLat = 51.1078
	DefaultLon = 17.0385
)

type WeatherClient interface {
	FetchCurrentWeather(ctx context.Context, lat, lon float64) (*CurrentWeatherSummary, error)
	FetchFutureWeather(ctx context.Context, lat, lon float64, days int) ([]WeatherSummary, error)
	FetchHistoricalWeather(ctx context.Context, lat, lon float64, startDate, endDate time.Time) ([]WeatherSummary, error)
}

// represents the requested business output format
type WeatherSummary struct {
	Date          string  `json:"date"`
	AvgTemp       float64 `json:"avg_temp"`
	TempAmplitude float64 `json:"temp_amplitude"`
	Rain          float64 `json:"rain"`
}

// is used for the current moment
type CurrentWeatherSummary struct {
	Date        string  `json:"date"`
	Temperature float64 `json:"temperature"`
	Rain        float64 `json:"rain"`
}

// maps the raw JSON for current data
type CurrentAPIResponse struct {
	Current RawCurrentState `json:"current"`
}

// maps the raw JSON for daily data
type DailyAPIResponse struct {
	Daily RawDailyData `json:"daily"`
}

// holds raw current conditions
type RawCurrentState struct {
	Time          string  `json:"time"`
	Temperature2M float64 `json:"temperature_2m"`
	Precipitation float64 `json:"precipitation"`
	Validate      func() bool
}

// holds raw daily conditions“
type RawDailyData struct {
	Time             []string  `json:"time"` // date
	Temperature2MMax []float64 `json:"temperature_2m_max"`
	Temperature2MMin []float64 `json:"temperature_2m_min"`
	PrecipitationSum []float64 `json:"precipitation_sum"`
}

func (r RawDailyData) Validate() error {
	expectedLen := len(r.Time)

	if len(r.Temperature2MMax) != expectedLen ||
		len(r.Temperature2MMin) != expectedLen ||
		len(r.PrecipitationSum) != expectedLen {
		return fmt.Errorf("inconsistent array lengths in daily data: time=%d, max=%d, min=%d, rain=%d",
			expectedLen, len(r.Temperature2MMax), len(r.Temperature2MMin), len(r.PrecipitationSum))
	}
	return nil
}
