import pandas as pd

def load_compustat_data(data_path="data") -> pd.DataFrame:
    """
    Reads and merges the four Compustat CSVs on
    (fyear, tic, conm, cik, gsubind, sic) and returns
    a single DataFrame with columns:
      fyear, tic, conm, cik, gsubind, sic,
      eps, P/E, 2024_mkt_cap, Price
    """
    # 1) Read each CSV WITHOUT parse_dates for fyear
    df_eps   = pd.read_csv(f"{data_path}/Compustat_eps.csv")
    df_pe    = pd.read_csv(f"{data_path}/Compustat_PE.csv")
    df_mkt   = pd.read_csv(f"{data_path}/Compustat_2024_mkt_value.csv")
    df_price = pd.read_csv(f"{data_path}/compustat_price.csv")

    # 2) Ensure fyear is an integer (not a date)
    for df in (df_eps, df_pe, df_mkt, df_price):
        df["fyear"] = df["fyear"].astype(int)

    # 3) Merge on the six key columns
    on_keys = ["fyear", "tic", "conm", "cik", "gsubind", "sic"]
    df = (
        df_eps
        .merge(df_pe,    on=on_keys, how="inner")
        .merge(df_mkt,   on=on_keys, how="inner")
        .merge(df_price, on=on_keys, how="inner")
    )

    return df
