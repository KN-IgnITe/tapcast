package parser

import (
	"fmt"
	"io"
	"strconv"
	"strings"
	"time"

	"github.com/xuri/excelize/v2"
)

func getCell(row []string, colIndex int) string {
	if colIndex < len(row) {
		return strings.TrimSpace(row[colIndex])
	}
	return ""
}

func ParseExcelToStruct(r io.Reader) (Raport, error) {
	raport := Raport{}

	f, err := excelize.OpenReader(r)
	if err != nil {
		return raport, fmt.Errorf("błąd otwierania pliku excel: %w", err)
	}
	defer f.Close()

	sheetName := f.GetSheetName(f.GetActiveSheetIndex())
	rows, err := f.GetRows(sheetName)
	if err != nil {
		return raport, fmt.Errorf("błąd pobierania wierszy: %w", err)
	}

	if len(rows) < 4 {
		return raport, fmt.Errorf("plik nie posiada wystarczającej liczby wierszy")
	}

	row2 := rows[1]
	row3 := rows[2]

	const colAIndex = 0
	const colEIndex = 4
	const colRIndex = 17

	maxCols := len(row3)

	for c := colRIndex; c < maxCols; c++ {
		dateStr := getCell(row3, c)

		if dateStr == "" {
			continue
		}

		parsedDate, err := time.Parse("02.01.2006", dateStr)
		if err != nil {
			fmt.Printf("Ostrzeżenie: nie udało się sparsować daty %s w kolumnie %d: %v\n", dateStr, c, err)
			continue
		}
		valRow2 := getCell(row2, c)
		isNewDay := valRow2 != ""

		if isNewDay {
			newDay := Day{
				Date:     parsedDate,
				Articles: []Article{},
			}

			currentGroup := ""

			for r := 3; r < len(rows); r++ {
				colA := getCell(rows[r], colAIndex)
				if colA != "" && !strings.Contains(strings.ToLower(colA), "razem") {
					currentGroup = colA
				}

				plu := getCell(rows[r], colEIndex)

				if plu == "" || strings.Contains(strings.ToLower(plu), "razem") {
					continue
				}

				qtyStr := getCell(rows[r], c)
				if qtyStr != "" {
					qtyStr = strings.ReplaceAll(qtyStr, ",", ".")
					qty, _ := strconv.ParseFloat(qtyStr, 64)

					if qty != 0 {
						newDay.Articles = append(newDay.Articles, Article{
							PLU:      plu,
							Group:    currentGroup,
							Quantity: qty,
						})
					}
				}
			}
			raport.Days = append(raport.Days, newDay)

		} else {
			if len(raport.Days) == 0 {
				continue
			}

			lastDayIdx := len(raport.Days) - 1
			currentGroup := ""

			for r := 3; r < len(rows); r++ {
				colA := getCell(rows[r], colAIndex)
				if colA != "" && !strings.Contains(strings.ToLower(colA), "razem") {
					currentGroup = colA
				}

				plu := getCell(rows[r], colEIndex)

				if plu == "" || strings.Contains(strings.ToLower(plu), "razem") {
					continue
				}

				qtyStr := getCell(rows[r], c)
				if qtyStr != "" {
					qtyStr = strings.ReplaceAll(qtyStr, ",", ".")
					qty, _ := strconv.ParseFloat(qtyStr, 64)

					if qty != 0 {
						foundIdx := -1
						for i, art := range raport.Days[lastDayIdx].Articles {
							if art.PLU == plu {
								foundIdx = i
								break
							}
						}

						if foundIdx != -1 {
							raport.Days[lastDayIdx].Articles[foundIdx].Quantity += qty
						} else {
							raport.Days[lastDayIdx].Articles = append(raport.Days[lastDayIdx].Articles, Article{
								PLU:      plu,
								Group:    currentGroup,
								Quantity: qty,
							})
						}
					}
				}
			}
		}
	}

	return raport, nil
}
