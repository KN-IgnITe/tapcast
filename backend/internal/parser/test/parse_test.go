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
		t.Fatalf("Nie udało się otworzyć pliku testowego '%s': %v", filePath, err)
	}
	defer file.Close()

	p := parser.NewParser()
	raport, err := p.Parse(file)
	if err != nil {
		t.Fatalf("Wystąpił błąd podczas parsowania: %v", err)
	}

	if len(raport.Days) == 0 {
		t.Fatalf("Błąd: Parser nie zwrócił żadnych dni z pliku")
	}

	targetDate := time.Date(2025, 1, 9, 0, 0, 0, 0, time.UTC)
	var foundDay *parser.Day

	for i := range raport.Days {
		if raport.Days[i].Date.Equal(targetDate) {
			foundDay = &raport.Days[i]
			break
		}
	}

	if foundDay == nil {
		t.Fatalf("Test nieudany: w raporcie nie znaleziono daty 01.09.2025")
	}

	var foundArticle *parser.Article
	for i := range foundDay.Articles {
		if foundDay.Articles[i].PLU == "539" {
			foundArticle = &foundDay.Articles[i]
			break
		}
	}

	if foundArticle == nil {
		t.Errorf("W dniu 09.01.2025 nie znaleziono artykułu o PLU 539")
	} else {
		expectedQty := 5.0
		if foundArticle.Quantity != expectedQty {
			t.Errorf("Błędna ilość dla PLU 539 w dniu 01.09.2025. Oczekiwano: %.2f, otrzymano: %.2f", 
				expectedQty, foundArticle.Quantity)
		}
	}

}