package scheduler

import (
	"context"
	"testing"

	"github.com/m1kus3q/pubpredictor/backend/internal/client/weather"
	"github.com/m1kus3q/pubpredictor/backend/internal/scheduler/mocks"

	"go.uber.org/mock/gomock"
)

func TestRun(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	weatherMock := mocks.NewMockWeatherClient(ctrl)
	dbMock := mocks.NewMockDB(ctrl)

	job := NewWeatherJob(weatherMock, dbMock)

	summaries := []weather.WeatherSummary{
		{
			Date:          "2026-07-26",
			AvgTemp:       20.5,
			TempAmplitude: 7.0,
			Rain:          1.2,
		},
		{
			Date:          "2026-07-27",
			AvgTemp:       22.0,
			TempAmplitude: 6.5,
			Rain:          0,
		},
	}

	weatherMock.EXPECT().
		FetchFutureWeather(gomock.Any(), weather.DefaultLat, weather.DefaultLon, defaultForecastDays).
		Return(summaries, nil)

	dbMock.EXPECT().
		Upsert(gomock.Any(), gomock.Any()).
		Times(2)

	job.Run(context.Background())
}
