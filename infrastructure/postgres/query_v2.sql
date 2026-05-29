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
WITH bounds AS (
    SELECT
        MIN(sale_date) AS min_date,
        MAX(sale_date) AS max_date
    FROM sale
    WHERE bar_id = $1
),
dates AS (
    SELECT gs::date AS date
    FROM bounds,
         generate_series(bounds.min_date, bounds.max_date, interval '1 day') AS gs
),
products AS (
    SELECT
        bar_id,
        plu,
        category
    FROM article
    WHERE bar_id = $1
),
grid AS (
    SELECT
        d.date,
        p.bar_id,
        p.plu,
        p.category
    FROM dates d
    CROSS JOIN products p
),
filled AS (
    SELECT
        g.date,
        g.bar_id,
        g.plu,
        g.category,
        COALESCE(s.amount, 0) AS amount
    FROM grid g
    LEFT JOIN sale s
        ON s.sale_date = g.date
       AND s.bar_id = g.bar_id
       AND s.plu = g.plu
)
SELECT
    f.date,
    EXTRACT(ISODOW FROM f.date)::int AS day_of_week,

    COALESCE(
        d.is_working,
        EXTRACT(ISODOW FROM f.date)::int BETWEEN 1 AND 5
    ) AS is_working,

    COALESCE(
        d_next.is_working,
        EXTRACT(ISODOW FROM f.date + interval '1 day')::int BETWEEN 1 AND 5
    ) AS is_next_day_working,

    COALESCE(w.avg_temp, 0) AS avg_temp,
    COALESCE(w.temp_amplitude, 0) AS temp_amplitude,
    COALESCE(w.rain, 0) AS rain,

    f.plu AS PLU,
    f.category,
    f.amount,

    LAG(f.amount, 1, 0) OVER (
        PARTITION BY f.plu
        ORDER BY f.date
    ) AS yesterday_demand,

    LAG(f.amount, 7, 0) OVER (
        PARTITION BY f.plu
        ORDER BY f.date
    ) AS week_ago_demand

FROM filled f

LEFT JOIN day d
    ON d.day_date = f.date

LEFT JOIN day d_next
    ON d_next.day_date = (f.date + interval '1 day')::date

LEFT JOIN bar b
    ON b.bar_id = f.bar_id

LEFT JOIN weather w
    ON w.weather_date = f.date
   AND w.location_id = b.location_id

ORDER BY f.date ASC, f.plu ASC;