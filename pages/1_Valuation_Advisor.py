import streamlit as st
import yfinance as yf
from helpers.peer_lookup import get_peers
from helpers.valuation_logic import analyze_valuation, plot_price_range

st.title("📈 Stock Insight Explorer")

ticker_input = st.text_input("Enter a ticker symbol", "DELL")

if ticker_input:
    ticker = yf.Ticker(ticker_input.upper())
    peers, sector, industry = get_peers(ticker_input.upper())

    tab1, tab2 = st.tabs(["📄 Overview", "📊 Recommendations"])

    # ========== OVERVIEW ==========
    with tab1:
        st.header(f"Overview: {ticker_input.upper()}")

        try:
            stock_info = ticker.info
            hist = ticker.history(period="1d")

            current_price = stock_info.get("regularMarketPrice")
            change = stock_info.get("regularMarketChangePercent", 0)
            market_cap = stock_info.get("marketCap")
            pe_ratio = stock_info.get("trailingPE", "N/A")
            div_yield = stock_info.get("dividendYield", 0)
            week52_high = stock_info.get("fiftyTwoWeekHigh", "N/A")
            week52_low = stock_info.get("fiftyTwoWeekLow", "N/A")

            st.metric("Current Price", f"${current_price:.2f}", f"{change:.2%}")
            st.line_chart(hist["Close"])

            col1, col2, col3 = st.columns(3)
            col1.metric("P/E Ratio", pe_ratio)
            col2.metric("Div Yield", f"{div_yield*100:.2f}%" if div_yield else "N/A")
            col3.metric("Market Cap", f"${market_cap/1e9:.2f}B" if market_cap else "N/A")

            col4, col5 = st.columns(2)
            col4.metric("52-wk High", f"${week52_high}")
            col5.metric("52-wk Low", f"${week52_low}")

            st.caption("📌 Data powered by Yahoo Finance")

        except Exception as e:
            st.error("Could not load overview data.")
            st.exception(e)

    # ========== RECOMMENDATIONS ==========
    with tab2:
        st.header("Peer-Based Valuation & Recommendation")

        if not peers:
            st.warning("⚠️ Could not fetch peer data.")
        else:
            result = analyze_valuation(ticker_input.upper(), peers)

            if not result['eps'] or not result['industry_pe_avg']:
                st.warning("⚠️ EPS or P/E data not available — cannot perform valuation.")
                st.stop()

            st.metric("EPS (TTM)", f"{result['eps']:.2f}")
            st.metric("Industry Avg P/E", f"{result['industry_pe_avg']:.2f}")
            st.metric("Current Stock Price", f"${result['current_price']:.2f}" if result['current_price'] else "N/A")

            st.subheader("Recommendation")
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
