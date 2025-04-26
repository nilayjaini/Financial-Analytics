import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

@st.cache_data
def load_data():
    # 1) Load your GICS mapping
    gics = pd.read_csv("data/GICS code.csv", parse_dates=["datadate"])
    # 2) Load each sheet from the master Excel
    xls = pd.ExcelFile("data/Master_data_EPS_Price_PE.xlsx")
    df_eps_wide   = xls.parse("EPS")
    df_price_wide = xls.parse("Price")
    df_pe_wide    = xls.parse("PE")

    # 3) Identify the “date” columns (anything beyond the ID columns)
    id_cols = ["Ticker", "conm", "gsubind", "sic"]
    date_cols = [c for c in df_eps_wide.columns if c not in id_cols]

    # 4) Melt each into long form
    df_eps = (
        df_eps_wide
        .melt(id_vars=id_cols, value_vars=date_cols,
              var_name="datadate", value_name="EPS")
    )
    df_price = (
        df_price_wide
        .melt(id_vars=id_cols, value_vars=date_cols,
              var_name="datadate", value_name="ActualPrice")
    )
    df_pe = (
        df_pe_wide
        .melt(id_vars=id_cols, value_vars=date_cols,
              var_name="datadate", value_name="PE")
    )

    # 5) Convert the datadate column to real datetimes
    for df_ in (df_eps, df_price, df_pe):
        df_["datadate"] = pd.to_datetime(df_["datadate"])

    # 6) Merge the three metrics together
    df = (
        df_eps
        .merge(df_price[["Ticker","datadate","ActualPrice"]],
               on=["Ticker","datadate"])
        .merge(df_pe[["Ticker","datadate","PE"]],
               on=["Ticker","datadate"])
    )

    # 7) Merge in your GICS fyear + industry code
    #    Note: in gics CSV your ticker column is probably named 'tic'
    df = (
        df
        .merge(
            gics.rename(columns={"tic":"Ticker"})[["Ticker","datadate","gsubind","fyear"]],
            on=["Ticker","datadate"],
            how="left"
        )
    )

    # 8) Prepare for backtest
    df["year"] = df["fyear"]
    df.rename(columns={"Ticker":"tic"}, inplace=True)
    return df

df = load_data()

# --- UI controls ---
stock = st.text_input("Ticker for backtest", "MSFT").upper()
horizon = st.selectbox("Forecast horizon (years)", [1, 2], index=0)

if stock:
    # compute industry median P/E by (industry, year)
    med_pe = (
        df.groupby(["gsubind","year"])["PE"]
          .median()
          .reset_index()
          .rename(columns={"PE":"MedianPE"})
    )

    # pull EPS for our stock
    stock_eps = df[df["tic"]==stock][["year","EPS","gsubind"]]
    bt = stock_eps.merge(med_pe, on=["gsubind","year"], how="left")

    # predicted price
    bt["Predicted"] = bt["MedianPE"] * bt["EPS"]

    # actual price at year+horizon
    price_map = df.set_index(["tic","year"])["ActualPrice"]
    bt["Actual"] = bt.apply(lambda r: price_map.get((stock, r.year + horizon), np.nan), axis=1)

    # errors & hit flag
    bt["PctError"] = (bt["Actual"] - bt["Predicted"]) / bt["Predicted"] * 100
    bt["Hit"] = bt["PctError"].abs() < 10

    # display table
    st.subheader(f"Backtest for {stock} over {horizon}-yr horizon")
    st.dataframe(
        bt[["year","EPS","MedianPE","Predicted","Actual","PctError","Hit"]],
        use_container_width=True
    )

    # summary stats & chart
    st.markdown(f"""
    **Mean Abs % Error:** {bt["PctError"].abs().mean():.1f}%  
    **Hit Rate (|error|<10%):** {bt["Hit"].mean()*100:.1f}%  
    """)
    st.line_chart(bt.set_index("year")[["Actual","Predicted"]], height=300)
