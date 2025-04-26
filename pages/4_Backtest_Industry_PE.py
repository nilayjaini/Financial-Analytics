import streamlit as st
import pandas as pd
import plotly.express as px
from helpers.compustat_loader import load_compustat_data

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

# 1) Load & cache the merged Compustat DataFrame
# Cache the merged DataFrame
@st.cache_data
def get_full_df():
def get_df():
return load_compustat_data(data_path="data")

df = get_full_df()
df = get_df()

# 2) UI Inputs
# --- User Inputs ---
ticker  = st.text_input("Ticker for backtest", "MSFT").upper()
horizon = st.selectbox("Forecast horizon (years)", [1,2,3,5], index=0)
horizon = st.selectbox("Forecast horizon (years)", [1, 2, 3, 5], index=0)

if ticker:
    # 3) Filter to this ticker and sub‐industry
    # Filter to this ticker
tick_df = df[df["tic"] == ticker]
if tick_df.empty:
        st.error(f"No data for {ticker}.")
        st.error(f"No data for ticker '{ticker}'.")
st.stop()

    subind   = tick_df["gsubind"].iloc[0]
    # 4) Compute median P/E by sub‐industry & fiscal year
    # Identify sub‐industry code
    subind = tick_df["gsubind"].iloc[0]
    st.write(f"**Sub-Industry Code:** {subind}")

    # Compute median P/E by (subind, fyear)
med_pe = (
      df[df["gsubind"] == subind]
       .groupby("fyear")["P/E"]
       .median()
       .reset_index(name="median_pe")
        df[df["gsubind"] == subind]
        .groupby("fyear")["P/E"]
        .median()
        .reset_index(name="median_pe")
)

    # 5) Build backtest table
    # Build the backtest table
bt = (
      tick_df[["fyear","eps","Price"]]
      .merge(med_pe, on="fyear", how="left")
      .assign(
         predicted = lambda d: d["eps"] * d["median_pe"],
         target_year = lambda d: d["fyear"] + horizon
      )
        tick_df[["fyear", "eps", "Price"]]
        .merge(med_pe, on="fyear", how="left")
        .assign(
            predicted=lambda d: d["eps"] * d["median_pe"],
            target_year=lambda d: d["fyear"] + horizon
        )
    )

    # Map the actual price in the target year
    price_map = df.set_index(["tic", "fyear"])["Price"]
    bt["actual"] = bt.apply(
        lambda r: price_map.get((ticker, int(r.target_year)), pd.NA),
        axis=1
    )

    # Compute error & hit flag
    bt["error_pct"] = 100 * (bt["actual"] - bt["predicted"]) / bt["predicted"]
    bt["hit"]       = bt["error_pct"].abs() <= 10  # ±10%

    # Display summary metrics
    hit_rate = bt["hit"].mean() * 100
    st.metric("Hit Rate (±10% error)", f"{hit_rate:.1f}%")

    # Plot Predicted vs Actual
    fig = px.scatter(
        bt, x="predicted", y="actual", color="hit",
        labels={"predicted":"Predicted Price", "actual":"Actual Price"},
        title=f"{ticker} Predicted vs Actual ({horizon}-Yr Horizon)"
    )
    fig.add_shape(
        type="line", x0=0, x1=bt["predicted"].max(),
        y0=0, y1=bt["predicted"].max(),
        line=dict(dash="dash", color="gray")
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
    # Show detailed backtest table
    st.dataframe(
        bt[["fyear","eps","median_pe","predicted","target_year","actual","error_pct","hit"]],
        use_container_width=True
    )
