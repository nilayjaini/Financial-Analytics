import streamlit as st
import pandas as pd
import numpy as np

# Load all required data
@st.cache_data
def load_data():
    file_path = 'Master data price eps etc.xlsb'
    company_data = pd.read_excel(file_path, sheet_name='Company Dta', engine='pyxlsb', header=None)
    median_pe = pd.read_excel(file_path, sheet_name='Median PE', engine='pyxlsb', header=None)
    analysis_data = pd.read_excel(file_path, sheet_name='Analysis', engine='pyxlsb', header=None)

    # Company Data Cleanup
    headers = company_data.iloc[3]
    company_data.columns = headers
    company_data = company_data.iloc[4:].reset_index(drop=True)

    # EPS and Price data
    eps_data = company_data.iloc[:, 9:24].apply(pd.to_numeric, errors='coerce')
    price_data = company_data.iloc[:, 24:39].apply(pd.to_numeric, errors='coerce')
    eps_data.columns = list(range(2010, 2025))
    price_data.columns = list(range(2010, 2025))

    # Metadata
    ticker_data = company_data.iloc[:, 0].reset_index(drop=True)
    gsubind_data = company_data['gsubind'].reset_index(drop=True)

    # Median PE Mapping
    median_pe_data_trimmed = median_pe.iloc[5:, :18].reset_index(drop=True)
    median_pe_data_trimmed.columns = [None, None, 'gsubind'] + list(range(2010, 2025))
    gsubind_to_median_pe = {row['gsubind']: row[3:].values for _, row in median_pe_data_trimmed.iterrows()}

    # Actual price data
    actual_price_data = analysis_data.iloc[5:, 24:39].apply(pd.to_numeric, errors='coerce')
    actual_price_data.columns = list(range(2010, 2025))

    return company_data, eps_data, price_data, ticker_data, gsubind_data, gsubind_to_median_pe, actual_price_data

# Load everything
company_data, eps_data, price_data, ticker_data, gsubind_data, gsubind_to_median_pe, actual_price_data = load_data()
years = list(range(2010, 2025))

# Streamlit App
st.title("📊 Company Stock Valuation Analysis")
ticker_input = st.text_input("Enter Ticker (e.g., AAPL, DELL, etc.)").upper()

if ticker_input:
    if ticker_input in ticker_data.values:
        idx = ticker_data[ticker_data == ticker_input].index[0]

        st.subheader(f"Details for: {ticker_input}")
        gsubind = gsubind_data[idx]
        st.write("**gsubind:**", gsubind)

        eps_row = eps_data.loc[idx]
        price_row = price_data.loc[idx]
        median_pe_row = pd.Series(gsubind_to_median_pe.get(gsubind, [None]*len(years)), index=years)

        model_price = eps_row * median_pe_row
        actual_price = actual_price_data.loc[idx]

        price_df = pd.DataFrame({
            'Year': years,
            'EPS': eps_row.values,
            'Median PE': median_pe_row.values,
            'Model Price': model_price.values,
            'Actual Price': actual_price.values
        })
        price_df['Prediction'] = np.where(model_price > actual_price, 'Up', 'Down')

        st.dataframe(price_df.set_index('Year'), use_container_width=True)

        st.success(f"🔮 Final Prediction for 2024: {price_df.loc[2024, 'Prediction']}")
    else:
        st.warning("Ticker not found. Please check and try again.")
    
