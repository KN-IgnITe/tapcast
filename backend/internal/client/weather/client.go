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

// Client implementuje interfejs WeatherClient.
type Client struct {
	BaseURL    string
	HTTPClient *http.Client
}

// NewClient tworzy nową instancję klienta z domyślnym timeoutem zapobiegającym zawieszeniu.
func NewClient() *Client {
	return &Client{
		BaseURL: OpenMeteoBaseURL,
		HTTPClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// FetchForecast pobiera i deserializuje dane pogodowe.
func (c *Client) FetchForecast(ctx context.Context, lat, lon float64) (*ForecastResponse, error) {
	// Budowa zapytania
	reqURL, err := url.Parse(c.BaseURL)
	if err != nil {
		return nil, fmt.Errorf("parsing base url: %w", err)
	}

	q := reqURL.Query()
	q.Add("latitude", strconv.FormatFloat(lat, 'f', 4, 64))
	q.Add("longitude", strconv.FormatFloat(lon, 'f', 4, 64))

	// Deklaracja wymaganych zmiennych zgodnie ze strukturami Go
	q.Add("current", "temperature_2m,apparent_temperature,is_day,precipitation,weathercode,wind_speed_10m")
	q.Add("hourly", "temperature_2m,apparent_temperature,precipitation_probability,precipitation,weathercode,cloud_cover,wind_speed_10m")
	q.Add("daily", "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours")
	q.Add("timezone", "auto")

	reqURL.RawQuery = q.Encode()

	// Inicjalizacja żądania z Contextem
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, reqURL.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	// http request
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("executing request: %w", err)
	}
	defer resp.Body.Close()

	// validate status
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected http status: %d", resp.StatusCode)
	}

	// deserialize data
	var forecast ForecastResponse
	if err := json.NewDecoder(resp.Body).Decode(&forecast); err != nil {
		return nil, fmt.Errorf("decoding response: %w", err)
	}

	return &forecast, nil
}
