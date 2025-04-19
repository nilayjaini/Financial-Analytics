import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import urllib.parse

st.set_page_config(layout="wide")
st.title("🏢 Company Snapshot")

ticker_input = st.text_input("Enter a ticker symbol", "DELL")

if ticker_input:
    ticker = yf.Ticker(ticker_input.upper())

    try:
        stock_info = ticker.info

        # Header Info
        company_name = stock_info.get("longName", ticker_input.upper())
        website = stock_info.get("website", "")
        domain = urllib.parse.urlparse(website).netloc
        clearbit_logo = f"https://logo.clearbit.com/{domain}" if domain else None

        col1, col2 = st.columns([1, 10])
        with col1:
            if clearbit_logo:
                st.image(clearbit_logo, width=50)
        with col2:
            st.subheader(f"{company_name} ({ticker_input.upper()})")

        # Interval selector
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

        # Historical price chart
        if selected_interval == "1d":
            hist = ticker.history(period="1d", interval="5m")
        else:
            hist = ticker.history(period=selected_interval)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', name='Close'))
        fig.update_layout(title=f"{ticker_input.upper()} Stock Price - {interval_label}",
                          xaxis_title="Date", yaxis_title="Price ($)", height=350)
        st.plotly_chart(fig, use_container_width=True)

        # Key Financials
        st.markdown("### 🧾 Key Financials")
        open_price = stock_info.get("open", 0)
        high = stock_info.get("dayHigh", 0)
        low = stock_info.get("dayLow", 0)
        price = stock_info.get("regularMarketPrice", 0)
        market_cap = stock_info.get("marketCap", 0)
        pe_ratio = stock_info.get("trailingPE", "N/A")
        div_yield = stock_info.get("dividendYield")
        div_yield_display = f"{div_yield*100:.2f}%" if div_yield and div_yield < 1 else "N/A"
        week52_high = stock_info.get("fiftyTwoWeekHigh", "N/A")
        week52_low = stock_info.get("fiftyTwoWeekLow", "N/A")
        earnings_date = stock_info.get("earningsDate", ["N/A"])[0]

        st.markdown("""
            <style>
            .metric-table { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; padding: 10px; }
            .metric-item { border: 1px solid #ddd; border-radius: 6px; padding: 10px; text-align: center; background-color: #fafafa; }
            .metric-item b { font-size: 16px; }
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
        st.error("Could not load data")
        st.exception(e)
