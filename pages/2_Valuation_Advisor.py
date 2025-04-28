import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set Streamlit page config
st.set_page_config(layout="wide")
st.title("💸 Valuation Advisor")

# File path
file_path = 'data/Master data price eps etc.xlsx'

# Load data functions
@st.cache_data
def load_company_data():
    df = pd.read_excel(file_path, sheet_name='Company Dta', header=None)
    headers = df.iloc[3]
    df.columns = headers
    df = df.iloc[4:].reset_index(drop=True)
    return df

@st.cache_data
def load_eps_price_data(df):
    eps_data = df.iloc[:, 9:24].apply(pd.to_numeric, errors='coerce')
    price_data = df.iloc[:, 24:39].apply(pd.to_numeric, errors='coerce')
    eps_data.columns = list(range(2010, 2025))
    price_data.columns = list(range(2010, 2025))

    ticker_data = df['Ticker'].reset_index(drop=True)
    gsubind_data = df['gsubind'].reset_index(drop=True)

    return eps_data, price_data, ticker_data, gsubind_data

# Load data
company_data = load_company_data()
eps_data, price_data, ticker_data, gsubind_data = load_eps_price_data(company_data)

# Input
ticker_input = st.text_input("Enter a ticker symbol", "DELL").upper()

if ticker_input and ticker_input in ticker_data.values:
    idx = ticker_data[ticker_data == ticker_input].index[0]
    company_gsubind = gsubind_data[idx]

    # Peers in same gsubind
    peer_indices = gsubind_data[gsubind_data == company_gsubind].index
    peers = ticker_data.loc[peer_indices].tolist()

    # Show sector/industry from company_data
    sector = company_data.loc[idx, 'Industry'] if 'Industry' in company_data.columns else "N/A"
    industry = company_data.loc[idx, 'Industry'] if 'Industry' in company_data.columns else "N/A"

    st.markdown(f"**Sector:** {sector}  ")
    st.markdown(f"**Industry:** {industry}  ")
    st.markdown(f"**Peers:** {', '.join(peers)}")

    # Calculate Median P/E for all peers
    pe_ratio = price_data.divide(eps_data)
    pe_ratio_with_gsubind = pe_ratio.copy()
    pe_ratio_with_gsubind['gsubind'] = gsubind_data.values

    peer_pe_ratios = pe_ratio_with_gsubind.loc[peer_indices]
    industry_pe_avg = peer_pe_ratios[2024].median()

    # Valuation
    eps = eps_data.loc[idx, 2024]
    current_price = price_data.loc[idx, 2024]
    implied_price = eps * industry_pe_avg
    implied_price_min = eps * peer_pe_ratios[2024].min()
    implied_price_max = eps * peer_pe_ratios[2024].max()

    # Display Key Inputs
    st.subheader("📊 Key Valuation Inputs")
    col1, col2, col3 = st.columns(3)
    col1.metric("EPS (2024)", f"{eps:.2f}")
    col2.metric("Industry Median P/E", f"{industry_pe_avg:.2f}")
    col3.metric("Current Price (2024)", f"${current_price:.2f}")

    # Recommendation Logic
    st.subheader("✅ Recommendation")
    if implied_price > current_price:
        st.success("📈 Likely Undervalued — Consider Buying")
    else:
        st.warning("📉 Likely Overvalued — Exercise Caution")

    # Visualization
    st.subheader("📉 Valuation Range Visualization")
    fig, ax = plt.subplots(figsize=(8, 2))
    ax.axhline(implied_price, color='blue', linewidth=2, label='Avg Implied Price')
    ax.plot(current_price, 0, 'ro', label='Current Price')
    ax.set_xlim([implied_price_min * 0.9, implied_price_max * 1.1])
    ax.set_yticks([])
    ax.set_xlabel('Price Range')
    ax.legend()
    st.pyplot(fig)

    gap = ((implied_price - current_price) / implied_price) * 100
    if gap > 0:
        st.caption(f"📉 Current price is **{gap:.1f}% below** peer-based valuation average.")
    else:
        st.caption(f"📈 Current price is **{abs(gap):.1f}% above** peer-based valuation average.")
else:
    st.warning("Ticker not found. Please check and try again.")
