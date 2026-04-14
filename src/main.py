import pandas as pd
from sklearn.impute import SimpleImputer

def load_data(file_path):
    """Load dataset"""
    try:
        df = pd.read_csv(file_path)
        print("✅ Data loaded successfully\n")
        return df
    except Exception as e:
        print("❌ Error loading data:", e)
        return None


def check_data_quality(df):
    """Check missing values and basic info"""
    print("🔍 Data Info:\n")
    print(df.info())
    
    print("\n📊 Missing Values:\n")
    print(df.isnull().sum())
    print("\n")


def impute_data(df):
    """Handle missing values using SimpleImputer"""
    df_copy = df.copy()

    # Select numeric columns
    numeric_cols = df_copy.select_dtypes(include=['float64', 'int64']).columns

    # Apply mean imputation
    imputer = SimpleImputer(strategy='mean')
    df_copy[numeric_cols] = imputer.fit_transform(df_copy[numeric_cols])

    print("✅ Missing values handled using Mean Imputation\n")
    return df_copy


def save_clean_data(df, output_path):
    """Save cleaned dataset"""
    df.to_csv(output_path, index=False)
    print(f"💾 Cleaned data saved to {output_path}\n")


def main():
    # File paths
    input_file = 'data/sample.csv'
    output_file = 'data/cleaned_sample.csv'

    # Load data
    df = load_data(input_file)

    if df is not None:
        print("🔹 Original Data:\n", df, "\n")

        # Check quality
        check_data_quality(df)

        # Impute missing values
        cleaned_df = impute_data(df)

        print("🔹 Cleaned Data:\n", cleaned_df)

        # Save cleaned data
        save_clean_data(cleaned_df, output_file)


if __name__ == "__main__":
    main()
