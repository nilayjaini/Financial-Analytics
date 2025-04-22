import streamlit as st
import yfinance as yf
from helpers.peer_lookup import get_dynamic_peers
from helpers.valuation_logic import analyze_valuation, plot_price_range

st.set_page_config(layout="wide")
st.title("💸 Valuation Advisor")

ticker_input = st.text_input("Enter a ticker symbol", "DELL")

if ticker_input:
    # dynamically fetch peers
    peers = get_dynamic_peers(ticker_input)
    st.markdown(f"**Peers (by SIC):** {', '.join(peers) if peers else 'N/A'}")

    if not peers:
        st.warning("⚠️ Could not fetch dynamic peer list via SIC.")
    else:
        result = analyze_valuation(ticker_input.upper(), peers)

        if not result['eps'] or not result['industry_pe_avg']:
            st.warning("⚠️ EPS or P/E data not available — cannot perform valuation.")
            st.stop()

        st.subheader("📊 Key Valuation Inputs")
        col1, col2, col3 = st.columns(3)
        col1.metric("EPS (TTM)", f"{result['eps']:.2f}")
        col2.metric("Industry Avg P/E", f"{result['industry_pe_avg']:.2f}")
        col3.metric("Current Stock Price", f"${result['current_price']:.2f}" if result['current_price'] else "N/A")

        st.subheader("✅ Recommendation")
        st.success(result['recommendation'])

        st.subheader("📉 Valuation Range Visualization")
        plot_price_range(
            result['current_price'],
            result['implied_price_min'],
            result['implied_price_max'],
            result['implied_price']
        )

        if result['implied_price']:
            gap = ((result['implied_price'] - result['current_price']) / result['implied_price']) * 100
            if gap > 0:
                st.caption(f"📉 Current price is **{gap:.1f}% below** peer-based valuation average.")
            else:
                st.caption(f"📈 Current price is **{abs(gap):.1f}% above** peer-based valuation average.")
