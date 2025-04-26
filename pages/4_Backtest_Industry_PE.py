import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from pandas import Timestamp

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

def flatten_wide(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for lvl0, lvl1 in df.columns:
            if pd.isna(lvl1):
                new_cols.append(lvl0)
            else:
                # convert timestamps or date‐like objects into YYYY-MM-DD
                if isinstance(lvl1, (Timestamp, datetime, date)):
                    new_cols.append(lvl1.strftime("%Y-%m-%d"))
                else:
                    new_cols.append(str(lvl1))
        df.columns = new_cols
    return df

@st.cache_data
def load_data():
    # 1) Read GICS mapping
    gics = pd.read_csv("data/GICS code.csv", parse_dates=["datadate"])

    # 2) Load the three sheets & flatten any MultiIndex headers
    xls           = pd.ExcelFile("data/Master_data_EPS_Price_PE.xlsx")
    df_eps_wide   = flatten_wide(xls.parse("EPS"))
    df_price_wide = flatten_wide(xls.parse("Price"))
    df_pe_wide    = flatten_wide(xls.parse("PE"))

    # 3) Discover true date columns (YYYY-MM-DD strings) by parsing
    def is_date_str(col):
        # try to parse with exact YYYY-MM-DD
        return pd.to_datetime(col, format="%Y-%m-%d", errors="coerce").notna()

    date_cols = [c for c in df_eps_wide.columns if is_date_str(c)]
    id_cols   = [c for c in df_eps_wide.columns if c not in date_cols]

    # 4) Melt only the date columns
    df_eps   = df_eps_wide.melt(id_vars=id_cols,   value_vars=date_cols,
                                var_name="datadate", value_name="EPS")
    df_price = df_price_wide.melt(id_vars=id_cols, value_vars=date_cols,
                                  var_name="datadate", value_name="ActualPrice")
    df_pe    = df_pe_wide.melt(id_vars=id_cols,    value_vars=date_cols,
                               var_name="datadate", value_name="PE")

    # 5) Cast datadate into real datetime
    for ddf in (df_eps, df_price, df_pe):
        ddf["datadate"] = pd.to_datetime(ddf["datadate"], format="%Y-%m-%d")

    # 6) Merge all three on Ticker+date
    df = (
      df_eps
      .merge(df_price[["Ticker","datadate","ActualPrice"]],
             on=["Ticker","datadate"])
      .merge(df_pe[["Ticker","datadate","PE"]],
             on=["Ticker","datadate"])
    )

    # 7) Bring in GICS industry & fiscal year
    df = df.merge(
        gics.rename(columns={"tic":"Ticker"})[["Ticker","datadate","gsubind","fyear"]],
        on=["Ticker","datadate"],
        how="left"
    )

    # 8) Prep for backtest
    df["year"] = df["fyear"]
    df.rename(columns={"Ticker":"tic"}, inplace=True)
    return df

# --- the rest of your backtest code remains the same ---
df = load_data()
# UI, grouping, predictions, plotting ...
