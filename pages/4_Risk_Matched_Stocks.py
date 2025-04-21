import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse

st.set_page_config(layout="wide")
st.title("🧠 Risk-Matched Stocks")

ticker_input = st.text_input("Enter a ticker symbol", "DELL")

if ticker_input:
    st.markdown("""
    This tool suggests stocks with **similar systematic risk exposure** based on:
    - Market Risk (Beta)
    - Size Risk (Market Cap)
    - Value Risk (P/B Ratio)
    """)

    try:
        # Step 1: Build universe dynamically (top 100 tickers for example purpose)
        universe_tickers = ["AAPL", "MSFT", "GOOGL", "META", "TSLA", "NVDA", "AMZN", "ORCL",
                            "IBM", "INTC", "CSCO", "DELL", "HPQ", "WMT", "TGT"]

        def get_metrics(ticker):
            try:
                info = yf.Ticker(ticker).info
                return {
                    "Ticker": ticker,
                    "Beta": info.get("beta", None),
                    "MarketCap": info.get("marketCap", None),
                    "PB_Ratio": info.get("priceToBook", None)
                }
            except:
                return None

        data = [get_metrics(tkr) for tkr in universe_tickers]
        df = pd.DataFrame([d for d in data if d and all(v is not None for v in d.values())])

        if ticker_input.upper() not in df["Ticker"].values:
            st.warning("Ticker not found in current universe or missing required metrics.")
            st.dataframe(df)
        else:
            df.set_index("Ticker", inplace=True)
            target = df.loc[ticker_input.upper()]
            scaled_df = (df - df.mean()) / df.std()
            target_scaled = scaled_df.loc[ticker_input.upper()]
            distances = scaled_df.drop(ticker_input.upper()).apply(
                lambda row: ((row - target_scaled) ** 2).sum() ** 0.5, axis=1
            )
            closest = distances.nsmallest(3).index.tolist()

            result_df = df.loc[closest].copy()
            result_df["Distance"] = distances[closest]
            result_df.reset_index(inplace=True)

            st.subheader("📋 Closest Matches by Risk Profile")
            st.dataframe(result_df, use_container_width=True)
            st.caption("Matched based on similarity in Beta, Market Cap, and P/B Ratio.")

            # Generate recommendations based on similarity
            st.markdown("### 💡 Analyst Insight")
            recommendations = []
            for _, row in result_df.iterrows():
                if row["Distance"] < 1:
                    rec = f"🔹 **{row['Ticker']}** has a very close risk profile and can be a potential alternative if you're looking to diversify without drastically altering your portfolio risk exposure."
                else:
                    rec = f"🔹 **{row['Ticker']}** is somewhat similar in risk profile but may differ more significantly on one or more dimensions. Review fundamentals before substituting."
                recommendations.append(rec)
            for rec in recommendations:
                st.markdown(rec)

    except Exception as e:
        st.error("Failed to compute risk-matched stocks.")
        st.exception(e)
