import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set Streamlit page config
st.set_page_config(layout="wide")
st.title("💸 Valuation Advisor")

file_path = 'data/Master data price eps etc.xlsx'

@st.cache_data
def load_company_data():
    df = pd.read_excel(file_path, sheet_name='Company Dta', header=None)
    headers = df.iloc[3]
    df.columns = headers
    df = df.iloc[4:].reset_index(drop=True)
    return df

@st.cache_data
def load_all_data():
    company_df = load_company_data()
    eps_data = company_df.iloc[:, 9:24].apply(pd.to_numeric, errors='coerce')
    price_data = company_df.iloc[:, 24:39].apply(pd.to_numeric, errors='coerce')
    eps_data.columns = list(range(2010, 2025))
    price_data.columns = list(range(2010, 2025))
    ticker_data = company_df['Ticker'].reset_index(drop=True)
    gsubind_data = company_df['gsubind'].reset_index(drop=True)

    median_pe = pd.read_excel(file_path, sheet_name='Median PE', header=None)
    median_pe = median_pe.iloc[5:, :18].reset_index(drop=True)
    median_pe.columns = [None, None, 'gsubind'] + list(range(2010, 2025))

    return company_df, eps_data, price_data, ticker_data, gsubind_data, median_pe

# Load everything
company_df, eps_data, price_data, ticker_data, gsubind_data, median_pe_df = load_all_data()

# Input
ticker_input = st.text_input("Enter a ticker symbol", "DELL").upper()

if ticker_input and ticker_input in ticker_data.values:
    idx = ticker_data[ticker_data == ticker_input].index[0]
    gsubind = gsubind_data[idx]
    peers = ticker_data[gsubind_data == gsubind].tolist()

    # Sector / Industry info
    sector = company_df.loc[idx, 'Sector'] if 'Sector' in company_df.columns else "N/A"
    industry = company_df.loc[idx, 'Industry'] if 'Industry' in company_df.columns else "N/A"

    st.markdown(f"**Sector:** {sector}")
    st.markdown(f"**Industry:** {industry}")
    st.markdown(f"**Peers:** {', '.join(peers)}")

    # EPS and current price
    eps = eps_data.loc[idx, 2024]
    current_price = price_data.loc[idx, 2024]
    eps = np.nan if eps <= 0 or np.isnan(eps) else eps

    # ✅ Get gsubind median PE from 2024 column
    gsubind_median_row = median_pe_df[median_pe_df['gsubind'] == gsubind]
    industry_pe_2024 = gsubind_median_row[2024].values[0] if not gsubind_median_row.empty else np.nan

    # Compute implied price
    implied_price = eps * industry_pe_2024 if not np.isnan(eps) and not np.isnan(industry_pe_2024) else np.nan

    # Display Key Inputs
    st.subheader("📊 Key Valuation Inputs")
    col1, col2, col3 = st.columns(3)
    col1.metric("EPS (2024)", f"{eps:.2f}" if not np.isnan(eps) else "N/A")
    col2.metric("Industry Median P/E (2024)", f"{industry_pe_2024:.2f}" if not np.isnan(industry_pe_2024) else "N/A")
    col3.metric("Current Price (2024)", f"${current_price:.2f}" if not np.isnan(current_price) else "N/A")

    # Recommendation
    st.subheader("✅ Recommendation")
    if not np.isnan(implied_price) and implied_price > current_price:
        st.success("📈 Likely Undervalued — Consider Buying")
    elif not np.isnan(implied_price):
        st.warning("📉 Likely Overvalued — Exercise Caution")
    else:
        st.info("ℹ️ Not enough data to provide recommendation.")

    # Visualization
    st.subheader("📉 Valuation Range Visualization")

    # For low/high implied price, use min/max of peer PE * EPS
    peer_indices = gsubind_data[gsubind_data == gsubind].index
    peer_pe = price_data.divide(eps_data)
    peer_pe = peer_pe.mask((peer_pe <= 0) | (eps_data <= 0))  # clean invalid
    valid_peer_pe_2024 = peer_pe.loc[peer_indices, 2024].dropna()

    if not np.isnan(eps) and not valid_peer_pe_2024.empty:
        implied_price_min = eps * valid_peer_pe_2024.min()
        implied_price_max = eps * valid_peer_pe_2024.max()

        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.hlines(1, implied_price_min, implied_price_max, color='gray', linewidth=10, alpha=0.4)
        ax.vlines(implied_price, 0.9, 1.1, color='blue', linewidth=2, label='Avg Implied Price')
        ax.plot(current_price, 1, 'ro', markersize=10, label='Current Price')

        ax.text(implied_price_min, 1.15, f"Low: ${implied_price_min:.2f}", ha='center', fontsize=9)
        ax.text(implied_price, 1.27, f"Avg: ${implied_price:.2f}", ha='center', fontsize=9, color='blue')
        ax.text(implied_price_max, 1.15, f"High: ${implied_price_max:.2f}", ha='center', fontsize=9)

        ax.set_xlim(implied_price_min * 0.85, implied_price_max * 1.15)
        ax.set_ylim(0.8, 1.4)
        ax.axis('off')
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.35), ncol=2)
        st.pyplot(fig)

        # Gap commentary
        gap = ((implied_price - current_price) / implied_price) * 100
        if gap > 0:
            st.caption(f"📉 Current price is **{gap:.1f}% below** the implied valuation average.")
        else:
            st.caption(f"📈 Current price is **{abs(gap):.1f}% above** the implied valuation average.")
    else:
        st.warning("⚠️ Not enough valid peer data to create a proper visualization.")
else:
    if ticker_input:
        st.error("❌ Ticker not found. Please check and try again.")
