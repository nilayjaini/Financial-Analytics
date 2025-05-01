import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import requests
import urllib.parse

# ─── Configuration ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Valuation & Backtest & Snapshot", layout="wide")
API_KEY = 'H79D93JHZWLC8I0H'  # Replace with your actual API key

# ─── Data Loading ────────────────────────────────────────────────────────────
file_path = "data/Master data price eps etc.xlsx"

@st.cache_data
def load_data():
    # Load company data
    df = pd.read_excel(file_path, sheet_name="Company Dta", header=None)
    headers = df.iloc[3]
    df.columns = headers
    company_data = df.iloc[4:].reset_index(drop=True)

    # Extract EPS and Price data
    eps_data = company_data.iloc[:, 9:24].apply(pd.to_numeric, errors="coerce")
    price_data = company_data.iloc[:, 24:39].apply(pd.to_numeric, errors="coerce")
    eps_data.columns = list(range(2010, 2025))
    price_data.columns = list(range(2010, 2025))

    # Extract tickers and sub-industry codes
    ticker_data = company_data["Ticker"].reset_index(drop=True)
    gsubind_data = company_data["gsubind"].reset_index(drop=True)

    # Load Median PE data
    median_pe = pd.read_excel(file_path, sheet_name="Median PE", header=None)
    median_pe_trim = median_pe.iloc[5:, :18].reset_index(drop=True)
    median_pe_trim.columns = [None, None, "gsubind"] + list(range(2010, 2025))
    gsubind_to_median_pe = {
        row["gsubind"]: row[3:].values for _, row in median_pe_trim.iterrows()
    }

    # Load actual prices from Analysis sheet
    analysis = pd.read_excel(file_path, sheet_name="Analysis", header=None)
    analysis_trim = analysis.iloc[5:, :40].reset_index(drop=True)
    actual_price = analysis_trim.iloc[:, 24:39].apply(pd.to_numeric, errors="coerce")
    actual_price.columns = list(range(2010, 2025))
    actual_price.index = analysis_trim.iloc[:, 0]

    return (
        company_data,
        eps_data,
        price_data,
        ticker_data,
        gsubind_data,
        gsubind_to_median_pe,
        actual_price,
    )

(
    company_data,
    eps_data,
    price_data,
    ticker_data,
    gsubind_data,
    gsubind_to_median_pe,
    actual_price_data,
) = load_data()
years = list(range(2010, 2025))

# ─── Sidebar Ticker Input ────────────────────────────────────────────────────
ticker_input = st.sidebar.selectbox("Choose a ticker", options=ticker_data.tolist())

# ─── Helper Function to Fetch Current Price ──────────────────────────────────
def fetch_current_price(symbol):
    base_url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': API_KEY
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        price = float(data['Global Quote']['05. price'])
        return price
    except Exception as e:
        st.error(f"Error fetching current price: {e}")
        return np.nan

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(
    ["💸 Valuation Advisor", "📊 Backtest", "🏢 Company Snapshot"]
)

# ═════════════════════════════════════════════════════════════════════════════
# Tab 1 – Valuation Advisor
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    st.title("💸 Valuation Advisor")

    if ticker_input in ticker_data.values:
        idx = ticker_data[ticker_data == ticker_input].index[0]
        company_gsubind = gsubind_data[idx]

        # Peers & industry
        peer_indices = gsubind_data[gsubind_data == company_gsubind].index
        peers = ticker_data.loc[peer_indices].tolist()
        industry = (
            company_data.loc[idx, "Industry"]
            if "Industry" in company_data.columns
            else "N/A"
        )

        st.markdown(f"**Industry:** {industry}")
        st.markdown(f"**Competitors:** {', '.join(peers)}")

        # Median P/E for peers (2024)
        pe_ratio = price_data.divide(eps_data)
        pe_ratio = pe_ratio.mask((pe_ratio <= 0) | pe_ratio.isna())
        pe_ratio["gsubind"] = gsubind_data.values
        peer_pe_ratios = pe_ratio.loc[peer_indices]
        valid_peer_pe = peer_pe_ratios[2024].dropna()

        eps_2024 = eps_data.loc[idx, 2024]
        current_price = fetch_current_price(ticker_input)

        eps_valid = (eps_2024 > 0) and not np.isnan(eps_2024)

        if eps_valid and not valid_peer_pe.empty:
            pe_2024_array = gsubind_to_median_pe.get(company_gsubind, [np.nan] * len(years))
            industry_pe_avg = pe_2024_array[-1]
            implied_price_avg = eps_2024 * industry_pe_avg
            implied_price_min = eps_2024 * valid_peer_pe.min()
            implied_price_max = eps_2024 * valid_peer_pe.max()
        else:
            industry_pe_avg = implied_price_avg = implied_price_min = implied_price_max = np.nan

        # Key inputs
        st.subheader("📊 Key Valuation Inputs")
        c1, c2, c3 = st.columns(3)
        c1.metric("Last Reported EPS", f"{eps_2024:.2f}" if eps_valid else "N/A")
        c2.metric(
            "2024 Median P/E",
            f"{industry_pe_avg:.2f}" if not np.isnan(industry_pe_avg) else "N/A",
        )
        c3.metric(
            "Current Price",
            f"${current_price:.2f}" if not np.isnan(current_price) else "N/A",
        )

        # Recommendation
        st.subheader("✅ Recommendation")
        if not np.isnan(implied_price_avg) and implied_price_avg > current_price:
            st.success("📈 Likely Undervalued — Consider Buying")
        elif not np.isnan(implied_price_avg):
            st.warning("📉 Likely Overvalued — Exercise Caution")
        else:
            st.info("ℹ️ Not enough data to provide recommendation.")

        # Valuation range visualization
        st.subheader("📉 Valuation Range Visualization")
        if eps_valid and not valid_peer_pe.empty:
            fig, ax = plt.subplots(figsize=(10, 2.5))
            ax.hlines(
                1,
                implied_price_min,
                implied_price_max,
                color="gray",
                linewidth=10,
                alpha=0.4,
            )
            ax.vlines(
                implied_price_avg,
                0.9,
                1.1,
                color="blue",
                linewidth=2,
                label="Avg Implied Price",
            )
            ax.plot(
                current_price,
                1,
                "ro",
                markersize=10,
                label="Current Price",
            )
            ax.text(
                implied_price_min,
                1.15,
                f"Low:  ${implied_price_min:.2f}",
                ha="center",
                fontsize=9,
            )
            ax.text(
                implied_price_avg,
                1.27,
                f"Avg:  ${implied_price_avg:.2f}",
                ha="center",
                fontsize=9,
                color="blue",
            )
            ax.text(
                implied_price_max,
                1.15,
                f"High: ${implied_price_max:.2f}",
                ha="center",
                fontsize=9,
            )
            ax.set_xlim(implied_price_min * 0.85, implied_price_max * 1.15)
            ax.set_ylim(0.8, 1.4)
            ax.axis("off")
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.35), ncol=2)
            st.pyplot(fig)

            gap = ((implied_price_avg - current_price) / implied_price_avg) * 100
            if gap > 0:
                st.caption(
                    f"📉 Current price is **{gap:.1f}% below** the implied valuation average."
                )
            else:
                st.caption(
                    f"📈 Current price is **{abs(gap):.1f}% above** the implied valuation average."
                )
        else:
            st.warning("⚠️ Not enough valid peer data to create a proper visualization.")
    else:
        st.error("❌ Ticker not found. Please check your selection.")


