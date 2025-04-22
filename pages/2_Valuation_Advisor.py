import streamlit as st
import yfinance as yf
from helpers.peer_lookup import get_dynamic_peers
from helpers.valuation_logic import analyze_valuation, plot_price_range

st.set_page_config(layout="wide")
st.title("💸 Valuation Advisor")

# force uppercase/trim whitespace
ticker_input = st.text_input("Enter a ticker symbol", "DELL").upper().strip()

if ticker_input:
    with st.spinner("🔍 Looking up peers…"):
        peers = get_dynamic_peers(ticker_input)

    st.markdown(f"**Peers (by SIC):** {', '.join(peers) if peers else 'N/A'}")

    if not peers:
        st.warning("⚠️ Could not fetch dynamic peer list via SIC.")
        st.stop()

    result = analyze_valuation(ticker_input, peers)
    if not result.get("eps") or not result.get("industry_pe_avg"):
        st.warning("⚠️ EPS or P/E data not available — cannot perform valuation.")
        st.stop()

    # Show key metrics
    st.subheader("📊 Key Valuation Inputs")
    col1, col2, col3 = st.columns(3)
    col1.metric("EPS (TTM)", f"{result['eps']:.2f}")
    col2.metric("Industry Avg P/E", f"{result['industry_pe_avg']:.2f}")
    col3.metric("Current Price", f"${result['current_price']:.2f}")

    # Recommendation
    st.subheader("✅ Recommendation")
    st.success(result["recommendation"])

    # Valuation range chart
    st.subheader("📉 Valuation Range Visualization")
    plot_price_range(
        result["current_price"],
        result["implied_price_min"],
        result["implied_price_max"],
        result["implied_price"],
    )

    # Percentage gap caption
    if result["implied_price"] and result["current_price"]:
        gap = (result["implied_price"] - result["current_price"]) \
              / result["implied_price"] * 100
        if gap > 0:
            st.caption(f"📉 Current price is **{gap:.1f}% below** peer‑based valuation average.")
        else:
            st.caption(f"📈 Current price is **{abs(gap):.1f}% above** peer‑based valuation average.")
