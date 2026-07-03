package parser

import (
	"time"
)

type Article struct {
	PLU      string  `json:"plu"`
	Group    string  `json:"group"`
	Quantity float64 `json:"quantity"`
}

type Day struct {
	Date     time.Time `json:"date"`
	Articles []Article `json:"articles"`
}

type Report struct {
	Days []Day `json:"days"`
}
