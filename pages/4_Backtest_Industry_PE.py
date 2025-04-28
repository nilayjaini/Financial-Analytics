import streamlit as st
import pandas as pd
import numpy as np

# Load all required data
@st.cache_data
def load_data():
    file_path = 'data/Master data price eps etc.xlsx'

    # Load Company Dta sheet
    company_data = pd.read_excel(file_path, sheet_name='Company Dta', header=None)
    headers = company_data.iloc[3]
    company_data.columns = headers
    company_data = company_data.iloc[4:].reset_index(drop=True)

    # EPS and Price from Company Dta
    eps_data = company_data.iloc[:, 9:24].apply(pd.to_numeric, errors='coerce')
    price_data = company_data.iloc[:, 24:39].apply(pd.to_numeric, errors='coerce')
    eps_data.columns = list(range(2010, 2025))
    price_data.columns = list(range(2010, 2025))

    # Metadata
    ticker_data = company_data.iloc[:, 0].reset_index(drop=True)
    gsubind_data = company_data['gsubind'].reset_index(drop=True)

    # Median PE
    median_pe = pd.read_excel(file_path, sheet_name='Median PE', header=None)
    median_pe_data_trimmed = median_pe.iloc[5:, :18].reset_index(drop=True)
    median_pe_data_trimmed.columns = [None, None, 'gsubind'] + list(range(2010, 2025))
    gsubind_to_median_pe = {row['gsubind']: row[3:].values for _, row in median_pe_data_trimmed.iterrows()}

    # Actual prices from Analysis sheet
    analysis_data = pd.read_excel(file_path, sheet_name='Analysis', header=None)
    analysis_data_trimmed = analysis_data.iloc[5:, :40].reset_index(drop=True)
    actual_price_data = analysis_data_trimmed.iloc[:, 24:39].apply(pd.to_numeric, errors='coerce')
    actual_price_data.columns = list(range(2010, 2025))
    actual_price_data.index = analysis_data_trimmed.iloc[:, 0]

    return company_data, eps_data, price_data, ticker_data, gsubind_data, gsubind_to_median_pe, actual_price_data

# Load data
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
        st.write("**gsubind:**", f"🧭 {gsubind}")

        eps_row = eps_data.loc[idx]
        median_pe_row = pd.Series(gsubind_to_median_pe.get(gsubind, [None]*len(years)), index=years)
        model_price = eps_row * median_pe_row

        try:
            actual_price = actual_price_data.loc[ticker_input]
        except KeyError:
            st.error(f"Ticker '{ticker_input}' not found in 'Analysis' actual price data.")
            st.stop()

        price_df = pd.DataFrame({
            'Year': years,
            'EPS': eps_row.values,
            'Median PE': median_pe_row.values,
            'Model Price': model_price.values,
            'Actual Price': actual_price.values
        })

        price_df['Prediction'] = np.where(model_price > actual_price, 'Up', 'Down')

        # --- Prediction Hit Rate Calculation ---
        if not np.isnan(actual_price[2010]) and not np.isnan(actual_price[2011]) and not np.isnan(actual_price[2012]):
            model_prediction_2010 = price_df.query("Year == 2010")['Prediction'].values[0]

            actual_movement_next_year = 'Up' if actual_price[2011] > actual_price[2010] else 'Down'
            actual_movement_second_year = 'Up' if actual_price[2012] > actual_price[2010] else 'Down'

            correct_next_year = 1 if model_prediction_2010 == actual_movement_next_year else 0
            correct_second_year = 1 if model_prediction_2010 == actual_movement_second_year else 0

            total_predictions = 2
            correct_predictions = correct_next_year + correct_second_year
            hit_rate_percent = (correct_predictions / total_predictions) * 100

            # --- Display Hit Rate ---
            st.subheader("🎯 Prediction Hit Rate Analysis")
            st.markdown(f"**Prediction for 2010 was:** `{model_prediction_2010}`")
            st.markdown(f"- 2011 Actual Movement: `{actual_movement_next_year}`")
            st.markdown(f"- 2012 Actual Movement: `{actual_movement_second_year}`")
            st.success(f"✅ Overall Prediction Hit Rate: **{hit_rate_percent:.2f}%** over 2 years")

        else:
            st.warning("⚠️ Not enough data for 2010/2011/2012 to calculate Hit Rate.")

        # --- Show Main Table ---
        st.dataframe(price_df, use_container_width=True)

        # --- Final Prediction for 2024 ---
        price_df.set_index('Year', inplace=True)
        if 2024 in price_df.index and not pd.isna(price_df.loc[2024, 'Prediction']):
            st.success(f"🔮 Final Prediction for 2024: {price_df.loc[2024, 'Prediction']}")
        else:
            st.warning("Prediction for 2024 is not available (missing data).")

    else:
        st.warning("Ticker not found. Please check and try again.")
