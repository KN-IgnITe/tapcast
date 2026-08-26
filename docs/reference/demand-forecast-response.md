# Demand Forecast Response

## Product Selection

The backend must provide one or more PLU identifiers in the forecast request.

The inference service calculates predictions only for the requested PLUs. An empty PLU list is invalid and does not mean that all products should be forecast.

When a user selects a category, the backend is responsible for resolving that category to its PLUs before requesting a forecast.

## Inference Output

For every requested PLU, the inference service returns:

- predicted quantity for each requested day;
- total predicted quantity for the selected date range.

The model may return fractional quantities. Display rounding should be applied after calculating the aggregated prediction.

## Backend Enrichment

Before returning forecasts to the frontend, the backend enriches each result with data stored in the database:

- product name;
- unit;
- category name;
- other presentation details required by the UI.

The backend matches forecast results with product data using the PLU.

## Not Available Yet

The current inference response does not include:

- prediction intervals or uncertainty margins;
- feature contributions;
- event contributions;
- category-level aggregates.
