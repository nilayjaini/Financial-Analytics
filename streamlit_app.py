import streamlit as st
import pandas as pd
import yfinance as yf

st.title(":earth_americas: Stock Performance App")
st.write("Welcome! Let's estimate EPS and price a stock using analyst forecasts and CAPM.")

# Step 1: Input ticker
ticker_symbol = st.text_input("Enter a ticker symbol (e.g., AAPL, MSFT, XOM):", value="XOM")

# Step 2: Input CAPM variables
st.subheader("CAPM Inputs")
risk_free_rate = st.number_input("Enter Risk-Free Rate (e.g., 10Y Treasury Yield)", value=0.046, step=0.001)
market_risk_premium = st.number_input("Enter Market Risk Premium", value=0.057, step=0.001)

if ticker_symbol:
    stock = yf.Ticker(ticker_symbol)

    try:
        # Step 3: Analyst EPS Forecasts
        eps = stock.eps_trend  # Still using your method for continuity (works sometimes)
        eps1 = eps.at['0y', 'current']
        eps2 = eps.at['+1y', 'current']

        st.write(f"**Year 1 EPS =** {eps1:.2f}")
        st.write(f"**Year 2 EPS =** {eps2:.2f}")

        # Step 4: Beta and Required Return
        beta = stock.info.get("beta", 1.0)  # fallback to 1.0 if not found
        st.write(f"**Stock Beta =** {beta:.3f}")

        re = risk_free_rate + beta * market_risk_premium
        st.write(f"**Required Return (re) =** {re:.4f}")

        # Step 5: Estimate growth and calculate value
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
