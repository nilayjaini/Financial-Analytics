import streamlit as st
import pandas as pd
import plotly.express as px

from helpers.compustat_loader import load_compustat_data
from helpers.peer_lookup        import get_peers

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

# 1) Load and cache your Compustat master table
# 1) Load master table
df = load_compustat_data()

# 2) User inputs
# 2) Inputs
ticker  = st.text_input("Ticker for backtest", "MSFT").upper()
horizon = st.selectbox("Forecast horizon (years)", [1,2,3,4,5], index=0)

# 3) Find this ticker’s sub-industry code (assuming you have that column):
try:
    subind = df.loc[df["tic"] == ticker, "gsubind"].iloc[0]
    st.write("🔎 Sub-Industry Code:", subind)
except IndexError:
    st.error("Ticker not found in Compustat master file.")
# 3) Look up this ticker’s sub-industry
matches = df[df.tic == ticker]
if matches.empty:
    st.error(f"{ticker} not found in Compustat data.")
st.stop()

# 4) Filter to this sub-industry and years 2015–2023 for backtest
subind = matches.gsubind.iat[0]
st.write("🔎 Sub-Industry Code:", subind)

# 4) Filter to years 2015–2023 in the same sub-industry
mask = (
    (df["gsubind"] == subind) &
    (df["fyear"] >= 2015) &
    (df["fyear"] <= 2023)
    (df.gsubind == subind) &
    (df.fyear    >= 2015) &
    (df.fyear    <= 2023)
)
df_sb = df[mask].copy()

if df_sb.empty:
    st.warning("No data for that sub-industry / period.")
    st.warning("No data for that sub-industry in 2015–2023.")
st.stop()

# 5) For each year calculate the “predicted” price for next year:
#    predicted = median_pe(current_year) × eps(current_year)
results = []
for year in sorted(df_sb["fyear"].unique()):
    df_year = df_sb[df_sb["fyear"] == year]
    med_pe = df_year["PE"].median()
    eps    = df_year.loc[df_year["tic"] == ticker, "EPS"].iat[0]
    pred   = med_pe * eps
# 5) Perform the backtest
records = []
for yr in sorted(df_sb.fyear.unique()):
    this_yr = df_sb[df_sb.fyear == yr]
    med_pe  = this_yr.PE.median()
    eps_val = this_yr.loc[this_yr.tic == ticker, "EPS"].iat[0]
    pred    = med_pe * eps_val

    # actual next-year price (from compustat_price)
    actual_row = df_sb[(df_sb["tic"] == ticker) & (df_sb["fyear"] == year+horizon)]
    actual_price = actual_row["Price"].iat[0] if not actual_row.empty else None
    # actual next-year price from our merged Price column
    next_row = df_sb[
        (df_sb.tic  == ticker) &
        (df_sb.fyear == yr + horizon)
    ]
    actual_price = next_row.Price.iat[0] if not next_row.empty else None

    # did we “hit” within ±10%?
hit = (
actual_price is not None
        and abs(pred - actual_price) / actual_price <= 0.10
        and abs(pred - actual_price)/actual_price <= 0.10
)

    results.append({
        "year":           year,
        "eps":            eps,
        "median_pe":      med_pe,
        "predicted":      pred,
        "target_year":    year+horizon,
        "actual":         actual_price,
        "hit":            hit
    records.append({
        "fyear":      yr,
        "EPS":        eps_val,
        "median_PE":  med_pe,
        "predicted":  pred,
        "target_fyr": yr + horizon,
        "actual":     actual_price,
        "hit":        hit
})

df_res = pd.DataFrame(results)
df_res = pd.DataFrame(records)

# 6) Show your backtest table + plot
# 6) Show table + scatter
st.subheader("Backtest Results")
st.dataframe(df_res, use_container_width=True)

fig = px.scatter(
    df_res, x="predicted", y="actual", color="hit",
    title=f"{ticker} Predicted vs Actual ({horizon}-Yr Horizon)"
    df_res,
    x="predicted", y="actual",
    color="hit",
    title=f"{ticker} Predicted vs. Actual ({horizon}-Yr Horizon)",
    labels={"predicted":"Predicted Price","actual":"Actual Price"}
)
# add 45° line
minv, maxv = df_res[["predicted","actual"]].min().min(), df_res[["predicted","actual"]].max().max()
fig.add_shape(
type="line", line=dict(dash="dash"),
    x0=df_res["predicted"].min(), x1=df_res["predicted"].max(),
    y0=df_res["predicted"].min(), y1=df_res["predicted"].max()
    x0=minv, x1=maxv, y0=minv, y1=maxv
)
st.plotly_chart(fig, use_container_width=True)

# 7) Hit‐rate summary
hit_rate = df_res["hit"].mean() * 100
st.metric(f"Hit Rate (±10%) over {len(df_res)} years", f"{hit_rate:.1f}%")
# 7) Hit rate
rate = df_res.hit.mean() * 100
st.metric(f"Hit Rate (±10%) over {len(df_res)} years", f"{rate:.1f}%")
