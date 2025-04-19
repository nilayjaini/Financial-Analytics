import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from helpers.peer_lookup import get_peers
from helpers.valuation_logic import analyze_valuation, plot_price_range
import urllib.parse

st.set_page_config(layout="wide")
st.title("📈 Stock Insight Explorer")

ticker_input = st.text_input("Enter a ticker symbol", "DELL")

if ticker_input:
    ticker = yf.Ticker(ticker_input.upper())
    peers, sector, industry = get_peers(ticker_input.upper())

    tab1, tab2 = st.tabs(["📄 Overview", "📊 Recommendations"])

    # ========== OVERVIEW ==========
    with tab1:
        try:
            stock_info = ticker.info

            # Header
            company_name = stock_info.get("longName", ticker_input.upper())
            logo = stock_info.get("logo_url")

            company_name = stock_info.get("longName", ticker_input.upper())
            logo = stock_info.get("logo_url")
            website = stock_info.get("website", "")
            domain = urllib.parse.urlparse(website).netloc
            clearbit_logo = f"https://logo.clearbit.com/{domain}" if domain else None

            col1, col2 = st.columns([1, 10])
            with col1:
                if logo:
                    st.image(logo, width=50)
                elif clearbit_logo:
                    st.image(clearbit_logo, width=50)
            with col2:
                st.subheader(f"{company_name} ({ticker_input.upper()})")

            # Interval dropdown
            interval_map = {
                "1 Day": "1d",
                "5 Days": "5d",
                "1 Month": "1mo",
                "6 Months": "6mo",
                "YTD": "ytd",
                "1 Year": "1y",
                "5 Years": "5y",
                "Max": "max"
            }
            interval_label = st.selectbox("📈 Select Time Range", list(interval_map.keys()), index=0)
            selected_interval = interval_map[interval_label]
            if selected_interval == "1d":
                hist = ticker.history(period="1d", interval="5m")
            else:
                hist = ticker.history(period=selected_interval)
            

            # Plotly Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', name='Close Price'))
            fig.update_layout(title=f"{ticker_input.upper()} Stock Price - {interval_label}",
                              xaxis_title="Date", yaxis_title="Price ($)", height=350)
            st.plotly_chart(fig, use_container_width=True)

            # Financial metrics
            price = stock_info.get("regularMarketPrice", 0)
            open_price = stock_info.get("open", 0)
            high = stock_info.get("dayHigh", 0)
            low = stock_info.get("dayLow", 0)
            market_cap = stock_info.get("marketCap", 0)
            pe_ratio = stock_info.get("trailingPE", "N/A")
            div_yield = stock_info.get("dividendYield")
            div_yield_display = f"{div_yield*100:.2f}%" if div_yield and div_yield < 1 else "N/A"
            week52_high = stock_info.get("fiftyTwoWeekHigh", "N/A")
            week52_low = stock_info.get("fiftyTwoWeekLow", "N/A")
            earnings_date = stock_info.get("earningsDate", ["N/A"])[0]

            # Grid-style layout
            st.markdown("### 🧾 Key Financials")
            st.markdown("""
                <style>
                    .metric-table {
                        display: grid;
                        grid-template-columns: repeat(4, 1fr);
                        gap: 10px;
                        padding: 10px;
                        border: 1px solid #eee;
                        background-color: #fff;
                        border-radius: 8px;
                        margin-bottom: 1rem;
                    }
                    .metric-item {
                        border: 1px solid #ddd;
                        border-radius: 6px;
                        padding: 10px;
                        text-align: center;
                        font-size: 14px;
                        background-color: #fafafa;
                    }
                    .metric-item b {
                        font-size: 16px;
                    }
                </style>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-table">
                    <div class="metric-item"><b>Open</b><br>${open_price:.2f}</div>
                    <div class="metric-item"><b>High</b><br>${high:.2f}</div>
                    <div class="metric-item"><b>Low</b><br>${low:.2f}</div>
                    <div class="metric-item"><b>Current</b><br>${price:.2f}</div>
                    <div class="metric-item"><b>Mkt Cap</b><br>${market_cap/1e9:.2f}B</div>
                    <div class="metric-item"><b>P/E Ratio</b><br>{pe_ratio}</div>
                    <div class="metric-item"><b>Div Yield</b><br>{div_yield_display}</div>
                    <div class="metric-item"><b>52-wk High</b><br>${week52_high}</div>
                    <div class="metric-item"><b>52-wk Low</b><br>${week52_low}</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("### 🏢 Company Overview")
            st.info(stock_info.get("longBusinessSummary", "No description available."))

            st.markdown(f"📅 **Next Earnings Date**: {earnings_date}")
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
