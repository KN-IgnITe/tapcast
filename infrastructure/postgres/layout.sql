CREATE Table IF NOT EXISTS day(
    day_date DATE Primary Key,
    is_working BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS location (
    location_id SERIAL Primary Key,
    name TEXT NOT NULL
);

CREATE Table IF NOT EXISTS bar (
    bar_id SERIAL Primary KEY,
    location_id INT NOT NULL,
    name TEXT,
    Foreign KEY(location_id)
        REFERENCES location(location_id)
);

CREATE Table IF NOT EXISTS weather(
    weather_date DATE ,
    location_id INT,
    avg_temp FLOAT  NOT NULL,
    temp_amplitude FLOAT NOT NULL,
    rain FLOAT NOT NULL DEFAULT 0  CHECK (rain >= 0),

    Primary Key(weather_date, location_id),
    Foreign KEY(weather_date)
        REFERENCES day(day_date),
    Foreign KEY(location_id)
        REFERENCES location(location_id)
);

CREATE TABLE IF NOT EXISTS article(
    bar_id INT,
    plu INT,
    category INT NOT NULL,

    Primary Key(bar_id, plu),
    Foreign KEY(bar_id)
        REFERENCES bar(bar_id)
);

CREATE Table IF NOT EXISTS sale(
    sale_date DATE,
    bar_id INT,
    plu INT,
    amount INT  NOT NULL CHECK (amount >= 0),

    Primary Key(sale_date, bar_id, plu),

    Foreign KEY(sale_date)
        REFERENCES day(day_date),
    Foreign KEY(bar_id, plu)
        REFERENCES article(bar_id, plu)
);



/*

-- 2. Przykładowe dane (Seeding)
INSERT INTO day (day_date, is_working) VALUES 
('2026-04-01', true), ('2026-04-02', true), ('2026-04-03', true), 
('2026-04-08', true), ('2026-04-09', true), ('2026-04-10', true);

INSERT INTO location (location_id, name) VALUES (1, 'Warszawa Centralna');
INSERT INTO bar (bar_id, location_id, name) VALUES (1, 1, 'Bar pod Złotym Łukiem');

INSERT INTO weather (weather_date, location_id, avg_temp, temp_amplitude, rain) 
VALUES ('2026-04-10', 1, 15.5, 5.0, 0.2);

INSERT INTO article (bar_id, plu, category) VALUES (1, 101, 5), (1, 102, 6);

INSERT INTO sale (sale_date, bar_id, plu, amount) VALUES 
('2026-04-03', 1, 101, 50), -- Sprzedaż tydzień temu
('2026-04-09', 1, 101, 60), -- Sprzedaż wczoraj
('2026-04-10', 1, 101, 100), -- Sprzedaż dzisiaj

('2026-04-03', 1, 102, 60), -- Sprzedaż tydzień temu
('2026-04-09', 1, 102, 70), -- Sprzedaż wczoraj
('2026-04-10', 1, 102, 110); -- Sprzedaż dzisiaj
*/