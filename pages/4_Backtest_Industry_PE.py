import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

# -- load & merge --
@st.cache_data
def load_compustat():
    # adjust file names/paths as needed
    df_eps   = pd.read_csv("data/Compustat_eps.csv")
    df_pe    = pd.read_csv("data/Compustat_PE.csv")
    df_price = pd.read_csv("data/compustat_price.csv")
    # only keep years 2010–2024
    mask = df_eps["fyear"].between(2010, 2024)
    df_eps   = df_eps[mask]
    df_pe    = df_pe[df_pe["fyear"].between(2010, 2024)]
    df_price = df_price[df_price["fyear"].between(2010, 2024)]

    # merge on ticker & year
    df = (
        df_eps
        .merge(df_pe[["tic","fyear","PE"]],    on=["tic","fyear"], how="inner")
        .merge(df_price[["tic","fyear","Price"]], on=["tic","fyear"], how="inner")
    )

    # drop any non-positive
    df = df[(df["eps"]   > 0) &
            (df["PE"]    > 0) &
            (df["Price"] > 0)]

    return df

df = load_compustat()

# -- user inputs --
ticker   = st.text_input("Ticker for backtest", "MSFT").upper()
horizon  = st.selectbox("Forecast horizon (years)", [1,2,3,5], index=0)

# must have at least 2015–2024 in your CSV
YEARS = list(range(2015, 2025))

if ticker:
    # ensure ticker exists
    if ticker not in df["tic"].unique():
        st.error(f"Ticker {ticker} not found in data.")
        st.stop()

    # grab sub-industry code for grouping
    # NOTE: adjust this if your file uses 'gsubind' or another column for sub-industry
    subind = df.loc[df["tic"]==ticker, "gsubind"].dropna().unique()
    if len(subind)==0:
        st.warning("No subindustry found; grouping by ticker only.")
    else:
        subind = subind[0]
        st.markdown(f"**Sub-Industry Code:** {subind}")

    # filter for this stock
    df_stock = df[df["tic"]==ticker]

    results = []
    for Y in YEARS:
        # need EPS at Y-1 and median PE at Y-1
        prev = Y-1
        row_eps = df_stock[df_stock["fyear"]==prev]
        if row_eps.empty:
            continue
        eps_prev = float(row_eps["eps"].iloc[0])

        # median P/E for subindustry (or overall if no subind)
        if subind:
            df_grp = df[df["gsubind"]==subind]
        else:
            df_grp = df
        med_pe = df_grp.loc[df_grp["fyear"]==prev, "PE"].median()
        if pd.isna(med_pe):
            continue

        # predicted price for year Y
        predicted = eps_prev * med_pe

        # actual price in year Y
        row_act = df_stock[df_stock["fyear"]==Y]
        actual = float(row_act["Price"].iloc[0]) if not row_act.empty else None

        if actual is not None:
            error_pct = 100*(actual - predicted)/predicted
            hit = abs(error_pct) <= 10
        else:
            error_pct = None
            hit = False

        results.append({
            "year": Y,
            "eps(prev)": eps_prev,
            "med_PE(prev)": med_pe,
            "predicted": predicted,
            "actual": actual,
            "error_%": error_pct,
            "hit": hit
        })

    backtest = pd.DataFrame(results)

    if backtest.empty:
        st.warning("No complete data points for the chosen years/horizon.")
        st.stop()

    # overall hit rate
    hit_rate = 100*backtest["hit"].mean()
    st.metric("Hit Rate (±10%)", f"{hit_rate:.1f}%")

    # bar chart of yearly hits
    fig = px.bar(
        backtest,
        x="year",
        y=backtest["hit"].astype(int),
        labels={"y":"Hit (1=yes,0=no)"},
        title=f"Yearly Hit/Miss for {ticker} (horizon={horizon}y)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # show detailed table
    st.dataframe(backtest, use_container_width=True)
