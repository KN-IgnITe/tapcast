package parser

import (
	"fmt"
	"io"
	"strconv"
	"strings"
	"time"

	"github.com/xuri/excelize/v2"
)

type Parser struct {
	GroupColumnIndex     int
	PLUColumnIndex       int
	FirstDateColumnIndex int
	FirstDataRowIndex    int
}

func NewParser() *Parser {
	return &Parser{
		GroupColumnIndex:     0,  // Kolumna A
		PLUColumnIndex:       4,  // Kolumna E
		FirstDateColumnIndex: 7, // Kolumna H pierwsza data
		FirstDataRowIndex:    3,  // Dane zaczynają się od wiersza 4 (indeks 3)
	}
}

func getCell(row []string, colIndex int) string {
	if colIndex < len(row) {
		return strings.TrimSpace(row[colIndex])
	}
	return ""
}

func (p *Parser) Parse(r io.Reader) (Raport, error) {
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

	indicatorRow := rows[1] // Wiersz określający czy to nowy dzień (zawiera nazwy zmiany np. 349)
	datesRow := rows[2]     // Wiersz zawierający daty
	maxCols := len(datesRow)

	for colIdx := p.FirstDateColumnIndex; colIdx < maxCols; colIdx++ {
		dateStr := getCell(datesRow, colIdx)
		if dateStr == "" {
			continue
		}

		parsedDate, err := time.Parse("02.01.2006", dateStr)
		if err != nil {
			continue
		}

		dayIndicator := getCell(indicatorRow, colIdx)
		isNewDay := dayIndicator != ""

		articles := p.extractArticlesFromColumn(rows, colIdx)

		if isNewDay {
			newDay := Day{
				Date:     parsedDate,
				Articles: []Article{},
			}
			p.mergeArticles(&newDay, articles)
			raport.Days = append(raport.Days, newDay)

		} else {
			if len(raport.Days) == 0 {
				continue
			}
			lastDayIdx := len(raport.Days) - 1
			p.mergeArticles(&raport.Days[lastDayIdx], articles)
		}
	}

	return raport, nil
}

func (p *Parser) extractArticlesFromColumn(rows [][]string, quantityColIdx int) []Article {
	var articles []Article
	currentGroup := "" //group jest tylko w jedym wierszu i potem jest puste az nie pojawi sie nowy grup
	currentPLU := ""   // nieraz jest PLU a nizej jest puste ale to puste tez jest tym PLU wiec tak samo

	for rowIdx := p.FirstDataRowIndex; rowIdx < len(rows); rowIdx++ {
		groupCell := getCell(rows[rowIdx], p.GroupColumnIndex)
		// pomijamy nazwe zmiany RAZEM bo manualnie dodajemy z dat w na jednej zmianie
		if groupCell != "" && !strings.Contains(strings.ToLower(groupCell), "razem") {
			currentGroup = groupCell
		}

		pluCell := getCell(rows[rowIdx], p.PLUColumnIndex)

		//pomijamy PLU razem bo jest bez sensu
		if strings.Contains(strings.ToLower(pluCell), "razem") {
			currentPLU = ""
			continue
		}

		if pluCell != "" {
			currentPLU = pluCell
		}

		if currentPLU == "" {
			continue
		}

		quantityStr := getCell(rows[rowIdx], quantityColIdx)
		if quantityStr != "" {
			quantityStr = strings.ReplaceAll(quantityStr, ",", ".")
			quantity, err := strconv.ParseFloat(quantityStr, 64)

			if err == nil && quantity != 0 {
				articles = append(articles, Article{
					PLU:      currentPLU,
					Group:    currentGroup,
					Quantity: quantity,
				})
			}
		}
	}

	return articles
}

func (p *Parser) mergeArticles(day *Day, newArticles []Article) {
	for _, newArt := range newArticles {
		foundIdx := -1
		for i, existingArt := range day.Articles {
			if existingArt.PLU == newArt.PLU {
				foundIdx = i
				break
			}
		}

		if foundIdx != -1 {
			day.Articles[foundIdx].Quantity += newArt.Quantity
		} else {
			day.Articles = append(day.Articles, newArt)
		}
	}
}
