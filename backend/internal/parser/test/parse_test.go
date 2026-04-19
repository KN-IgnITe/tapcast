package test

import (
	"encoding/json"
	"os"
	"testing"

	"github.com/m1kus3q/pubpredictor/backend/internal/parser"

)

func TestParseExcelToStruct(t *testing.T) {
	filePath := "przyklad_pos.xlsx"
	file, err := os.Open(filePath)
	if err != nil {
		t.Fatalf("Nie udało się otworzyć pliku testowego '%s': %v", filePath, err)
	}
	defer file.Close()

	raport, err := parser.ParseExcelToStruct(file)
	if err != nil {
		t.Fatalf("Wystąpił błąd podczas parsowania: %v", err)
	}

	if len(raport.Days) == 0 {
		t.Errorf("Oczekiwano sparsowanych dni, ale raport jest pusty")
	}

	jsonData, err := json.MarshalIndent(raport, "", "  ")
	if err != nil {
		t.Fatalf("Nie udało się zrzutować wyniku do JSON: %v", err)
	}
	
	t.Logf("Sparsowany raport:\n%s", string(jsonData))
}