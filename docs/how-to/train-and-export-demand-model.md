# Train and Export Demand Model

## Purpose

This guide explains how to run the demand model training pipeline and export the production-ready model artifacts.

## Prerequisites

Make sure the training JSON file exists at:

```text
training/data/raw/sql_export.json
```

The JSON file should be generated from the current SQL export process and must match the training data contract.

## Run Training

From the `training` directory, run:

```bash
poetry run python -m training.main
```

If you are using the local virtual environment directly on Windows, run:

```bash
.\.venv\Scripts\python.exe src/training/main.py
```

## What the Script Does

The training script performs the full offline training flow:

1. Loads raw demand data.
2. Splits data chronologically into train/validation and final test parts.
3. Compares supported XGBoost objectives.
4. Selects the best objective using backtest metrics.
5. Runs walk-forward backtesting.
6. Compares XGBoost against the Lag-14 baseline.
7. Reports global, per-category and per-PLU metrics.
8. Evaluates 1-day, 7-day, 14-day prediction windows.
9. Runs the final untouched test.
10. Trains the production model on all available data.
11. Exports production artifacts.

## Exported Artifacts

The production bundle is saved to:

```text
training/artifacts/production
```

Expected files:

```text
xgb_model.json
preprocessor.joblib
cleaner_artifacts.json
metadata.json
```

## Artifact Meaning

`xgb_model.json` contains the trained XGBoost model.

`preprocessor.joblib` contains the fitted model preprocessor.

`cleaner_artifacts.json` contains historical cleaning artifacts, including winsorization thresholds.

`metadata.json` contains model configuration, selected objective, number of trees and cleaning configuration.

## Notes

The final untouched test is used only for evaluation. After that, the production model is trained on all available data using the selected configuration.

The exported bundle is intended for the future inference pipeline.
