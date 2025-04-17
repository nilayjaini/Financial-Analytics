import streamlit as st
import pandas as pd
import yfinance as yf

st.title(":earth_americas: Apple Stock Valuation")
st.write("We’ll estimate Apple’s value based on analyst earnings forecasts and CAPM.")

# Step 1: Fixed ticker
ticker_symbol = "AAPL"
stock = yf.Ticker(ticker_symbol)

# Step 2: CAPM Inputs
st.subheader("CAPM Inputs")
risk_free_rate = st.number_input("Enter Risk-Free Rate (e.g., 10Y Treasury Yield)", value=0.046, step=0.001)
market_risk_premium = st.number_input("Enter Market Risk Premium", value=0.057, step=0.001)

try:
    # Step 3: Analyst EPS Forecasts
    eps = stock.eps_trend
    eps1 = eps.at['0y', 'current']
    eps2 = eps.at['+1y', 'current']

    st.write(f"**Year 1 EPS =** {eps1:.2f}")
    st.write(f"**Year 2 EPS =** {eps2:.2f}")

    # Step 4: Beta and Required Return
    beta = stock.info.get("beta", 1.0)
    st.write(f"**Stock Beta =** {beta:.3f}")

    re = risk_free_rate + beta * market_risk_premium
    st.write(f"**Required Return (re) =** {re:.4f}")

    # Step 5: Estimate Growth and Value
    g = eps2 / eps1 - 1
    price1 = (
        eps1 / (1 + re) +
        eps2 / ((1 + re)**2) +
        eps2 * (1 + g) / ((1 + re)**2 * (re - 0.03))
    )
    st.write(f"**Predicted Price =** ${price1:.2f}")

    # Step 6: Current Price
    current_price = stock.fast_info.get('lastPrice', None)
    if current_price:
        st.write(f"**Current Stock Price =** ${current_price}")
    else:
        st.warning("Could not fetch current stock price.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
