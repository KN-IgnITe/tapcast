package parser

import (
	"time"
)

type Article struct {
	PLU   string  `json:"plu"`
	Group string  `json:"group"`
	Quantity float64 `json:"quantity"`
}

type Day struct {
	Date     time.Time `json:"data"`
	Articles []Article `json:"articles"`
}

type Raport struct {
	Days []Day `json:"days"`
}
