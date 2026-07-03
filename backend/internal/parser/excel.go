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
		GroupColumnIndex:     0, // Column A
		PLUColumnIndex:       4, // Column E
		FirstDateColumnIndex: 7, // Column H first date
		FirstDataRowIndex:    3, // Data starts from row 4 (index 3)
	}
}

func getCell(row []string, colIndex int) string {
	if colIndex < len(row) {
		return strings.TrimSpace(row[colIndex])
	}
	return ""
}

func (p *Parser) Parse(r io.Reader) (Report, error) {
	report := Report{}

	f, err := excelize.OpenReader(r)
	if err != nil {
		return report, fmt.Errorf("error opening excel file: %w", err)
	}
	defer func() { _ = f.Close() }()

	sheetName := f.GetSheetName(f.GetActiveSheetIndex())
	rows, err := f.GetRows(sheetName)
	if err != nil {
		return report, fmt.Errorf("error getting rows: %w", err)
	}

	if len(rows) < 4 {
		return report, fmt.Errorf("file does not have enough rows")
	}

	indicatorRow := rows[1] // Row indicating if it's a new day (contains shift names e.g., 349)
	datesRow := rows[2]     // Row containing dates
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
			report.Days = append(report.Days, newDay)

		} else {
			if len(report.Days) == 0 {
				continue
			}
			lastDayIdx := len(report.Days) - 1
			p.mergeArticles(&report.Days[lastDayIdx], articles)
		}
	}

	return report, nil
}

func (p *Parser) extractArticlesFromColumn(rows [][]string, quantityColIdx int) []Article {
	var articles []Article
	currentGroup := ""
	currentPLU := ""

	for rowIdx := p.FirstDataRowIndex; rowIdx < len(rows); rowIdx++ {
		groupCell := getCell(rows[rowIdx], p.GroupColumnIndex)

		// skip shift name TOTAL (razem) because we manually add from dates in one shift
		if groupCell != "" && !strings.Contains(strings.ToLower(groupCell), "razem") {
			currentGroup = groupCell
		}

		pluCell := getCell(rows[rowIdx], p.PLUColumnIndex)

		// skip PLU total (razem)
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
