# Demand Forecast Response

## Inference Output

The inference service returns model-related forecast data:

- PLU;
- predicted quantity for each requested day;
- total predicted quantity for the selected date range.

The model may return fractional quantities. Display rounding should be handled after calculating the aggregated prediction.

## Backend Enrichment

Before returning forecasts to the frontend, the backend should enrich each product result with data stored in the database:

- product name;
- unit;
- category name;
- other product presentation details required by the UI.

The backend matches forecast results with product data using the PLU.

## Not Available Yet

The current inference response does not include:

- prediction intervals or uncertainty margins;
- feature contributions;
- event contributions;
- category-level aggregates.

These capabilities require additional implementation in training or inference before they can be exposed to the frontend.
