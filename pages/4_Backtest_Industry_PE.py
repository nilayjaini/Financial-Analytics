import streamlit as st
import pandas as pd
import plotly.express as px
from helpers.compustat_loader import load_compustat_data

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

# Cache the merged DataFrame
@st.cache_data
def get_df():
    return load_compustat_data(data_path="data")

df = get_df()

# --- User Inputs ---
ticker  = st.text_input("Ticker for backtest", "MSFT").upper()
horizon = st.selectbox("Forecast horizon (years)", [1, 2, 3, 5], index=0)

if ticker:
    # Filter to this ticker
    tick_df = df[df["tic"] == ticker]
    if tick_df.empty:
        st.error(f"No data for ticker '{ticker}'.")
        st.stop()

    # Identify sub‐industry code
    subind = tick_df["gsubind"].iloc[0]
    st.write(f"**Sub-Industry Code:** {subind}")

    # Compute median P/E by (subind, fyear)
    med_pe = (
        df[df["gsubind"] == subind]
        .groupby("fyear")["P/E"]
        .median()
        .reset_index(name="median_pe")
    )

    # Build the backtest table
    bt = (
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
    st.plotly_chart(fig, use_container_width=True)

    # Show detailed backtest table
    st.dataframe(
        bt[["fyear","eps","median_pe","predicted","target_year","actual","error_pct","hit"]],
        use_container_width=True
    )
