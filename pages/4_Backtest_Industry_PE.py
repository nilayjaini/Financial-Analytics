import streamlit as st
import pandas as pd
import plotly.express as px

from helpers.compustat_loader import load_compustat_data
from helpers.peer_lookup        import get_peers

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

# 1) Load and cache your Compustat master table
df = load_compustat_data()

# 2) User inputs
ticker  = st.text_input("Ticker for backtest", "MSFT").upper()
horizon = st.selectbox("Forecast horizon (years)", [1,2,3,4,5], index=0)

# 3) Find this ticker’s sub-industry code (assuming you have that column):
try:
    subind = df.loc[df["tic"] == ticker, "gsubind"].iloc[0]
    st.write("🔎 Sub-Industry Code:", subind)
except IndexError:
    st.error("Ticker not found in Compustat master file.")
    st.stop()

# 4) Filter to this sub-industry and years 2015–2023 for backtest
mask = (
    (df["gsubind"] == subind) &
    (df["fyear"] >= 2015) &
    (df["fyear"] <= 2023)
)
df_sb = df[mask].copy()

if df_sb.empty:
    st.warning("No data for that sub-industry / period.")
    st.stop()

# 5) For each year calculate the “predicted” price for next year:
#    predicted = median_pe(current_year) × eps(current_year)
results = []
for year in sorted(df_sb["fyear"].unique()):
    df_year = df_sb[df_sb["fyear"] == year]
    med_pe = df_year["PE"].median()
    eps    = df_year.loc[df_year["tic"] == ticker, "EPS"].iat[0]
    pred   = med_pe * eps

    # actual next-year price (from compustat_price)
    actual_row = df_sb[(df_sb["tic"] == ticker) & (df_sb["fyear"] == year+horizon)]
    actual_price = actual_row["Price"].iat[0] if not actual_row.empty else None

    # did we “hit” within ±10%?
    hit = (
        actual_price is not None
        and abs(pred - actual_price) / actual_price <= 0.10
    )

    results.append({
        "year":           year,
        "eps":            eps,
        "median_pe":      med_pe,
        "predicted":      pred,
        "target_year":    year+horizon,
        "actual":         actual_price,
        "hit":            hit
    })

df_res = pd.DataFrame(results)

# 6) Show your backtest table + plot
st.subheader("Backtest Results")
st.dataframe(df_res, use_container_width=True)

fig = px.scatter(
    df_res, x="predicted", y="actual", color="hit",
    title=f"{ticker} Predicted vs Actual ({horizon}-Yr Horizon)"
)
fig.add_shape(
    type="line", line=dict(dash="dash"),
    x0=df_res["predicted"].min(), x1=df_res["predicted"].max(),
    y0=df_res["predicted"].min(), y1=df_res["predicted"].max()
)
st.plotly_chart(fig, use_container_width=True)

# 7) Hit‐rate summary
hit_rate = df_res["hit"].mean() * 100
st.metric(f"Hit Rate (±10%) over {len(df_res)} years", f"{hit_rate:.1f}%")
