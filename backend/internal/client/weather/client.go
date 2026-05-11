package weather

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// implements WeatherClient interface
type OpenMeteoWeatherClient struct {
	ForecastURL string
	ArchiveURL  string
	HTTPClient  *http.Client
}

// creates a new instance of Client
func NewClient() *OpenMeteoWeatherClient {
	return &OpenMeteoWeatherClient{
		ForecastURL: OpenMeteoForecastURL,
		ArchiveURL:  OpenMeteoArchiveURL,
		HTTPClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// retrieves current weather conditions
func (c *OpenMeteoWeatherClient) FetchCurrentWeather(ctx context.Context, lat, lon float64) (*CurrentWeatherSummary, error) {
	reqURL, err := url.Parse(c.ForecastURL)
	if err != nil {
		return nil, fmt.Errorf("parsing forecast url: %w", err)
	}

	q := reqURL.Query()
	q.Add("latitude", strconv.FormatFloat(lat, 'f', 4, 64))
	q.Add("longitude", strconv.FormatFloat(lon, 'f', 4, 64))
	q.Add("current", "temperature_2m,precipitation")
	reqURL.RawQuery = q.Encode()

	var resp CurrentAPIResponse
	if err := c.doRequest(ctx, reqURL.String(), &resp); err != nil {
		return nil, err
	}

	return &CurrentWeatherSummary{
		Date:        resp.Current.Time,
		Temperature: resp.Current.Temperature2M,
		Rain:        resp.Current.Precipitation,
	}, nil
}

// retrieves weather forecast for a given number of days
func (c *OpenMeteoWeatherClient) FetchFutureWeather(ctx context.Context, lat, lon float64, days int) ([]WeatherSummary, error) {
	reqURL, err := url.Parse(c.ForecastURL)
	if err != nil {
		return nil, fmt.Errorf("parsing forecast url: %w", err)
	}

	q := reqURL.Query()
	q.Add("latitude", strconv.FormatFloat(lat, 'f', 4, 64))
	q.Add("longitude", strconv.FormatFloat(lon, 'f', 4, 64))
	q.Add("daily", "temperature_2m_max,temperature_2m_min,precipitation_sum")
	q.Add("forecast_days", strconv.Itoa(days))
	q.Add("timezone", "auto")
	reqURL.RawQuery = q.Encode()

	var resp DailyAPIResponse
	if err := c.doRequest(ctx, reqURL.String(), &resp); err != nil {
		return nil, err
	}

	summaries, err := summarizeWeather(resp.Daily)
	if err != nil {
		return nil, fmt.Errorf("processing future weather data: %w", err)
	}

	return summaries, nil
}

// retrieves past weather data within a specific date range
func (c *OpenMeteoWeatherClient) FetchHistoricalWeather(ctx context.Context, lat, lon float64, startDate, endDate time.Time) ([]WeatherSummary, error) {
	reqURL, err := url.Parse(c.ArchiveURL)
	if err != nil {
		return nil, fmt.Errorf("parsing archive url: %w", err)
	}

	q := reqURL.Query()
	q.Add("latitude", strconv.FormatFloat(lat, 'f', 4, 64))
	q.Add("longitude", strconv.FormatFloat(lon, 'f', 4, 64))
	// Open-Meteo requires YYYY-MM-DD format
	q.Add("start_date", startDate.Format(time.DateOnly))
	q.Add("end_date", endDate.Format(time.DateOnly))
	q.Add("daily", "temperature_2m_max,temperature_2m_min,precipitation_sum")
	q.Add("timezone", "auto")
	reqURL.RawQuery = q.Encode()

	var resp DailyAPIResponse
	if err := c.doRequest(ctx, reqURL.String(), &resp); err != nil {
		return nil, err
	}

	summaries, err := summarizeWeather(resp.Daily)
	if err != nil {
		return nil, fmt.Errorf("processing historical weather data: %w", err)
	}

	return summaries, nil
}

// helper method to handle HTTP execution and JSON decoding
func (c *OpenMeteoWeatherClient) doRequest(ctx context.Context, targetURL string, target interface{}) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, targetURL, nil)
	if err != nil {
		return fmt.Errorf("creating request: %w", err)
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return fmt.Errorf("executing request: %w", err)
	}
	defer func() { _ = resp.Body.Close() }()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected http status: %d", resp.StatusCode)
	}

	if err := json.NewDecoder(resp.Body).Decode(target); err != nil {
		return fmt.Errorf("decoding response: %w", err)
	}

	return nil
}

// transforms raw Open-Meteo daily arrays into business logic slice
func summarizeWeather(daily RawDailyData) ([]WeatherSummary, error) {
	if err := daily.Validate(); err != nil {
		return nil, fmt.Errorf("invalid daily data: %w", err)
	}

	var summaries []WeatherSummary
	for i := range daily.Time {
		max := daily.Temperature2MMax[i]
		min := daily.Temperature2MMin[i]

		summaries = append(summaries, WeatherSummary{
			Date:          daily.Time[i],
			AvgTemp:       (max + min) / 2.0, // Calculate average
			TempAmplitude: max - min,         // Calculate amplitude
			Rain:          daily.PrecipitationSum[i],
		})
	}
	return summaries, nil
}
