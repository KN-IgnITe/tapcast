# ML Training Pipeline

## Purpose

The ML training pipeline builds a global demand forecasting model for kitchen demand.

The model predicts demand for a specific PLU and date using product, category, calendar, weather and historical demand features.

## High-Level Flow

The pipeline follows these steps:

1. Load raw demand data from JSON.
2. Clean historical demand.
3. Build leakage-safe training features.
4. Run chronological backtesting.
5. Compare XGBoost objectives.
6. Select the final number of trees using early stopping.
7. Evaluate the selected configuration on the final untouched test set.
8. Train the production model on all available data.
9. Export the production model bundle.

## Important Columns

`demand_raw` is the original observed demand from the source data.

`demand_cleaned` is the cleaned demand used only for historical feature generation.

`target_demand` is the supervised learning target that the model learns to predict.

`prediction` is the model output used during evaluation.

## Cleaning

The history cleaner prepares demand columns and cleaning artifacts.

Winsorization is applied only to historical demand used for features. It should not modify the final target.

Out-of-stock imputation is disabled by default because the current data does not contain a reliable product availability signal.

## Feature Building

The training matrix contains leakage-safe features such as:

- exact demand lags,
- smart lag based on the last similar historical day,
- PLU rolling median,
- category rolling median,
- restaurant total demand lag,
- weather features,
- calendar features,
- historical quality flags.

Historical features must not use data newer than the target date minus the safety buffer.

## Preprocessing and Model Training

Feature building calculates historical demand features. Preprocessing then selects the model's input columns and applies model-specific encoding, imputation or scaling.

FeatureSchema and the XGBoost and Ridge preprocessors live in ml_common. ModelTrainer separates target_demand from the input features and uses a training strategy to fit the estimator. Date and target_demand are not estimator inputs.

Each training run uses a fresh preprocessor fitted only on its training partition. Evaluation rows use transform without fitting again. Future inference must use the fitted preprocessor saved in the model bundle.

## Backtesting

The model is evaluated using chronological walk-forward backtesting.

Random train/test split is not used because it would mix past and future observations and could create data leakage.

Each fold trains on older data and validates on later data.

## Baseline

The Lag-14 baseline is a simple benchmark that predicts demand by copying `demand_lag_14d`.

The XGBoost model should be compared against this baseline to check whether it adds value beyond a naive historical rule.

## XGBoost Model

The production model is a single global XGBoost model trained for all PLUs.

PLU and category are treated as categorical features.

The pipeline compares supported objectives:

- `count:poisson`
- `reg:tweedie`

The best objective is selected using backtest metrics, primarily WAPE.

## Early Stopping and Final Tree Count

Early stopping is used to estimate a reasonable number of boosting rounds.

After the final tree count is selected, the final production model is trained with that fixed number of trees.

## Final Test

The final untouched test set is held out from model selection.

It is used to estimate how the selected configuration performs on unseen future data.

## Production Export

After evaluation, the model is trained again on all available data and exported as a production bundle.

The bundle contains:

- the XGBoost model,
- the fitted preprocessor,
- cleaner artifacts,
- metadata.

## Inference

The current pipeline is focused on training.

Future inference code must build feature rows for future dates without `target_demand`, load the exported artifacts and call the trained model.
