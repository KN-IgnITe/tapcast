package weather

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"reflect"
	"testing"
	"time"
)

// nsure math calculations (avg, amplitude) are correct
func TestProcessDailyData(t *testing.T) {
	input := RawDailyData{
		Time:             []string{"2023-10-01", "2023-10-02"},
		Temperature2MMax: []float64{20.0, 10.0},
		Temperature2MMin: []float64{10.0, -2.0},
		PrecipitationSum: []float64{5.5, 0.0},
	}

	expected := []WeatherSummary{
		{
			Date:          "2023-10-01",
			AvgTemp:       15.0, // (20 + 10) / 2
			TempAmplitude: 10.0, // 20 - 10
			Rain:          5.5,
		},
		{
			Date:          "2023-10-02",
			AvgTemp:       4.0,  // (10 + -2) / 2
			TempAmplitude: 12.0, // 10 - (-2)
			Rain:          0.0,
		},
	}

	result := summarizeWeather(input)

	if !reflect.DeepEqual(result, expected) {
		t.Errorf("processDailyData() mismatch.\nExpected: %+v\nGot: %+v", expected, result)
	}
}

// spin up a mock HTTP server
func setupMockServer(responseBody string, statusCode int) *httptest.Server {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(statusCode)
		fmt.Fprint(w, responseBody)
	})
	return httptest.NewServer(handler)
}

// test fetching successful 200 OK response
func TestFetchCurrentWeather_Success(t *testing.T) {
	mockJSON := `{"current": {"time": "2023-10-27T12:00", "temperature_2m": 15.5, "precipitation": 1.2}}`
	server := setupMockServer(mockJSON, http.StatusOK)
	defer server.Close()

	client := NewClient()
	client.ForecastURL = server.URL // Override real URL with mock server URL

	ctx := context.Background()
	result, err := client.FetchCurrentWeather(ctx, DefaultLat, DefaultLon)

	if err != nil {
		t.Fatalf("failed to fetch current weather: %v", err)
	}

	expected := &CurrentWeatherSummary{
		Date:        "2023-10-27T12:00",
		Temperature: 15.5,
		Rain:        1.2,
	}

	if !reflect.DeepEqual(result, expected) {
		t.Errorf("expected %+v, got %+v", expected, result)
	}
}

// test fetching future weather with a successful 200 OK response
func TestFetchFutureWeather_Success(t *testing.T) {
	mockJSON := `{
		"daily": {
			"time": ["2023-10-28"],
			"temperature_2m_max": [22.0],
			"temperature_2m_min": [12.0],
			"precipitation_sum": [0.0]
		}
	}`
	server := setupMockServer(mockJSON, http.StatusOK)
	defer server.Close()

	client := NewClient()
	client.ForecastURL = server.URL // override real URL

	ctx := context.Background()
	result, err := client.FetchFutureWeather(ctx, DefaultLat, DefaultLon, 1)

	if err != nil {
		t.Fatalf("failed to fetch future weather: %v", err)
	}

	if len(result) != 1 {
		t.Fatalf("expected 1 result, got %d", len(result))
	}

	expectedSummary := WeatherSummary{
		Date:          "2023-10-28",
		AvgTemp:       17.0, // (22+12)/2
		TempAmplitude: 10.0, // 22-12
		Rain:          0.0,
	}

	if !reflect.DeepEqual(result[0], expectedSummary) {
		t.Errorf("expected %+v, got %+v", expectedSummary, result[0])
	}
}

// Test fetching historical weather with a successful 200 OK response
func TestFetchHistoricalWeather_Success(t *testing.T) {
	mockJSON := `{
		"daily": {
			"time": ["2022-05-01"],
			"temperature_2m_max": [15.0],
			"temperature_2m_min": [5.0],
			"precipitation_sum": [10.5]
		}
	}`
	server := setupMockServer(mockJSON, http.StatusOK)
	defer server.Close()

	client := NewClient()
	client.ArchiveURL = server.URL // Override real archive URL

	ctx := context.Background()
	startDate := time.Date(2022, 5, 1, 0, 0, 0, 0, time.UTC)
	endDate := startDate

	result, err := client.FetchHistoricalWeather(ctx, DefaultLat, DefaultLon, startDate, endDate)

	if err != nil {
		t.Fatalf("failed to fetch historical weather: %v", err)
	}

	expectedSummary := WeatherSummary{
		Date:          "2022-05-01",
		AvgTemp:       10.0,
		TempAmplitude: 10.0,
		Rain:          10.5,
	}

	if !reflect.DeepEqual(result[0], expectedSummary) {
		t.Errorf("expected %+v, got %+v", expectedSummary, result[0])
	}
}

// Test handling of HTTP 400 Bad Request
func TestDoRequest_HTTPError(t *testing.T) {
	server := setupMockServer(`{"error": true, "reason": "invalid parameters"}`, http.StatusBadRequest)
	defer server.Close()

	client := NewClient()
	client.ForecastURL = server.URL

	ctx := context.Background()
	_, err := client.FetchCurrentWeather(ctx, DefaultLat, DefaultLon)

	if err == nil {
		t.Error("expected error for HTTP 400, got nil")
	}
}

// Test handling of corrupted JSON response
func TestDoRequest_InvalidJSON(t *testing.T) {
	server := setupMockServer(`{invalid_json_here`, http.StatusOK)
	defer server.Close()

	client := NewClient()
	client.ForecastURL = server.URL

	ctx := context.Background()
	_, err := client.FetchCurrentWeather(ctx, DefaultLat, DefaultLon)

	if err == nil {
		t.Error("expected error for invalid JSON, got nil")
	}
}
