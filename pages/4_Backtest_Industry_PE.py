import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# 📥 Load Data
@st.cache_data
def load_data():
    file_path = 'data/Master data price eps etc.xlsx'

    company_data = pd.read_excel(file_path, sheet_name='Company Dta', header=None)
    headers = company_data.iloc[3]
    company_data.columns = headers
    company_data = company_data.iloc[4:].reset_index(drop=True)

    eps_data = company_data.iloc[:, 9:24].apply(pd.to_numeric, errors='coerce')
    price_data = company_data.iloc[:, 24:39].apply(pd.to_numeric, errors='coerce')
    eps_data.columns = list(range(2010, 2025))
    price_data.columns = list(range(2010, 2025))

    ticker_data = company_data.iloc[:, 0].reset_index(drop=True)
    gsubind_data = company_data['gsubind'].reset_index(drop=True)

    median_pe = pd.read_excel(file_path, sheet_name='Median PE', header=None)
    median_pe_data_trimmed = median_pe.iloc[5:, :18].reset_index(drop=True)
    median_pe_data_trimmed.columns = [None, None, 'gsubind'] + list(range(2010, 2025))
    gsubind_to_median_pe = {
        row['gsubind']: row[3:].values for _, row in median_pe_data_trimmed.iterrows()
    }

    analysis_data = pd.read_excel(file_path, sheet_name='Analysis', header=None)
    analysis_data_trimmed = analysis_data.iloc[5:, :40].reset_index(drop=True)
    actual_price_data = analysis_data_trimmed.iloc[:, 24:39].apply(pd.to_numeric, errors='coerce')
    actual_price_data.columns = list(range(2010, 2025))
    actual_price_data.index = analysis_data_trimmed.iloc[:, 0]

    return company_data, eps_data, price_data, ticker_data, gsubind_data, gsubind_to_median_pe, actual_price_data

# 🚀 Load
company_data, eps_data, price_data, ticker_data, gsubind_data, gsubind_to_median_pe, actual_price_data = load_data()
years = list(range(2010, 2025))

# 📊 Streamlit App
st.title("📊 Company Stock Valuation Analysis")
ticker_input = st.text_input("Enter Ticker (e.g., AAPL, DELL, TSLA)").upper()

if ticker_input:
    if ticker_input in ticker_data.values:
        idx = ticker_data[ticker_data == ticker_input].index[0]

        st.subheader(f"Details for: {ticker_input}")
        gsubind = gsubind_data[idx]
        st.write("**gsubind:**", f"🧭 {gsubind}")

        eps_row = eps_data.loc[idx]
        eps_row = eps_row.mask(eps_row <= 0)

        median_pe_row = pd.Series(gsubind_to_median_pe.get(gsubind, [None]*len(years)), index=years)
        model_price = eps_row * median_pe_row

        try:
            actual_price = actual_price_data.loc[ticker_input]
        except KeyError:
            st.error(f"Ticker '{ticker_input}' not found in 'Analysis' actual price data.")
            st.stop()

        # ✅ FIXED: More robust current price fetching with fallback
        try:
            ticker_obj = yf.Ticker(ticker_input)
            info = ticker_obj.info
            current_price = info.get("regularMarketPrice")

            if current_price is None:
                hist = ticker_obj.history(period="1d")
                current_price = hist["Close"].iloc[-1] if not hist.empty else None

        except Exception:
            current_price = None
            st.warning("⚠️ Could not fetch live price from Yahoo Finance (rate-limited or invalid ticker).")

        st.subheader("📈 Price Comparison for 2024")
        col1, col2, col3 = st.columns(3)

        if not pd.isna(model_price.get(2024)):
            col1.metric("Model Price (2024)", f"${model_price[2024]:.2f}")
        else:
            col1.metric("Model Price (2024)", "N/A")

        if not pd.isna(actual_price.get(2024)):
            col2.metric("Actual Price (2024)", f"${actual_price[2024]:.2f}")
        else:
            col2.metric("Actual Price (2024)", "N/A")

        if current_price is not None:
            col3.metric("Current Stock Price", f"${current_price:.2f}")
        else:
            col3.metric("Current Stock Price", "N/A")

    else:
        st.error(f"❌ Ticker '{ticker_input}' not found in uploaded data.")
