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
    sector = company_data.loc[idx, 'Sector'] if 'Sector' in company_data.columns else "N/A"
    industry = company_data.loc[idx, 'Industry'] if 'Industry' in company_data.columns else "N/A"

    st.markdown(f"**Sector:** {sector}  ")
    st.markdown(f"**Industry:** {industry}  ")
    st.markdown(f"**Peers:** {', '.join(peers)}")

    # Calculate Median P/E for all peers
    pe_ratio = price_data.divide(eps_data)

    # ⚡ Remove negative and zero PEs
    pe_ratio = pe_ratio.mask((pe_ratio <= 0) | (pe_ratio.isna()))

    pe_ratio_with_gsubind = pe_ratio.copy()
    pe_ratio_with_gsubind['gsubind'] = gsubind_data.values

    peer_pe_ratios = pe_ratio_with_gsubind.loc[peer_indices]
    valid_peer_pe = peer_pe_ratios[2024].dropna()

    # EPS and Current Price
    eps = eps_data.loc[idx, 2024]
    current_price = price_data.loc[idx, 2024]

    # ⚡ Remove invalid EPS
    if eps <= 0 or np.isnan(eps):
        eps = np.nan

    if not valid_peer_pe.empty and not np.isnan(eps):
        industry_pe_avg = valid_peer_pe.median()
        implied_price_avg = eps * industry_pe_avg
        implied_price_min = eps * valid_peer_pe.min()
        implied_price_max = eps * valid_peer_pe.max()
    else:
        industry_pe_avg = implied_price_avg = implied_price_min = implied_price_max = np.nan

    # Display Key Inputs
    st.subheader("📊 Key Valuation Inputs")
    col1, col2, col3 = st.columns(3)
    col1.metric("EPS (2024)", f"{eps:.2f}" if not np.isnan(eps) else "N/A")
    col2.metric("Industry Median P/E", f"{industry_pe_avg:.2f}" if not np.isnan(industry_pe_avg) else "N/A")
    col3.metric("Current Price (2024)", f"${current_price:.2f}" if not np.isnan(current_price) else "N/A")

    # Recommendation Logic
    st.subheader("✅ Recommendation")
    if not np.isnan(implied_price_avg) and implied_price_avg > current_price:
        st.success("📈 Likely Undervalued — Consider Buying")
    elif not np.isnan(implied_price_avg):
        st.warning("📉 Likely Overvalued — Exercise Caution")
    else:
        st.info("ℹ️ Not enough data to provide recommendation.")

    # Visualization
    st.subheader("📉 Valuation Range Visualization")

    if not valid_peer_pe.empty and not np.isnan(eps):
        fig, ax = plt.subplots(figsize=(10, 2.5))

        # Gray bar for implied price range
        ax.hlines(1, implied_price_min, implied_price_max, color='gray', linewidth=10, alpha=0.4)

        # Blue line: median implied price
        ax.vlines(implied_price_avg, 0.9, 1.1, color='blue', linewidth=2, label='Avg Implied Price')

        # Red dot: current stock price
        ax.plot(current_price, 1, 'ro', markersize=10, label='Current Price')

        # Add separate text labels without overlap
        ax.text(implied_price_min, 1.15, f"Low: ${implied_price_min:.2f}", ha='center', fontsize=9)
        ax.text(implied_price_avg, 1.27, f"Avg: ${implied_price_avg:.2f}", ha='center', fontsize=9, color='blue')
        ax.text(implied_price_max, 1.15, f"High: ${implied_price_max:.2f}", ha='center', fontsize=9)

        ax.set_xlim(implied_price_min * 0.85, implied_price_max * 1.15)
        ax.set_ylim(0.8, 1.4)
        ax.axis('off')
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.35), ncol=2)

        st.pyplot(fig)

        # Gap commentary
        gap = ((implied_price_avg - current_price) / implied_price_avg) * 100
        if gap > 0:
            st.caption(f"📉 Current price is **{gap:.1f}% below** the implied valuation average.")
        else:
            st.caption(f"📈 Current price is **{abs(gap):.1f}% above** the implied valuation average.")
    else:
        st.warning("⚠️ Not enough valid peer data to create a proper visualization.")

else:
    if ticker_input:
        st.error("❌ Ticker not found. Please check and try again.")
