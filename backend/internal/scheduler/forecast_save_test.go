//go:build integration

package scheduler

import (
	"context"
	"testing"
	"time"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	db "github.com/m1kus3q/pubpredictor/backend/internal/db/client"
	"github.com/m1kus3q/pubpredictor/backend/internal/db/models"
	"github.com/m1kus3q/pubpredictor/backend/internal/scheduler/mocks"

	"github.com/stretchr/testify/require"
	"go.uber.org/mock/gomock"
)

func TestForecastSave(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	weatherMock := mocks.NewMockWeatherClient(ctrl)

	config, err := db.NewDBConfig()
	require.NoError(t, err)

	dbClient, err := db.NewDBClient(config)
	require.NoError(t, err)

	require.NoError(t,
		dbClient.Upsert(context.Background(), &models.Location{
			LocationID: 1,
			Name:       "Test",
		}),
	)

	dayStr := "2026-07-26"

	day, err := time.Parse("2006-01-02", dayStr)
	require.NoError(t, err)

	require.NoError(t,
		dbClient.Upsert(context.Background(), &models.Day{
			DayDate:   day,
			IsWorking: false,
		}),
	)

	summaries := []weather.WeatherSummary{
		{
			Date:          dayStr,
			AvgTemp:       20.5,
			TempAmplitude: 7.0,
			Rain:          1.2,
		},
	}

	weatherMock.EXPECT().
		FetchFutureWeather(
			gomock.Any(),
			weather.DefaultLat,
			weather.DefaultLon,
			defaultForecastDays,
		).
		Return(summaries, nil)

	job := NewWeatherJob(weatherMock, dbClient)

	ctx := context.Background()
	job.Run(ctx)

	var forecast models.WeatherForecast

	pattern := models.WeatherForecast{
		WeatherDate: day,
		LocationID:  1,
	}

	err = dbClient.FirstByExample(ctx, &forecast, pattern)
	require.NoError(t, err)

	require.Equal(t, 1, forecast.LocationID)
	require.Equal(t, 20.5, forecast.AvgTemp)
	require.Equal(t, 7.0, forecast.TempAmplitude)
	require.Equal(t, 1.2, forecast.Rain)
	require.False(t, forecast.ForecastDate.IsZero())
}
