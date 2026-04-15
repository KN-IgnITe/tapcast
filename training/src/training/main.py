from pathlib import Path

from training.data.data_loader import DemandDataLoader
from training.data.data_splitter import DataSplitter
from training.models.model_trainer import ModelTrainer, ModelType


def main() -> None:
    data_path = Path(__file__).parents[2] / "data" / "raw" / "mocked_data.json"

    loader = DemandDataLoader(data_path)
    splitter = DataSplitter(test_size=0.15, n_splits=5)  # 85% train, 15% test

    # 1. Load data and process
    print("==========Start of pipeline============")
    df_flat = loader.load_and_process()
    print(f"Loaded and processed: {len(df_flat)} rows")

    # 2. split of data
    train_val_df, test_df = splitter.get_final_test_split(df_flat)
    print(f"Train+Val set: {len(train_val_df)} rows, Test set: {len(test_df)} rows")

    # 3. Train and evaluate model

    trainer_log_lin = ModelTrainer(model_type=ModelType.LOG_LIN)
    mae_log_lin = trainer_log_lin.run_walk_forward_training(train_val_df, splitter)

    trainer_xgboost = ModelTrainer(model_type=ModelType.XGBOOST)
    mae_xgboost = trainer_xgboost.run_walk_forward_training(train_val_df, splitter)

    print(f"Log-linear model MAE: {mae_log_lin:.4f}")
    print(f"XGBoost model MAE: {mae_xgboost:.4f}")

    # 4. Final evaluation on test set
    print("\n==========Final evaluation on test set============")

    final_mae_log_lin = trainer_log_lin.evaluate_on_test(train_val_df, test_df)
    final_mae_xgboost = trainer_xgboost.evaluate_on_test(train_val_df, test_df)

    print(f"Log-Linear model final MAE on test set: {final_mae_log_lin:.4f}")
    print(f"XGBoost model final MAE on test set: {final_mae_xgboost:.4f}")


if __name__ == "__main__":
    main()
