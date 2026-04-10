/*
 query1.sql

Opis: 
    Pobiera dane o sprzedaży z poprzednich dni i uzupełnia je o informacje o pogodzie oraz dacie.
    Dodatkowo wyznacza, jaki był popyt dzień wcześniej i tydzień wcześniej, zachowując ten sam układ dni w kalendarzu



  paramtr kwerendy: bar_id, Identyfikator lokalu, dla którego generujemy dane.


 Zwracane kolumny:
   date(date)                      -  data sprzedazy
   day_of_week(int)                -  numer dnia tygodnia:  1 = poniedzialek, ..., 7 = niedziela
   is_working(bool)                -  czy dany dzien jest roboczy
   is_next_day_working(boolean)    -  czy nastepny dzien jest roboczy
   avg_temp(float)                 -  Srednia temperatura w danym zakresie godzin
   temp_amplitude(float)           -  Amplituda temperatury w danych zakresie godzin,  dodatnia -> tendencja wzrostowa,  ujemna -> spadkowa 
   rain(float)                     -  Suma opadow w danym zakresie godzin
   plu(int)                        -  numer identyfikacyjny artykulu w barze
   category(int)                   -  id kategorii, do ktorej nalezy dany produkt
   ammount(int)                    -  liczba ile razy dany artykul zostal sprzedany w dniu
   yesterday_demand(int)           -  liczba ile razy dany artykul zostal sprzedany dzien wczesniej
   week_ago_demand(int)            -  liczba ile razy dany artykul zostal sprzedany tydzien temu
DIALEKT: PostgreSQL
*/
SELECT
    s.sale_date AS date,
    EXTRACT(ISODOW FROM s.sale_date)::int AS day_of_week,

    d.is_working, 

    d_next.is_working AS is_next_day_working,       --moze byc null

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
    ON d_next.day_date = s.sale_date + INTERVAL '1 day'

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
   AND s_prev.sale_date = s.sale_date - INTERVAL '1 day'

LEFT JOIN sale s_week
    ON s_week.bar_id = s.bar_id
   AND s_week.plu = s.plu
   AND s_week.sale_date = s.sale_date - INTERVAL '7 day'

WHERE s.bar_id = $1

ORDER BY s.sale_date DESC, s.plu;