package weather

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestFetchForecast_Success(t *testing.T) {
	// JSON, który zwróciłoby API
	mockJSON := `{
		"latitude": 51.1,
		"longitude": 17.0,
		"current": {
			"temperature_2m": 22.5,
			"wind_speed_10m": 15.0
		}
	}`

	// uruchomienie lokalnego serwera testowego
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Opcjonalnie: sprawdzamy czy parametry w URL się zgadzają
		lat := r.URL.Query().Get("latitude")
		if lat != "51.1000" {
			t.Errorf("expected latitude 51.1000, got %s", lat)
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, mockJSON)
	}))
	defer server.Close()

	// Inicjalizacja klienta i podpięcie go pod serwer testowy
	client := NewClient()
	client.BaseURL = server.URL //podmieniNa adresu na lokalny serwer

	forecast, err := client.FetchForecast(context.Background(), 51.1, 17.0)

	// asercje
	if err != nil {
		t.Fatalf("FetchForecast failed: %v", err)
	}

	if forecast.Latitude != 51.1 {
		t.Errorf("expected latitude 51.1, got %f", forecast.Latitude)
	}

	if forecast.Current.Temperature2M != 22.5 {
		t.Errorf("expected temperature 22.5, got %f", forecast.Current.Temperature2M)
	}
}

func TestFetchForecast_ServerError(t *testing.T) {
	// Serwer zwracający błąd 500
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewClient()
	client.BaseURL = server.URL

	// Próba pobrania danych
	_, err := client.FetchForecast(context.Background(), 51.1, 17.0)

	// Sprawdzamy czy błąd został wykryty
	if err == nil {
		t.Error("expected error for HTTP 500, but got nil")
	}
}

func TestFetchForecast_Integration(t *testing.T) {
	// Inicjalizacja prawdziwego klienta
	client := NewClient()

	// Context z timeoutem (jakby API za wolno działało)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// wywołanie dla realnych współrzędnych Wrocławia
	forecast, err := client.FetchForecast(ctx, DefaultLat, DefaultLon)

	// Sprawdzenie błędów
	if err != nil {
		t.Fatalf("Błąd podczas połączenia z Open-Meteo: %v", err)
	}

	// wyniki w terminalu (dodac flage -v w tescie)
	t.Logf("Sukces! Pobrane dane dla: %f, %f", forecast.Latitude, forecast.Longitude)
	t.Logf("Strefa czasowa: %s", forecast.Timezone)
	t.Logf("Aktualna temperatura: %.1f°C", forecast.Current.Temperature2M)
	t.Logf("Prędkość wiatru: %.1f km/h", forecast.Current.WindSpeed10M)

	// asercje
	if forecast.Timezone == "" {
		t.Error("Błąd: Otrzymano pustą strefę czasową")
	}

	if len(forecast.Hourly.Time) == 0 {
		t.Error("Błąd: Brak danych godzinowych w odpowiedzi")
	}
}
