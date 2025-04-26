import pandas as pd

def load_compustat_data(data_path: str = "data") -> pd.DataFrame:
def load_compustat_data(data_path="data") -> pd.DataFrame:
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
    # 1) Read each CSV WITHOUT parse_dates for fyear
    df_eps   = pd.read_csv(f"{data_path}/Compustat_eps.csv")
    df_pe    = pd.read_csv(f"{data_path}/Compustat_PE.csv")
    df_mkt   = pd.read_csv(f"{data_path}/Compustat_2024_mkt_value.csv")
    df_price = pd.read_csv(f"{data_path}/compustat_price.csv")

    # 2) Merge stepwise on the six key fields
    # 2) Ensure fyear is an integer (not a date)
    for df in (df_eps, df_pe, df_mkt, df_price):
        df["fyear"] = df["fyear"].astype(int)

    # 3) Merge on the six key columns
on_keys = ["fyear", "tic", "conm", "cik", "gsubind", "sic"]
df = (
df_eps
@@ -24,4 +28,3 @@ def load_compustat_data(data_path: str = "data") -> pd.DataFrame:
)

return df
