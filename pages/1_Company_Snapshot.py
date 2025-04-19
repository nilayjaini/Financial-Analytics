# 1_Company_Snapshot.py
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
        info = ticker.info
        company_name = info.get("longName", ticker_input.upper())
        website = info.get("website", "")
        domain = urllib.parse.urlparse(website).netloc
        logo = info.get("logo_url") or f"https://logo.clearbit.com/{domain}" if domain else None

        col1, col2 = st.columns([1, 10])
        with col1:
            if logo:
                st.image(logo, width=50)
        with col2:
            st.subheader(f"{company_name} ({ticker_input.upper()})")

        interval_map = {
            "1 Day": "1d", "5 Days": "5d", "1 Month": "1mo", "6 Months": "6mo",
            "YTD": "ytd", "1 Year": "1y", "5 Years": "5y", "Max": "max"
        }
        interval_label = st.selectbox("📈 Select Time Range", list(interval_map.keys()), index=0)
        selected_interval = interval_map[interval_label]
        hist = ticker.history(period="1d", interval="5m") if selected_interval == "1d" else ticker.history(period=selected_interval)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', name='Close Price'))
        fig.update_layout(title=f"{ticker_input.upper()} Stock Price - {interval_label}", height=350, xaxis_title="Date", yaxis_title="Price ($)")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🧾 Key Financials")
        def safe_fmt(val, pct=False):
            if val is None or val == "N/A": return "N/A"
            return f"{val*100:.2f}%" if pct else f"${val:.2f}" if isinstance(val, (int, float)) else val

        grid_data = [
            ("Open", safe_fmt(info.get("open"))),
            ("High", safe_fmt(info.get("dayHigh"))),
            ("Low", safe_fmt(info.get("dayLow"))),
            ("Current", safe_fmt(info.get("regularMarketPrice"))),
            ("Mkt Cap", f"${info.get('marketCap',0)/1e9:.2f}B"),
            ("P/E Ratio", info.get("trailingPE", "N/A")),
            ("Div Yield", safe_fmt(info.get("dividendYield"), pct=True)),
            ("52-wk High", safe_fmt(info.get("fiftyTwoWeekHigh"))),
            ("52-wk Low", safe_fmt(info.get("fiftyTwoWeekLow")))
        ]

        st.markdown("""
        <style>
            .metric-table {display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; border: 1px solid #eee; border-radius: 8px;}
            .metric-item {border: 1px solid #ddd; border-radius: 6px; padding: 10px; text-align: center; font-size: 14px; background: #fafafa;}
            .metric-item b {font-size: 16px;}
        </style>""", unsafe_allow_html=True)
        html = "<div class='metric-table'>" + "".join([f"<div class='metric-item'><b>{k}</b><br>{v}</div>" for k,v in grid_data]) + "</div>"
        st.markdown(html, unsafe_allow_html=True)

        st.markdown("### 🏢 Company Overview")
        st.info(info.get("longBusinessSummary", "No description available."))
        st.markdown(f"📅 **Next Earnings Date**: {info.get('earningsDate', ['N/A'])[0]}")
        st.caption("📌 Data powered by Yahoo Finance")

    except Exception as e:
        st.error("Could not load company data.")
        st.exception(e)
