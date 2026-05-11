package api

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"path/filepath"
)

type UploadResponseXLSX struct {
	Message  string `json:"message"`
	Filename string `json:"filename"`
	Size     int64  `json:"size_bytes"`
}

func UploadHandlerXLSX(w http.ResponseWriter, r *http.Request) {

	if r.Method != http.MethodPost {
		http.Error(w, "Metoda niedozwolona", http.StatusMethodNotAllowed)
		return
	}

	//z fronta wysylaja FormData
	file, header, err := r.FormFile("file") //nazwa file to klucz tu musi byc tak jak w froncie
	if err != nil {
		http.Error(w, "Błąd pobierania pliku", http.StatusBadRequest)
		return
	}
	defer func() { _ = file.Close() }()

	//tu juz mamy nasz plik file

	if ext := filepath.Ext(header.Filename); ext != ".xlsx" {
		http.Error(w, "Dozwolone są tylko pliki .xlsx", http.StatusBadRequest)
		return
	}

	size, err := io.Copy(io.Discard, file)
	if err != nil {
		http.Error(w, "Błąd podczas odczytu pliku", http.StatusInternalServerError)
		return
	}

	//przewijamy strumiej na poczatek bo wczesniej przeszlismy przez caly zeby zczytac rozmiar
	_, err = file.Seek(0, io.SeekStart)
	if err != nil {
		http.Error(w, "Błąd resetowania pliku", http.StatusInternalServerError)
		return
	}

	// tu przekazujemy plik do jakies funkcji ktora go przemieli
	//err = processExcelFile(file)

	fmt.Printf("Otrzymano plik: %s (Rozmiar: %d bajtów)\n", header.Filename, size)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(UploadResponseXLSX{
		Message:  "Plik przyjęty pomyślnie",
		Filename: header.Filename,
		Size:     size,
	})
}
