/*
 query1.sql

Description:
    Retrieves sales data and enriches it with weather and calendar information.
    Additionally calculates demand from the previous day and the previous week,
    preserving the same weekday alignment.

Query parameter:
    bar_id - identifier of the bar for which the data is generated.

Returned columns:
    date(date)                   - sale date
    day_of_week(int)             - weekday number: 1 = Monday, ..., 7 = Sunday
    is_working(bool)             - whether the given day is a working day
    is_next_day_working(bool)    - whether the next day is a working day
    avg_temp(float)              - average temperature during the selected period
    temp_amplitude(float)        - temperature amplitude in the selected period
    rain(float)                  - rainfall sum during the selected period
    plu(int)                     - product identifier in the bar
    category(int)                - product category identifier
    amount(int)                  - number of times the product was sold on that day
    yesterday_demand(int)        - number of times the product was sold one day earlier
    week_ago_demand(int)         - number of times the product was sold one week earlier

DIALECT: PostgreSQL
*/
WITH open_dates AS (
    SELECT
        sale_date AS date
    FROM sale
    WHERE bar_id = $1
    GROUP BY sale_date
    HAVING SUM(amount) > 0
),

product_activity AS (
    SELECT
        a.bar_id,
        a.plu,
        a.category,
        MIN(s.sale_date) AS active_from,
        MAX(s.sale_date) AS active_to
    FROM article a
    JOIN sale s
        ON s.bar_id = a.bar_id
       AND s.plu = a.plu
    WHERE a.bar_id = $1
    GROUP BY
        a.bar_id,
        a.plu,
        a.category
),

product_day_grid AS (
    SELECT
        od.date,
        pa.bar_id,
        pa.plu,
        pa.category
    FROM open_dates od
    JOIN product_activity pa
        ON od.date BETWEEN pa.active_from AND pa.active_to
),

filled_sales AS (
    SELECT
        grid.date,
        grid.bar_id,
        grid.plu,
        grid.category,
        COALESCE(s.amount, 0) AS amount
    FROM product_day_grid grid
    LEFT JOIN sale s
        ON s.sale_date = grid.date
       AND s.bar_id = grid.bar_id
       AND s.plu = grid.plu
)

SELECT
    current_sale.date,

    EXTRACT(
        ISODOW FROM current_sale.date
    )::int AS day_of_week,

    COALESCE(
        calendar_day.is_working,
        EXTRACT(ISODOW FROM current_sale.date)::int BETWEEN 1 AND 5
    ) AS is_working,

    COALESCE(
        next_calendar_day.is_working,
        EXTRACT(
            ISODOW FROM current_sale.date + INTERVAL '1 day'
        )::int BETWEEN 1 AND 5
    ) AS is_next_day_working,

    COALESCE(weather.avg_temp, 0) AS avg_temp,
    COALESCE(weather.temp_amplitude, 0) AS temp_amplitude,
    COALESCE(weather.rain, 0) AS rain,

    current_sale.plu AS PLU,
    current_sale.category,
    current_sale.amount,

    COALESCE(yesterday_sale.amount, 0) AS yesterday_demand,
    COALESCE(week_ago_sale.amount, 0) AS week_ago_demand

FROM filled_sales current_sale

LEFT JOIN filled_sales yesterday_sale
    ON yesterday_sale.bar_id = current_sale.bar_id
   AND yesterday_sale.plu = current_sale.plu
   AND yesterday_sale.date = current_sale.date - INTERVAL '1 day'

LEFT JOIN filled_sales week_ago_sale
    ON week_ago_sale.bar_id = current_sale.bar_id
   AND week_ago_sale.plu = current_sale.plu
   AND week_ago_sale.date = current_sale.date - INTERVAL '7 days'

LEFT JOIN day calendar_day
    ON calendar_day.day_date = current_sale.date

LEFT JOIN day next_calendar_day
    ON next_calendar_day.day_date =
        (current_sale.date + INTERVAL '1 day')::date

LEFT JOIN bar
    ON bar.bar_id = current_sale.bar_id

LEFT JOIN weather
    ON weather.weather_date = current_sale.date
   AND weather.location_id = bar.location_id

ORDER BY
    current_sale.date ASC,
    current_sale.plu ASC;