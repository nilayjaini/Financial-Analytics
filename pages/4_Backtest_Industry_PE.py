import streamlit as st
import pandas as pd
import plotly.express as px
from helpers.compustat_loader import load_compustat_data

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

# 1) Load & cache the merged Compustat DataFrame
@st.cache_data
def get_full_df():
    return load_compustat_data(data_path="data")

df = get_full_df()

# 2) UI Inputs
ticker  = st.text_input("Ticker for backtest", "MSFT").upper()
horizon = st.selectbox("Forecast horizon (years)", [1,2,3,5], index=0)

if ticker:
    # 3) Filter to this ticker and sub‐industry
    tick_df = df[df["tic"] == ticker]
    if tick_df.empty:
        st.error(f"No data for {ticker}.")
        st.stop()

    subind   = tick_df["gsubind"].iloc[0]
    # 4) Compute median P/E by sub‐industry & fiscal year
    med_pe = (
      df[df["gsubind"] == subind]
       .groupby("fyear")["P/E"]
       .median()
       .reset_index(name="median_pe")
    )

    # 5) Build backtest table
    bt = (
      tick_df[["fyear","eps","Price"]]
      .merge(med_pe, on="fyear", how="left")
      .assign(
         predicted = lambda d: d["eps"] * d["median_pe"],
         target_year = lambda d: d["fyear"] + horizon
      )
    )
    # Map actual price in target year
    price_map = df.set_index(["tic","fyear"])["Price"]
    bt["actual"] = bt.apply(lambda r: price_map.get((ticker, r.target_year), pd.NA), axis=1)
    bt["error_pct"] = (bt["actual"] - bt["predicted"]) / bt["predicted"] * 100
    bt["hit"] = bt["error_pct"].abs() <= 10

    # 6) Display summary & chart
    st.metric("Hit Rate (±10%)", f"{100*bt['hit'].mean():.1f}%")
    fig = px.scatter(bt, x="predicted", y="actual", color="hit",
                     labels={"predicted":"Predicted","actual":"Actual"})
    fig.add_shape(dict(type="line", x0=0, x1=bt["predicted"].max(),
                       y0=0, y1=bt["predicted"].max(), line=dict(dash="dash")))
    st.plotly_chart(fig, use_container_width=True)

    # 7) Full table
    st.dataframe(bt[["fyear","eps","median_pe","predicted",
                     "target_year","actual","error_pct","hit"]])
