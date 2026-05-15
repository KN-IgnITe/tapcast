package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"
	"github.com/m1kus3q/pubpredictor/backend/internal/parser"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func parseData(path string) (report parser.Raport, err error) {
	file, err := os.Open(path)
	if err != nil {
		return parser.Raport{}, err
	}

	defer func() {
		closeErr := file.Close()
		if err == nil && closeErr != nil {
			err = closeErr
		}
	}()

	dataParser := parser.NewParser()
	return dataParser.Parse(file)
}
func fetchWeather(report parser.Raport) ([]weather.WeatherSummary, error) {
	if len(report.Days) == 0 {
		return nil, fmt.Errorf("empty report")
	}

	weatherClient := weather.NewClient()
	ctx := context.Background()
	firstDay := report.Days[0].Date
	lastDay := report.Days[len(report.Days)-1].Date

	return weatherClient.FetchHistoricalWeather(ctx, weather.DefaultLat, weather.DefaultLon, firstDay, lastDay)
}

func main() {
	// read file path as option
	filePath := flag.String("file", "file.txt", "Ścieżka do pliku z raportem") //usunac wartosc domyslna
	flag.Parse()

	report, err := parseData(*filePath)
	if err != nil {
		log.Fatalf("failed to parse data: %v", err)
	}

	requiredEnvVars := []string{"DB_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD", "DB_NAME", "DB_PORT"}
	for _, envVar := range requiredEnvVars {
		if os.Getenv(envVar) == "" {
			log.Fatalf("required environment variable %s is not set", envVar)
		}
	}

	dsn := fmt.Sprintf(
		"host=%s user=%s password=%s dbname=%s port=%s sslmode=disable",
		os.Getenv("DB_HOST"), os.Getenv("POSTGRES_USER"), os.Getenv("POSTGRES_PASSWORD"), os.Getenv("DB_NAME"), os.Getenv("DB_PORT"),
	)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}

	// ensure schema matches models
	err = db.AutoMigrate(&models.Location{}, &models.Bar{}, &models.Day{}, &models.Weather{}, &models.Article{}, &models.Sale{})
	if err != nil {
		log.Fatalf("failed to auto migrate database: %v", err)
	}

	// setup mock location and bar
	mockLocation := models.Location{Name: "Wrocław"}
	db.FirstOrCreate(&mockLocation, models.Location{Name: "Wrocław"})

	mockBar := models.Bar{LocationID: mockLocation.LocationID, Name: "Mocked Pub"}
	db.FirstOrCreate(&mockBar, models.Bar{Name: "Mocked Pub"})

	// process weather
	weatherSummaries, err := fetchWeather(report)
	if err != nil {
		log.Fatalf("failed to fetch weather: %v", err)
	}

	for _, ws := range weatherSummaries {
		dbWeather, err := MapWeather(ws, mockLocation.LocationID)
		if err != nil {
			log.Printf("failed to map weather for date %s: %v", ws.Date, err)
			continue
		}
		// create Day if it doesn't exist yet
		dbDay := MapDay(dbWeather.WeatherDate)
		db.FirstOrCreate(&dbDay, models.Day{DayDate: dbDay.DayDate})

		db.Save(&dbWeather)
	}

	// process days, articles, and sales
	for _, parsedDay := range report.Days {
		dbDay := MapDay(parsedDay.Date)
		db.Save(&dbDay)

		for _, parsedArticle := range parsedDay.Articles {
			dbArticle, err := MapArticle(parsedArticle, mockBar.BarID)
			if err != nil {
				log.Printf("failed to map article PLU %s: %v", parsedArticle.PLU, err)
				continue
			}
			db.FirstOrCreate(&dbArticle, models.Article{BarID: dbArticle.BarID, Plu: dbArticle.Plu})

			dbSale, err := MapSale(parsedArticle, parsedDay.Date, mockBar.BarID)
			if err != nil {
				log.Printf("failed to map sale for PLU %s: %v", parsedArticle.PLU, err)
				continue
			}
			db.Save(&dbSale)
		}
	}
}
