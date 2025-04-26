import pandas as pd
import streamlit as st

@st.cache_data
def load_compustat_data():
    # adjust paths if you put data folder elsewhere
    path = "data/"
    df_mkt  = pd.read_csv(path + "Compustat_2024_mkt_value.csv")
    df_pe   = pd.read_csv(path + "Compustat_PE.csv")
    df_eps  = pd.read_csv(path + "Compustat_eps.csv")
    df_price= pd.read_csv(path + "compustat_price.csv")

    # Merge on your chosen key — here I'm assuming 'tic' and 'fyear' exist
    df = (
        df_eps
        .merge(df_pe,    on=["tic","fyear"], how="inner")
        .merge(df_mkt,   on=["tic","fyear"], how="inner")
        .merge(df_price, on=["tic","fyear"], how="inner")
    )

    # drop rows with missing or non-positive EPS/PE
    df = df[(df["EPS"]  > 0) & (df["PE"]   > 0)]
    return df
