import pandas as pd
import streamlit as st

@st.cache_data
def load_compustat_data():
    base = "data/"

    # Read each file and select only the columns we absolutely need
    df_eps   = pd.read_csv(base + "Compustat_eps.csv",   usecols=["tic","fyear","EPS"])
    df_pe    = pd.read_csv(base + "Compustat_PE.csv",    usecols=["tic","fyear","PE"])
    df_price = pd.read_csv(base + "compustat_price.csv", usecols=["tic","fyear","Price"])
    df_mkt   = pd.read_csv(base + "Compustat_2024_mkt_value.csv", 
                           usecols=["tic","fyear","MktCap","gsubind"])

    # Merge them one by one on tic + fyear
    df = (
        df_eps
        .merge(df_pe,    on=["tic","fyear"], how="inner")
        .merge(df_price, on=["tic","fyear"], how="inner")
        .merge(df_mkt,   on=["tic","fyear"], how="inner")
    )

    # drop any non-positive or missing EPS/PE rows
    df = df[(df.EPS  > 0) & (df.PE  > 0)]
    return df
