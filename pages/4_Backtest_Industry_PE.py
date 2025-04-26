# pages/4_Backtest_Industry_PE.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

# 1) Load & cache your Excel sheets
@st.cache_data
def load_data():
    xls = pd.ExcelFile("data/Master_data_EPS_Price_PE.xlsx")
    df_eps = xls.parse("EPS")
    df_pe  = xls.parse("PE")
    df_price = xls.parse("Price")
    return df_eps, df_pe, df_price

# 2) Helper to unpivot a wide → long
def melt_yearly(df_wide, value_name):
    # 1) Try to convert any column name that *looks* like a date into a Timestamp
    rename_map = {}
    for col in df_wide.columns:
        try:
            # if this succeeds, col really is a date
            dt = pd.to_datetime(col, infer_datetime_format=True)
            rename_map[col] = dt
        except (ValueError, TypeError):
            # cannot parse → leave as is
            pass

    df_wide = df_wide.rename(columns=rename_map)

    # 2) Now identify which columns *are* real Timestamps
    date_cols = [c for c in df_wide.columns if isinstance(c, pd.Timestamp)]
    id_vars   = [c for c in df_wide.columns if c not in date_cols]

    # 3) Melt into long form
    df_long = df_wide.melt(
        id_vars     = id_vars,
        value_vars  = date_cols,
        var_name    = "datadate",
        value_name  = value_name
    )

    # 4) Safely extract year
    df_long["year"] = df_long["datadate"].dt.year
    return df_long

    # EPS & Price time‐series for our ticker
    df_eps_t   = df_eps[df_eps["Ticker"] == ticker][["year","EPS"]]
    df_price_t = df_price[df_price["Ticker"] == ticker][["year","Price"]]

    # 5) assemble backtest hits
    records = []
    for _, row in df_eps_t.iterrows():
        base_year = int(row["year"])
        eps_val   = row["EPS"]
        target_year = base_year + horizon

        # get that year's median PE
        pe_row = df_pe_ind[df_pe_ind["year"] == base_year]
        if pe_row.empty:
            continue
        pe_med = pe_row["Median_PE"].iloc[0]

        # predicted vs actual
        pred_price = eps_val * pe_med
        actual_row = df_price_t[df_price_t["year"] == target_year]
        if actual_row.empty:
            continue
        actual_price = actual_row["Price"].iloc[0]

        err_pct = (pred_price - actual_price) / actual_price * 100
        hit     = abs(err_pct) <= 10  # ±10% tolerance

        records.append({
            "Base Year":       base_year,
            "Target Year":     target_year,
            "EPS":              eps_val,
            "Median P/E":       pe_med,
            "Predicted Price":  pred_price,
            "Actual Price":     actual_price,
            "Error (%)":       err_pct,
            "Hit (±10%)":      "✔️" if hit else "❌",
        })

    df_bt = pd.DataFrame(records)
    if df_bt.empty:
        st.warning("ℹ️ Not enough data to run a backtest for that horizon.")
        st.stop()

    # 6) Hit rate metric
    hit_rate = (df_bt["Hit (±10%)"] == "✔️").mean() * 100
    st.metric("Hit Rate (±10% error)", f"{hit_rate:.1f}%")

    # 7) Plot Actual vs Predicted
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_bt["Base Year"], y=df_bt["Actual Price"],
        mode="lines+markers", name="Actual"
    ))
    fig.add_trace(go.Scatter(
        x=df_bt["Base Year"], y=df_bt["Predicted Price"],
        mode="lines+markers", name="Predicted"
    ))
    fig.update_layout(
        title=f"{ticker}: {horizon}-Year Backtest",
        xaxis_title="Base Year",
        yaxis_title="Price ($)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    # 8) Show detail table
    st.dataframe(df_bt.style.format({
        "EPS":              "{:.2f}",
        "Median P/E":       "{:.2f}",
        "Predicted Price":  "${:,.2f}",
        "Actual Price":     "${:,.2f}",
        "Error (%)":        "{:+.1f}%",
    }))
