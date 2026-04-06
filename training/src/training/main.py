# print("Python Training: Worker initialized.")
from pathlib import Path

from data.data_loader import DemandDataLoader
from data.data_splitter import DataSplitter
from features.preprocessor import DataProcessor

def main():
    data_path = Path(__file__).parents[2] / "data" / "raw" / "mocked_data.json"
    
    loader = DemandDataLoader(data_path)
    splitter = DataSplitter(test_size=0.2) # 80% train, 20% test
    preprocessor = DataProcessor()

    print("Starting data processing pipeline...\n")

    # Load and flatten data
    print("1. Data loading and flattening...")
    df_flat = loader.load_and_process()
    print(f"   -> Loaded all rows: {len(df_flat)}")

    # chronological split into train and test sets
    print("2. Splitting data into train and test sets(chronologically)...")    
    train_df, test_df = splitter.split(df_flat)
    print(f" Split completed. Train rows: {len(train_df)}, Test rows: {len(test_df)}")

    # Preprocessing 
    train_processed = preprocessor.fit_transform(train_df)
    test_processed = preprocessor.transform(test_df)
    print("3. Data preprocessing completed.")

    # Validation: Check for date continuity and no overlap
    print("\n--- Summary of sets---")
    print("TRAINING SET:")
    print(f" - Rows: {len(train_df)}")
    print(f" - From: {train_df['date'].min().date()} to: {train_df['date'].max().date()}")
    
    print("\nTEST SET:")
    print(f" - Rows: {len(test_df)}")
    print(f" - From: {test_df['date'].min().date()} to: {test_df['date'].max().date()}")

    print("\n---------- Processed Feature Matrix(First 5 rows) ----------")
    print(f"New column count: {len(train_processed.columns)}")
    print(train_processed.head().to_string())

if __name__ == "__main__":
    main()