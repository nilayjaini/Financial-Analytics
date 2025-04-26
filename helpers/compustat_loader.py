import pandas as pd

def load_compustat_data(data_path: str = "data") -> pd.DataFrame:
    """
    Reads and merges the four Compustat CSVs on
    (fyear, tic, conm, cik, gsubind, sic) and returns
    a single DataFrame with columns:
      fyear, tic, conm, cik, gsubind, sic,
      eps, P/E, 2024_mkt_cap, Price
    """
    # 1) Read each CSV
    df_eps   = pd.read_csv(f"{data_path}/Compustat_eps.csv",   parse_dates=["fyear"])
    df_pe    = pd.read_csv(f"{data_path}/Compustat_PE.csv",    parse_dates=["fyear"])
    df_mkt   = pd.read_csv(f"{data_path}/Compustat_2024_mkt_value.csv", parse_dates=["fyear"])
    df_price = pd.read_csv(f"{data_path}/compustat_price.csv", parse_dates=["fyear"])

    # 2) Merge stepwise on the six key fields
    on_keys = ["fyear", "tic", "conm", "cik", "gsubind", "sic"]
    df = (
        df_eps
        .merge(df_pe,    on=on_keys, how="inner")
        .merge(df_mkt,   on=on_keys, how="inner")
        .merge(df_price, on=on_keys, how="inner")
    )

    return df

