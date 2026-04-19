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
	ColAIndex int
	ColEIndex int
	ColRIndex int
	StartRow  int
}

func NewParser() *Parser {
	return &Parser{
		ColAIndex: 0,
		ColEIndex: 4,
		ColRIndex: 17,
		StartRow:  3,
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

	row2 := rows[1]
	row3 := rows[2]
	maxCols := len(row3)

	for c := p.ColRIndex; c < maxCols; c++ {
		dateStr := getCell(row3, c)
		if dateStr == "" {
			continue
		}

		parsedDate, err := time.Parse("02.01.2006", dateStr)
		if err != nil {
			continue
		}

		valRow2 := getCell(row2, c)
		isNewDay := valRow2 != ""

		articles := p.extractArticlesFromColumn(rows, c)

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

func (p *Parser) extractArticlesFromColumn(rows [][]string, colIndex int) []Article {
	var articles []Article
	currentGroup := ""
	currentPLU := ""

	for r := p.StartRow; r < len(rows); r++ {
		colA := getCell(rows[r], p.ColAIndex)
		if colA != "" && !strings.Contains(strings.ToLower(colA), "razem") {
			currentGroup = colA
		}

		pluCell := getCell(rows[r], p.ColEIndex)
		
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

		qtyStr := getCell(rows[r], colIndex)
		if qtyStr != "" {
			qtyStr = strings.ReplaceAll(qtyStr, ",", ".")
			qty, err := strconv.ParseFloat(qtyStr, 64)

			if err == nil && qty != 0 {
				articles = append(articles, Article{
					PLU:      currentPLU,
					Group:    currentGroup,
					Quantity: qty,
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