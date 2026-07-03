package test

import (
	"os"
	"testing"
	"time"

	"github.com/m1kus3q/pubpredictor/backend/internal/parser"
)

func TestParseExcelToStruct(t *testing.T) {
	filePath := "przyklad_pos.xlsx"
	file, err := os.Open(filePath)
	if err != nil {
		t.Fatalf("Failed to open test file '%s': %v", filePath, err)
	}
	defer func() { _ = file.Close() }()

	p := parser.NewParser()
	report, err := p.Parse(file)
	if err != nil {
		t.Fatalf("Error occurred during parsing: %v", err)
	}

	if len(report.Days) == 0 {
		t.Fatalf("Error: Parser did not return any days from the file")
	}

	var foundDay *parser.Day
	var foundArticle *parser.Article

	targetDate := time.Date(2025, 1, 9, 0, 0, 0, 0, time.UTC)

	for i := range report.Days {
		if report.Days[i].Date.Equal(targetDate) {
			foundDay = &report.Days[i]
			break
		}
	}

	if foundDay == nil {
		t.Fatalf("Test failed: date 01.09.2025 not found in report")
	}

	for i := range foundDay.Articles {
		if foundDay.Articles[i].PLU == "539" {
			foundArticle = &foundDay.Articles[i]
			break
		}
	}

	if foundArticle == nil {
		t.Errorf("Article with PLU 539 not found on 09.01.2025")
	} else {
		expectedQty := 5.0
		if foundArticle.Quantity != expectedQty {
			t.Errorf("Incorrect quantity for PLU 539 on 01.09.2025. Expected: %.2f, got: %.2f",
				expectedQty, foundArticle.Quantity)
		}
	}

	// testing the first day after fix to read from the 1st day

	targetDate = time.Date(2025, 1, 3, 0, 0, 0, 0, time.UTC)

	for i := range report.Days {
		if report.Days[i].Date.Equal(targetDate) {
			foundDay = &report.Days[i]
			break
		}
	}

	if foundDay == nil {
		t.Fatalf("Test failed: date 01.03.2025 not found in report")
	}

	for i := range foundDay.Articles {
		if foundDay.Articles[i].PLU == "537" {
			foundArticle = &foundDay.Articles[i]
			break
		}
	}

	if foundArticle == nil {
		t.Errorf("Article with PLU 537 not found on 03.01.2025")
	} else {
		expectedQty := 3.0
		if foundArticle.Quantity != expectedQty {
			t.Errorf("Incorrect quantity for PLU 537 on 01.03.2025. Expected: %.2f, got: %.2f",
				expectedQty, foundArticle.Quantity)
		}
	}
}
