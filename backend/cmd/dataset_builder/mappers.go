package main

import (
	"strconv"
	"time"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"
	"github.com/m1kus3q/pubpredictor/backend/internal/parser"
)

func MapWeather(ws weather.WeatherSummary, locationID int) (models.Weather, error) {
	// assumes data format YYYY-MM-DD
	parsedDate, err := time.Parse(time.DateOnly, ws.Date)
	if err != nil {
		return models.Weather{}, err
	}

	return models.Weather{
		WeatherDate:   parsedDate,
		LocationID:    locationID,
		AvgTemp:       ws.AvgTemp,
		TempAmplitude: ws.TempAmplitude,
		Rain:          ws.Rain,
	}, nil
}

func MapDay(date time.Time) models.Day {
	weekday := date.Weekday()
	isWorking := weekday != time.Saturday && weekday != time.Sunday

	return models.Day{
		DayDate:   date,
		IsWorking: isWorking,
	}
}

func MapArticle(pa parser.Article, barID int) (models.Article, error) {
	plu, err := strconv.Atoi(pa.PLU)
	if err != nil {
		return models.Article{}, err
	}

	return models.Article{
		BarID: barID,
		Plu:   plu,
		//change category to string
	}, nil
}

func MapSale(pa parser.Article, date time.Time, barID int) (models.Sale, error) {
	plu, err := strconv.Atoi(pa.PLU)
	if err != nil {
		return models.Sale{}, err
	}

	return models.Sale{
		SaleDate: date,
		BarID:    barID,
		Plu:      plu,
		Amount:   int(pa.Quantity),
	}, nil
}
