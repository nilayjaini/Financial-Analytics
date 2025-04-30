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
    # Visualization
st.subheader("📉 Valuation Range Visualization")

# Ensure min, max are valid and not negative or extreme
valid_peer_pe = peer_pe_ratios[2024].dropna()
import matplotlib.pyplot as plt

# Assuming eps, current_price, valid_peer_pe, implied_price are defined earlier
if not valid_peer_pe.empty and eps > 0:
    implied_price_min = eps * valid_peer_pe.min()
    implied_price_max = eps * valid_peer_pe.max()
    implied_price_avg = implied_price

    fig, ax = plt.subplots(figsize=(10, 2))

    # Gray bar: Implied price range
    ax.hlines(1, implied_price_min, implied_price_max, color='gray', linewidth=10, alpha=0.4)

    # Blue line: Avg implied price
    ax.vlines(implied_price_avg, 0.9, 1.1, color='blue', linewidth=2, label='Avg Implied Price')

    # Red dot: Current price
    ax.plot(current_price, 1, 'ro', markersize=10, label='Current Price')

    # Add text labels for min, avg, max
    ax.text(implied_price_min, 1.15, f"Low: ${implied_price_min:.2f}", ha='left', fontsize=9)
    ax.text(implied_price_avg, 1.15, f"Avg: ${implied_price_avg:.2f}", ha='center', fontsize=9, color='blue')
    ax.text(implied_price_max, 1.15, f"High: ${implied_price_max:.2f}", ha='right', fontsize=9)

    ax.set_xlim([implied_price_min * 0.9, implied_price_max * 1.1])
    ax.set_ylim([0.8, 1.2])
    ax.axis('off')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.3), ncol=2)

    st.pyplot(fig)

    # Caption on valuation gap
    gap = ((implied_price_avg - current_price) / implied_price_avg) * 100
    if gap > 0:
        st.caption(f"📉 Current price is **{gap:.1f}% below** the implied valuation average.")
    else:
        st.caption(f"📈 Current price is **{abs(gap):.1f}% above** the implied valuation average.")
else:
    st.warning("⚠️ Not enough valid peer data to create a proper visualization.")

# if not valid_peer_pe.empty and eps > 0:
#     implied_price_min = eps * valid_peer_pe.min()
#     implied_price_max = eps * valid_peer_pe.max()
#     fig, ax = plt.subplots(figsize=(8, 1.5))

#     ax.plot([implied_price_min, implied_price_max], [0, 0], color='gray', linewidth=10, alpha=0.3)
#     ax.plot(implied_price, 0, 'b|', markersize=30, label='Avg Implied Price')
#     ax.plot(current_price, 0, 'ro', markersize=12, label='Current Price')

#     ax.set_xlim([implied_price_min * 0.9, implied_price_max * 1.1])
#     ax.set_yticks([])
#     ax.set_xlabel('Price Range')
#     ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=2)

#     st.pyplot(fig)

#     gap = ((implied_price - current_price) / implied_price) * 100
#     if gap > 0:
#         st.caption(f"📉 Current price is **{gap:.1f}% below** peer-based valuation average.")
#     else:
#         st.caption(f"📈 Current price is **{abs(gap):.1f}% above** peer-based valuation average.")
# else:
#     st.warning("⚠️ Not enough valid peer data to create a proper visualization.")
