import os
import pandas as pd

def load_compustat_data(data_path: str = "data/") -> pd.DataFrame:
    """
    Loads and merges Compustat data from CSV files located in data_path.
    Returns a DataFrame containing only rows where eps > 0, PE > 0, and Price > 0.
    """
    # Define file paths
    eps_file = os.path.join(data_path, "Compustat_eps.csv")
    pe_file = os.path.join(data_path, "Compustat_PE.csv")
    mktcap_file = os.path.join(data_path, "Compustat_2024_mkt_value.csv")
    price_file = os.path.join(data_path, "compustat_price.csv")

    # Join keys
    keys = ["fyear", "tic", "conm", "cik", "gsubind", "sic"]

    # Load each dataset and select only necessary columns to avoid overlaps
    eps_df = pd.read_csv(eps_file, usecols=keys + ["eps"])  # EPS
    pe_df = pd.read_csv(pe_file, usecols=keys + ["PE"])     # P/E
    mkt_df = pd.read_csv(mktcap_file, usecols=keys + ["MktCap"])  # Market Cap
    price_df = pd.read_csv(price_file, usecols=keys + ["Price"])  # Price

    # Merge datasets sequentially on keys
    df = eps_df.merge(pe_df, on=keys, how="inner")
    df = df.merge(mkt_df, on=keys, how="inner")
    df = df.merge(price_df, on=keys, how="inner")

    # Filter for positive values
    df = df[(df["eps"] > 0) & (df["PE"] > 0) & (df["Price"] > 0)]

    return df
