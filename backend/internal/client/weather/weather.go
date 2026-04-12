package weather

import (
	"context"
	"time"
)

const (
	OpenMeteoBaseURL = "https://api.open-meteo.com/v1/forecast"
	DefaultLat       = 51.1078
	DefaultLon       = 17.0385
)

type WeatherClient interface {
	FetchForecast(ctx context.Context, lat, lon float64) (*ForecastResponse, error)
}

type ForecastResponse struct {
	Latitude         float64      `json:"latitude"`
	Longitude        float64      `json:"longitude"`
	UtcOffsetSeconds int          `json:"utc_offset_seconds"`
	Timezone         string       `json:"timezone"`
	Current          CurrentState `json:"current"`
	Hourly           HourlyData   `json:"hourly"`
	Daily            DailyData    `json:"daily"`
}

type CurrentState struct {
	Time                string  `json:"time"`
	Temperature2M       float64 `json:"temperature_2m"`
	ApparentTemperature float64 `json:"apparent_temperature"`
	IsDay               int     `json:"is_day"`
	Precipitation       float64 `json:"precipitation"`
	WeatherCode         int     `json:"weathercode"`
	WindSpeed10M        float64 `json:"wind_speed_10m"`
}

type HourlyData struct {
	Time                     []string  `json:"time"`
	Temperature2M            []float64 `json:"temperature_2m"`
	ApparentTemperature      []float64 `json:"apparent_temperature"`
	PrecipitationProbability []int     `json:"precipitation_probability"`
	Precipitation            []float64 `json:"precipitation"`
	WeatherCode              []int     `json:"weathercode"`
	CloudCover               []int     `json:"cloud_cover"`
	WindSpeed10M             []float64 `json:"wind_speed_10m"`
}

type DailyData struct {
	Time               []string  `json:"time"`
	WeatherCode        []int     `json:"weathercode"`
	Temperature2MMax   []float64 `json:"temperature_2m_max"`
	Temperature2MMin   []float64 `json:"temperature_2m_min"`
	PrecipitationSum   []float64 `json:"precipitation_sum"`
	PrecipitationHours []float64 `json:"precipitation_hours"`
}

type HourlyMetrics struct {
	Timestamp                time.Time
	ApparentTemperature      float64
	PrecipitationProbability int
	PrecipitationVolume      float64
	WeatherCode              int
	WindSpeed                float64
}
