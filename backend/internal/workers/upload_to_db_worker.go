package workers

import (
	"context"
	"errors"
	"io"
	"strconv"
	"time"

	"gorm.io/gorm"

	"log"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	dbclient "github.com/m1kus3q/pubpredictor/backend/internal/db/client"
	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"
	"github.com/m1kus3q/pubpredictor/backend/internal/message_channel"
	"github.com/m1kus3q/pubpredictor/backend/internal/parser"

	"github.com/m1kus3q/pubpredictor/backend/internal/minio"
)

const (
	periodTime = 3 * time.Minute
)

type Storage interface {
	GetObject(ctx context.Context, bucketName string, key string) (io.ReadCloser, error)
	ListObjectsKeys(ctx context.Context, bucketName string) ([]string, error)
	GetTag(ctx context.Context, bucketName string, key string, tagKey string) (*string, error)
	SetTag(ctx context.Context, bucketName string, key string, tagKey string, tagValue string) error
}
type UploadWorker struct {
	StorageClient Storage
	BucketName    string
	Queue         message_channel.MessageQueue
	DBClient      *dbclient.DBClient
	WeatherClient weather.WeatherClient
}

func (w *UploadWorker) Run() {
	ctx := context.Background()

	jobs, err := w.Queue.Subscribe()
	if err != nil {
		log.Println("Message queue closed")
		return
	}

	ticker := time.NewTicker(periodTime)
	defer ticker.Stop()

	for {
		select {
		case objectKey := <-jobs:
			err := w.processObject(ctx, objectKey)
			if err != nil {
				log.Printf("Failed to process %s: %v", objectKey, err)
			}
		case <-ticker.C:
			w.scanStorage(ctx)
		}
	}
}

func (w *UploadWorker) scanStorage(ctx context.Context) {
	keys, err := w.StorageClient.ListObjectsKeys(ctx, w.BucketName)
	if err != nil {
		log.Printf("Failed to list objects in bucket %q: %v", w.BucketName, err)
		return
	}
	for _, key := range keys {
		status, err := w.StorageClient.GetTag(ctx, w.BucketName, key, minio.TagStatus)
		if err != nil {
			log.Printf("Failed to get status tag for %q: %v", key, err)
			continue
		}
		if *status == minio.StatusQueued {
			_ = w.processObject(ctx, key)
		}
	}
}

func (w *UploadWorker) processObject(ctx context.Context, objectKey string) error {
	file, err := w.StorageClient.GetObject(ctx, w.BucketName, objectKey)
	if err != nil {
		return err
	}
	defer func() { _ = file.Close() }()

	raport, err := w.parseReport(file)
	if err != nil {
		return err
	}
	weatherMap, err := w.parseWeatherMap(ctx, raport)
	if err != nil {
		return err
	}

	err = w.doTransaction(raport, weatherMap)
	if err != nil {
		return err
	}

	err = w.StorageClient.SetTag(ctx, w.BucketName, objectKey, minio.TagStatus, minio.StatusParsed)
	if err != nil {
		return err
	}

	log.Printf("Successfully save file %s", objectKey)

	return nil
}

func (w *UploadWorker) parseReport(file io.Reader) (*parser.Report, error) {
	p := parser.NewParser()
	raport, err := p.Parse(file)
	if err != nil {
		return nil, errors.New("parse error: " + err.Error())
	}

	if len(raport.Days) == 0 {
		return nil, errors.New("no valid days found")
	}
	return &raport, nil
}

func (w *UploadWorker) parseWeatherMap(ctx context.Context, raport *parser.Report) (map[string]weather.WeatherSummary, error) {
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
	weatherData, err := w.WeatherClient.FetchHistoricalWeather(ctx, weather.DefaultLat, weather.DefaultLon, minDate, maxDate)
	if err != nil {
		return nil, errors.New("weather API error: " + err.Error())
	}

	// Map for quick weather lookups
	weatherMap := make(map[string]weather.WeatherSummary)
	for _, wData := range weatherData {
		weatherMap[wData.Date] = wData
	}

	return weatherMap, nil
}

func (w *UploadWorker) doTransaction(raport *parser.Report,
	weatherMap map[string]weather.WeatherSummary) error {
	// Save everything to DB
	db := w.DBClient.GetDB()

	return db.Transaction(func(tx *gorm.DB) error {

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
}
