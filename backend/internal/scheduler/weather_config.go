package scheduler

const defaultForecastDays = 7

type weatherConfig struct {
	forecastDays int
	lat          float64
	lon          float64
	locationID   int
}

type WeatherOption func(*weatherConfig)

func WithForecastDays(days int) WeatherOption {
	return func(c *weatherConfig) {
		c.forecastDays = days
	}
}

func WithLocationID(id int) WeatherOption {
	return func(c *weatherConfig) {
		c.locationID = id
	}
}

func WithCoordinates(lat, lon float64) WeatherOption {
	return func(c *weatherConfig) {
		c.lat = lat
		c.lon = lon
	}
}
