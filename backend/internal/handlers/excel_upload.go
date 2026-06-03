package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	dbclient "github.com/m1kus3q/pubpredictor/backend/internal/db/client"
	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"
	"github.com/m1kus3q/pubpredictor/backend/internal/parser"
	"gorm.io/gorm"
)

// Holds DB and Weather API dependencies.
type UploadHandler struct {
	DBClient      *dbclient.DBClient
	WeatherClient weather.WeatherClient
}

func (h *UploadHandler) HandleXLSX(w http.ResponseWriter, r *http.Request) {
	// Get file from multipart form
	file, _, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "Failed to read file", http.StatusBadRequest)
		return
	}
	defer func() { _ = file.Close() }()

	// Parse Excel file
	p := parser.NewParser()
	raport, err := p.Parse(file)
	if err != nil {
		http.Error(w, "Parse error: "+err.Error(), http.StatusInternalServerError)
		return
	}

	if len(raport.Days) == 0 {
		http.Error(w, "No valid days found", http.StatusBadRequest)
		return
	}

	// Find date range for weather data.
	minDate := raport.Days[0].Date
	maxDate := raport.Days[0].Date
	for _, day := range raport.Days {
		if day.Date.Before(minDate) {
			minDate = day.Date
		}
		if day.Date.After(maxDate) {
			maxDate = day.Date
		}
	}

	// Fetch historical weather
	weatherData, err := h.WeatherClient.FetchHistoricalWeather(r.Context(), weather.DefaultLat, weather.DefaultLon, minDate, maxDate)
	if err != nil {
		http.Error(w, "Weather API error: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Map for quick weather lookups
	weatherMap := make(map[string]weather.WeatherSummary)
	for _, wData := range weatherData {
		weatherMap[wData.Date] = wData
	}

	// Save everything to DB
	db := h.DBClient.GetDB()

	err = db.Transaction(func(tx *gorm.DB) error {

		const defaultLocationID = 1
		const defaultBarID = 1

		mockLocation := models.Location{Name: "Mocked City"}
		if err := tx.FirstOrCreate(&mockLocation, models.Location{LocationID: defaultLocationID}).Error; err != nil {
			return err
		}

		mockBar := models.Bar{LocationID: defaultLocationID, Name: "Mocked Pub"}
		if err := tx.FirstOrCreate(&mockBar, models.Bar{BarID: defaultBarID}).Error; err != nil {
			return err
		}

		for _, parsedDay := range raport.Days {

			weekday := parsedDay.Date.Weekday()
			isWorking := weekday != time.Saturday && weekday != time.Sunday

			dayModel := models.Day{
				DayDate:   parsedDay.Date,
				IsWorking: isWorking,
			}
			if err := tx.Save(&dayModel).Error; err != nil {
				return err
			}

			// Save Weather
			dateStr := parsedDay.Date.Format(time.DateOnly)
			if wSummary, exists := weatherMap[dateStr]; exists {
				weatherModel := models.Weather{
					WeatherDate:   parsedDay.Date,
					LocationID:    defaultLocationID,
					AvgTemp:       wSummary.AvgTemp,
					TempAmplitude: wSummary.TempAmplitude,
					Rain:          wSummary.Rain,
				}
				if err := tx.Save(&weatherModel).Error; err != nil {
					return err
				}
			}

			// Save Articles and Sales
			for _, article := range parsedDay.Articles {
				pluInt, _ := strconv.Atoi(article.PLU)

				articleModel := models.Article{
					BarID:    defaultBarID,
					Plu:      pluInt,
					Category: article.Group,
				}
				if err := tx.Save(&articleModel).Error; err != nil {
					return err
				}

				saleModel := models.Sale{
					SaleDate: parsedDay.Date,
					BarID:    defaultBarID,
					Plu:      pluInt,
					Amount:   int(article.Quantity),
				}
				if err := tx.Save(&saleModel).Error; err != nil {
					return err
				}
			}
		}
		return nil
	})

	if err != nil {
		http.Error(w, "DB save error: "+err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(map[string]string{"status": "success", "message": "data processed successfully"}); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
	}
}
