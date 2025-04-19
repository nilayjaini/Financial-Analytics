import streamlit as st
import yfinance as yf

st.set_page_config(layout="wide")
st.title("🔍 Fundamental Analysis")

ticker_input = st.text_input("Enter a ticker symbol", "DELL")

if ticker_input:
    ticker = yf.Ticker(ticker_input.upper())
    info = ticker.info

    st.markdown(f"### {info.get('longName', ticker_input.upper())} ({ticker_input.upper()})")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Income Statement", "📉 Balance Sheet", "💵 Cash Flow", "📈 Growth & Ratios"])

    # ========== Income Statement ==========
    with tab1:
        st.subheader("📊 Key Income Metrics")
        st.metric("Revenue (TTM)", f"${info.get('totalRevenue', 0)/1e9:.2f}B")
        st.metric("Gross Profit (TTM)", f"${info.get('grossProfits', 0)/1e9:.2f}B")
        st.metric("EBITDA", f"${info.get('ebitda', 0)/1e9:.2f}B")
        st.metric("Net Income (TTM)", f"${info.get('netIncomeToCommon', 0)/1e9:.2f}B")
        st.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.2f}%")

    # ========== Balance Sheet ==========
    with tab2:
        st.subheader("📉 Key Balance Sheet Metrics")
        st.metric("Total Assets", f"${info.get('totalAssets', 0)/1e9:.2f}B")
        st.metric("Total Liabilities", f"${info.get('totalLiab', 0)/1e9:.2f}B")
        st.metric("Total Debt", f"${info.get('totalDebt', 0)/1e9:.2f}B")
        st.metric("Current Ratio", f"{info.get('currentRatio', 0):.2f}")
        st.metric("Book Value per Share", f"${info.get('bookValue', 0):.2f}")

    # ========== Cash Flow ==========
    with tab3:
        st.subheader("💵 Key Cash Flow Metrics")
        st.metric("Operating Cash Flow (TTM)", f"${info.get('operatingCashflow', 0)/1e9:.2f}B")
        st.metric("Free Cash Flow", f"${info.get('freeCashflow', 0)/1e9:.2f}B")
        st.metric("CapEx", f"${info.get('capitalExpenditures', 0)/1e9:.2f}B")
        st.metric("Levered FCF Margin", f"{(info.get('freeCashflow', 0)/info.get('totalRevenue', 1))*100:.2f}%")

    # ========== Growth & Ratios ==========
    with tab4:
        st.subheader("📈 Growth & Valuation Multiples")
        st.metric("Trailing P/E", f"{info.get('trailingPE', 0):.2f}")
        st.metric("Forward P/E", f"{info.get('forwardPE', 0):.2f}")
        st.metric("PEG Ratio", f"{info.get('pegRatio', 0):.2f}")
        st.metric("Price to Sales (TTM)", f"{info.get('priceToSalesTrailing12Months', 0):.2f}")
        st.metric("Price to Book", f"{info.get('priceToBook', 0):.2f}")
        st.metric("Return on Equity", f"{info.get('returnOnEquity', 0)*100:.2f}%")
        st.metric("Return on Assets", f"{info.get('returnOnAssets', 0)*100:.2f}%")
        st.metric("Revenue Growth (YoY)", f"{info.get('revenueGrowth', 0)*100:.2f}%")
        st.metric("Earnings Growth (YoY)", f"{info.get('earningsGrowth', 0)*100:.2f}%")

    st.caption("📌 Financial data sourced from Yahoo Finance via yfinance")

