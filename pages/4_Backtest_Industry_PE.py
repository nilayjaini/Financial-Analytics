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
                if isinstance(lvl1, (Timestamp, datetime, date)):
                    new_cols.append(lvl1.strftime("%Y-%m-%d"))
                else:
                    new_cols.append(str(lvl1))
        df.columns = new_cols
    return df

@st.cache_data
def load_data():
    # 1) GICS mapping
    gics = pd.read_csv("data/GICS code.csv", parse_dates=["datadate"])

    # 2) Read & flatten
    xls = pd.ExcelFile("data/Master_data_EPS_Price_PE.xlsx")
    df_eps_wide   = flatten_wide(xls.parse("EPS"))
    df_price_wide = flatten_wide(xls.parse("Price"))
    df_pe_wide    = flatten_wide(xls.parse("PE"))

    # 3) Identify true date cols
    def is_date_str(c):
        dt = pd.to_datetime(c, format="%Y-%m-%d", errors="coerce")
        return not pd.isna(dt)

    date_cols = [c for c in df_eps_wide.columns if is_date_str(c)]
    id_cols   = [c for c in df_eps_wide.columns if c not in date_cols]

    # 4) Melt only date_cols
    df_eps   = df_eps_wide.melt(id_vars=id_cols, value_vars=date_cols,
                                var_name="datadate", value_name="EPS")
    df_price = df_price_wide.melt(id_vars=id_cols, value_vars=date_cols,
                                  var_name="datadate", value_name="ActualPrice")
    df_pe    = df_pe_wide.melt(id_vars=id_cols, value_vars=date_cols,
                               var_name="datadate", value_name="PE")

    # 5) Cast datadate
    for ddf in (df_eps, df_price, df_pe):
        ddf["datadate"] = pd.to_datetime(ddf["datadate"], format="%Y-%m-%d")

    # 6) Merge
    df = (
      df_eps
      .merge(df_price[["Ticker","datadate","ActualPrice"]],
             on=["Ticker","datadate"])
      .merge(df_pe[["Ticker","datadate","PE"]],
             on=["Ticker","datadate"])
    )

    # 7) Join GICS info
    df = df.merge(
      gics.rename(columns={"tic":"Ticker"})[["Ticker","datadate","gsubind","fyear"]],
      on=["Ticker","datadate"], how="left"
    )

    # 8) Prep
    df["year"] = df["fyear"]
    df.rename(columns={"Ticker":"tic"}, inplace=True)
    return df

# Load once
df = load_data()

# ---- UI ----
stock   = st.text_input("Ticker for backtest", "MSFT").upper()
horizon = st.selectbox("Forecast horizon (years)", [1, 2], index=0)

if stock and stock in df["tic"].unique():
    # Compute median P/E by industry-year
    med_pe = (
       df.groupby(["gsubind","year"])["PE"]
         .median()
         .reset_index()
         .rename(columns={"PE":"MedianPE"})
    )

    # This stock’s EPS series
    stock_eps = df[df["tic"]==stock][["year","EPS","gsubind"]]
    bt = stock_eps.merge(med_pe, on=["gsubind","year"], how="left")

    # Predict & pull actual next‐year price
    bt["Predicted"] = bt["MedianPE"] * bt["EPS"]
    price_map      = df.set_index(["tic","year"])["ActualPrice"]
    bt["Actual"]   = bt.apply(
        lambda r: price_map.get((stock, r.year + horizon), np.nan),
        axis=1
    )

    # Error + hit
    bt["PctError"] = (bt["Actual"] - bt["Predicted"]) / bt["Predicted"] * 100
    bt["Hit"]      = bt["PctError"].abs() < 10

    # Display table & summary
    st.subheader(f"🔍 Backtest: {stock} over {horizon}-yr horizon")
    st.dataframe(
      bt[["year","EPS","MedianPE","Predicted","Actual","PctError","Hit"]],
      use_container_width=True
    )
    st.markdown(f"""
      **Mean Abs % Error:** {bt["PctError"].abs().mean():.1f}%  
      **Hit Rate (|error|<10%):** {bt["Hit"].mean()*100:.1f}%  
    """)
    st.line_chart(bt.set_index("year")[["Actual","Predicted"]], height=300)

elif stock:
    st.error(f"No data for ticker '{stock}' in your backtest universe.")
