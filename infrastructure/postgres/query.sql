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
SELECT
    s.sale_date AS date,
    EXTRACT(ISODOW FROM s.sale_date)::int AS day_of_week,

    d.is_working, 

    d_next.is_working AS is_next_day_working,     

    w.avg_temp,
    w.temp_amplitude,
    w.rain,

    s.plu AS PLU,
    a.category,
    s.amount,

    s_prev.amount AS yesterday_demand,
    s_week.amount AS week_ago_demand

FROM sale s

JOIN day d
    ON d.day_date = s.sale_date

LEFT JOIN day d_next
    ON d_next.day_date = (s.sale_date + INTERVAL '1 day')::date

JOIN article a
    ON a.bar_id = s.bar_id
   AND a.plu = s.plu

JOIN bar b
    ON b.bar_id = s.bar_id

--
LEFT JOIN weather w
    ON w.weather_date = s.sale_date
   AND w.location_id = b.location_id

--
LEFT JOIN sale s_prev
    ON s_prev.bar_id = s.bar_id
   AND s_prev.plu = s.plu
   AND s_prev.sale_date = (s.sale_date - INTERVAL '1 day')::date

LEFT JOIN sale s_week
    ON s_week.bar_id = s.bar_id
   AND s_week.plu = s.plu
   AND s_week.sale_date = (s.sale_date - INTERVAL '7 day')::date

WHERE s.bar_id = $1

ORDER BY s.sale_date DESC, s.plu;