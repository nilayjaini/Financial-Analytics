import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🧮 Industry P/E × EPS Backtest")

@st.cache_data
def load_data():
    # 1) Load industry mappings and metrics from data/
    gics = pd.read_csv("data/GICS code.csv", parse_dates=["datadate"])
    xls = pd.ExcelFile("data/Master_data_EPS_Price_PE.xlsx")
    df_eps   = xls.parse(xls.sheet_names[0], parse_dates=["datadate"])
    df_price = xls.parse(xls.sheet_names[1], parse_dates=["datadate"])
    df_pe    = xls.parse(xls.sheet_names[2], parse_dates=["datadate"])
    # 2) Merge
    df = (
        df_eps.rename(columns={"eps":"EPS"})
          .merge(df_price.rename(columns={"price":"ActualPrice"}), on=["tic","datadate"])
          .merge(df_pe.rename(columns={"pe":"PE"}), on=["tic","datadate"])
          .merge(gics[["tic","gsubind","fyear"]], on=["tic","datadate"], how="left")
    )
    df["year"] = df["datadate"].dt.year
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
    bt["Predicted"] = bt["MedianPE"] * bt["EPS"]

    # actual at year+horizon
    price_map = df.set_index(["tic","year"])["ActualPrice"]
    def get_actual(row):
        return price_map.get((stock, row.year + horizon), np.nan)
    bt["Actual"] = bt.apply(get_actual, axis=1)

    # errors & hit
    bt["PctError"] = (bt["Actual"] - bt["Predicted"]) / bt["Predicted"] * 100
    bt["Hit"] = bt["PctError"].abs() < 10

    # show table
    st.subheader(f"Backtest for {stock} over {horizon}-yr horizon")
    st.dataframe(bt[["year","EPS","MedianPE","Predicted","Actual","PctError","Hit"]], use_container_width=True)

    # summary stats & chart
    st.markdown(f"""
    **Mean Abs % Error:** {bt["PctError"].abs().mean():.1f}%  
    **Hit Rate (|error|<10%):** {bt["Hit"].mean()*100:.1f}%  
    """)
    st.line_chart(bt.set_index("year")[["Actual","Predicted"]], height=300)

