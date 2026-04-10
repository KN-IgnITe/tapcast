package parser

import "time"

type MLProjectContract struct {
	DayData []Day `json:"day_data"`
}

type Day struct {
	Weather          Weather   `json:"weather"`
	Sells            Sells     `json:"sells"`
	
	Date             time.Time `json:"date"`
	DayOfWeek        int       `json:"day_of_week"`
	IsWorking        bool      `json:"is_working"`
	IsNextDayWorking bool      `json:"is_next_day_working"`
}

type Weather struct {
	AvgTemp       float64 `json:"avg_temp"`
	TempAmplitude float64 `json:"temp_amplitude"`
	Rain          float64 `json:"rain,omitempty"`
}

type Sells struct {
	Articles []Article `json:"articles"`
}

type Article struct {
	PLU             int `json:"PLU"`
	Category        int `json:"category"`
	Ammount         int `json:"ammount"`
	YesterdayDemand int `json:"yesterday_demand"`
	WeekAgoDemand   int `json:"week_ago_demand"`
}