with tab2:
    st.title("📊 Backtest")
    st.subheader(f"Backtesting Strategy for {ticker_input}")

    if ticker_input not in actual_price_data.index:
        st.warning("Historical data is not available for this ticker.")
        st.stop()

    idx = ticker_data[ticker_data == ticker_input].index[0]
    gsubind = gsubind_data[idx]

    eps_row = eps_data.loc[idx].mask(eps_data.loc[idx] <= 0)
    median_pe_row = pd.Series(gsubind_to_median_pe.get(gsubind, [None]*len(years)), index=years)
    model_price = eps_row * median_pe_row
    actual_price = actual_price_data.loc[ticker_input]

    price_df = pd.DataFrame({
        "Year": years,
        "EPS": eps_row.values,
        "Median PE": median_pe_row.values,
        "Model Price": model_price.values,
        "Actual Price": actual_price.values
    })
    price_df["Prediction"] = np.where(model_price > actual_price, "Up", "Down")

    st.markdown("### 📈 Model vs Actual Price (t → t+1)")

    x_actual = price_df["Year"]
    y_actual = price_df["Actual Price"]
    x_model = x_actual + 1
    y_model = price_df["Model Price"]

    fig_bt = go.Figure()
    fig_bt.add_trace(go.Scatter(x=x_model, y=y_model, mode="lines+markers", name="Model (t→t+1)"))
    fig_bt.add_trace(go.Scatter(x=x_actual, y=y_actual, mode="lines+markers", name="Actual (t)"))
    fig_bt.update_layout(height=400, xaxis_title="Year", yaxis_title="Price ($)", hovermode="x unified")
    st.plotly_chart(fig_bt, use_container_width=True)

    # Hit rate logic
    total = correct = 0
    for year in range(2010, 2024):
        if pd.isna(model_price.get(year)) or pd.isna(actual_price.get(year)):
            continue
        pred = "Up" if model_price[year] > actual_price[year] else "Down"

        if year + 1 in actual_price.index and pd.notna(actual_price.get(year + 1)):
            actual_move = "Up" if actual_price[year + 1] > actual_price[year] else "Down"
            if pred == actual_move:
                correct += 1
            total += 1

        if year + 2 in actual_price.index and pd.notna(actual_price.get(year + 2)):
            actual_move_2 = "Up" if actual_price[year + 2] > actual_price[year] else "Down"
            if pred == actual_move_2:
                correct += 1
            total += 1

    if total > 0:
        hit_rate = correct / total * 100
        st.success(f"✅ Overall Backtest Hit Rate: {hit_rate:.2f}%")
    else:
        st.warning("Not enough data to compute hit rate.")

    st.dataframe(price_df, use_container_width=True)


with tab3:
    st.title("🏢 Company Snapshot")

    st.markdown(f"### Snapshot for **{ticker_input}**")

    current_price = fetch_current_price(ticker_input)
    idx = ticker_data[ticker_data == ticker_input].index[0]
    industry = company_data.loc[idx, "Industry"] if "Industry" in company_data.columns else "N/A"
    gsubind = gsubind_data[idx]

    st.markdown(f"- **Current Price:** ${current_price:.2f}" if not np.isnan(current_price) else "- **Current Price:** N/A")
    st.markdown(f"- **Industry:** {industry}")
    st.markdown(f"- **Gsubind Code:** {gsubind}")
    st.markdown("---")

    st.markdown("**Note:** This tab uses preloaded Excel data and Alpha Vantage's current price API. No live fundamentals shown due to API limits.")

