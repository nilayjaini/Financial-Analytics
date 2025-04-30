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
    gsubind_to_median_pe = {row['gsubind']: row[3:].values for _, row in median_pe_data_trimmed.iterrows()}

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

if ticker_input and ticker_input in ticker_data.values:
    idx = ticker_data[ticker_data == ticker_input].index[0]
    gsubind = gsubind_data[idx]

    eps_row = eps_data.loc[idx].mask(eps_data.loc[idx] <= 0)
    median_pe_row = pd.Series(gsubind_to_median_pe.get(gsubind, [None]*len(years)), index=years)
    model_price = eps_row * median_pe_row

    try:
        actual_price = actual_price_data.loc[ticker_input]
    except KeyError:
        st.error(f"Ticker '{ticker_input}' not found in 'Analysis' actual price data.")
        st.stop()

    try:
        ticker_obj = yf.Ticker(ticker_input)
        current_price_info = ticker_obj.history(period="1d")
        current_price = current_price_info['Close'].iloc[-1] if not current_price_info.empty else None
    except Exception as e:
        current_price = None
        st.error(f"Error fetching current price: {e}")

    # 📈 Price Comparison
    st.subheader("📈 Price Comparison for 2024")
    col1, col2, col3 = st.columns(3)
    col1.metric("Model Price (2024)", f"${model_price[2024]:.2f}" if not pd.isna(model_price[2024]) else "N/A")
    col2.metric("Actual Price (2024)", f"${actual_price[2024]:.2f}" if not pd.isna(actual_price[2024]) else "N/A")
    col3.metric("Current Market Price", f"${current_price:.2f}" if current_price else "N/A")

    # ⏳ Prepare Table
    price_df = pd.DataFrame({
        'Year': years,
        'EPS': eps_row.values,
        'Median PE': median_pe_row.values,
        'Model Price': model_price.values,
        'Actual Price': actual_price.values
    })
    price_df['Prediction'] = np.where(model_price > actual_price, 'Up', 'Down')
    st.dataframe(price_df, use_container_width=True)

    # 🎯 Hit Rate
    total, correct = 0, 0
    for y in range(2010, 2024):
        if pd.isna(model_price.get(y)): continue
        pred = 'Up' if model_price[y] > actual_price[y] else 'Down'
        for offset in [1, 2]:
            if pd.notna(actual_price.get(y + offset)):
                move = 'Up' if actual_price[y + offset] > actual_price[y] else 'Down'
                correct += int(pred == move)
                total += 1
    hit_rate = correct / total * 100 if total else np.nan
    st.subheader("🎯 Overall Prediction Hit Rate Analysis")
    st.markdown(f"**Total Valid Predictions:** {total}")
    st.markdown(f"**Correct Predictions:** {correct}")
    st.success(f"✅ Hit Rate: **{hit_rate:.2f}%**") if not np.isnan(hit_rate) else st.warning("Not enough data.")

else:
    if ticker_input:
        st.error("❌ Ticker not found. Please check and try again.")
