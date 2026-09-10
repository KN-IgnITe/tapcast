# Share Model Preprocessing and Separate Training Strategies

- Status: proposed
- Date: 2026-09-10
- Deciders: pending team review

## Context and Problem Statement

The previous preprocessor combined XGBoost and Ridge preprocessing in the training package. A serialized preprocessor referenced its Python class in that package, so loading it required the training code to be available.

ModelTrainer also combined model-specific training with backtesting and evaluation. Adding another model required changes to this shared class.

## Decision Drivers

- Reuse the same preprocessing implementation in training and inference.
- Keep model-specific behavior outside the shared training orchestration.
- Preserve chronological validation and prevent fitting preprocessing on evaluation data.

## Considered Options

- Keep preprocessing in training and make inference depend on it.
- Move preprocessing to ml_common and introduce model-specific training strategies.

## Decision Outcome

Choose shared preprocessing in ml_common and model-specific strategies in training.

- FeatureSchema defines required input columns, their order and categorical columns. It does not generate features.
- XGBoostPreprocessor and RidgePreprocessor implement FeaturePreprocessor and return transformed features without the target.
- ModelTrainer extracts target_demand, fits the preprocessor and delegates model fitting and prediction to a strategy.
- XGBoostTrainingStrategy and RidgeTrainingStrategy handle estimator creation and model-specific behavior, including target transformations.
- ModelBacktester runs chronological folds. EarlyStoppingSelector selects the final tree count without using the final test set.
- Bundle metadata records model_kind and the feature schema name and version.

Preprocessing is fitted only on the training partition. Validation, test and inference rows use the fitted preprocessor's transform method. Date remains available for temporal splits and reporting, but is not an estimator input.

## Consequences

### Positive Consequences

- Training and inference can import preprocessing without duplicating it.
- Model-specific fitting and prediction can change without rewriting ModelTrainer.

### Negative Consequences

- Existing bundles referencing the old preprocessor class require regeneration or an explicit migration.
- Shared preprocessing changes must remain compatible with the bundles that use it.

This change does not complete the inference runtime or provide automatic export and loading for every model kind. The production flow still uses XGBoost.

## Pros and Cons of the Options

### Keep Preprocessing in Training

- Pros: fewer immediate changes.
- Cons: inference depends on training code to deserialize the preprocessor.

### Share Preprocessing and Separate Strategies

- Pros: shared preprocessing and clearer ownership of model-specific behavior.
- Cons: bundle compatibility must be handled when moving serialized classes.
