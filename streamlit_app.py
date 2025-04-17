import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

st.set_page_config(page_title="Valuation Explorer", layout="centered")
st.title(":moneybag: Stock Valuation Dashboard")
st.caption("Based on Analyst EPS Forecasts + CAPM + Gordon Growth")

# Inputs
ticker_symbol = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT, XOM):", value="XOM")

st.subheader("📊 CAPM Assumptions")
col1, col2 = st.columns(2)
with col1:
    risk_free_rate = st.number_input("Risk-Free Rate (e.g. 10Y Treasury)", value=0.046, step=0.001)
with col2:
    market_risk_premium = st.number_input("Market Risk Premium", value=0.057, step=0.001)

if ticker_symbol:
    stock = yf.Ticker(ticker_symbol)

    try:
        eps = stock.eps_trend
        eps1 = eps.at['0y', 'current']
        eps2 = eps.at['+1y', 'current']
        beta = stock.info.get("beta", 1.0)
        current_price = stock.fast_info.get("lastPrice", None)

        base_re = risk_free_rate + beta * market_risk_premium
        base_g = eps2 / eps1 - 1

        st.markdown(f"""
        **Ticker**: `{ticker_symbol}`  
        **Beta**: `{beta:.3f}`  
        **Year 1 EPS**: `{eps1:.2f}`  
        **Year 2 EPS**: `{eps2:.2f}`  
        **Calculated Growth (g)**: `{base_g:.4f}`  
        **Base Required Return (re)**: `{base_re:.4f}`  
        """)

        st.subheader("🎛️ Sensitivity Sliders")
        re = st.slider("Adjust Required Return (re)", 0.02, 0.15, value=round(base_re, 4), step=0.001)
        g = st.slider("Adjust Long-Term Growth Rate (g)", 0.00, 0.15, value=round(base_g, 4), step=0.001)

        # Valuation Formula
        def compute_valuation(eps1, eps2, re, g):
            try:
                return (
                    eps1 / (1 + re) +
                    eps2 / ((1 + re)**2) +
                    eps2 * (1 + g) / ((1 + re)**2 * (re - 0.03))
                )
            except:
                return None

        predicted_price = compute_valuation(eps1, eps2, re, g)
        st.metric(label="💰 Predicted Stock Price", value=f"${predicted_price:.2f}")
        if current_price:
            st.metric(label="📈 Current Market Price", value=f"${current_price:.2f}")

        # --- Sensitivity Analysis DataFrames ---
        st.subheader("📉 Sensitivity Analysis")

        # Varying re
        re_range = [round(x, 3) for x in list(pd.Series([re - 0.02 + i * 0.002 for i in range(21)]))]
        re_sensitivity = pd.DataFrame({
            "Required Return (re)": re_range,
            "Predicted Price": [compute_valuation(eps1, eps2, r, g) for r in re_range]
        })

        fig1, ax1 = plt.subplots()
        ax1.plot(re_sensitivity["Required Return (re)"], re_sensitivity["Predicted Price"])
        ax1.set_xlabel("Required Return (re)")
        ax1.set_ylabel("Predicted Price")
        ax1.set_title("Sensitivity of Price to Required Return")
        st.pyplot(fig1)

        # Varying g
        g_range = [round(x, 3) for x in list(pd.Series([g - 0.02 + i * 0.002 for i in range(21)]))]
        g_sensitivity = pd.DataFrame({
            "Growth Rate (g)": g_range,
            "Predicted Price": [compute_valuation(eps1, eps2, re, growth) for growth in g_range]
        })

        fig2, ax2 = plt.subplots()
        ax2.plot(g_sensitivity["Growth Rate (g)"], g_sensitivity["Predicted Price"])
        ax2.set_xlabel("Growth Rate (g)")
        ax2.set_ylabel("Predicted Price")
        ax2.set_title("Sensitivity of Price to Growth Rate")
        st.pyplot(fig2)

        # --- Downloadable Table ---
        st.download_button(
            label="📥 Download Sensitivity Table (CSV)",
            data=re_sensitivity.to_csv(index=False),
            file_name=f"{ticker_symbol}_sensitivity_re.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Error: {e}")
