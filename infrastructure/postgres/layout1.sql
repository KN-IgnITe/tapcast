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

