# ML Demand Modeling Decisions

## Status

Proposed

## Context

The demand forecasting pipeline must predict kitchen demand without using future information. The model should support many PLUs at once and produce artifacts that can later be used by the inference service.

## Decisions

### Train one global model

We train one global model for all PLUs instead of one model per product.

This allows the model to learn shared patterns between products, categories, weather and calendar features.

### Use `target_demand` as the supervised target

The model learns to predict `target_demand`.

`demand_cleaned` is used only for historical feature generation and must not be used as the final target.

### Keep historical features leakage-safe

Historical features must use only data available at least 14 days before the target date.

This prevents the model from learning from future demand.

### Use chronological backtesting

Random train/test split is not used.

The model is evaluated with walk-forward chronological validation because production inference will also predict future dates from past data.

### Compare XGBoost objectives

The pipeline compares:

- `count:poisson`
- `reg:tweedie`

The selected objective is based mainly on WAPE from backtesting.

### Use Lag-14 as baseline

The Lag-14 baseline predicts demand by copying `demand_lag_14d`.

It is used as a simple benchmark to check whether the XGBoost model adds value.

### Disable OOS imputation by default

Out-of-stock imputation is disabled because the current dataset does not contain a reliable product availability signal.

Without that signal, zero demand may mean either no sales or unavailable product, and automatic imputation could introduce false demand.

### Export a production model bundle

The final training step exports:

- XGBoost model,
- fitted preprocessor,
- cleaner artifacts,
- metadata.

This keeps training and future inference consistent.

## Consequences

The production model can be exported and loaded later by inference code.

A separate inference feature builder is still required, because future prediction rows will not contain `target_demand`.
