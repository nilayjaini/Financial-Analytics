"""
streamlit_app.py  –  Equity Insight Workbench
Cleaned up with consistent 4-space indentation.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import plotly.graph_objects as go
import urllib.parse

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Valuation & Backtest & Snapshot", layout="wide")

# ─── Data Loading ────────────────────────────────────────────────────────────
file_path = "data/Master data price eps etc.xlsx"


@st.cache_data
def load_data():
    # Company Dta sheet
    df = pd.read_excel(file_path, sheet_name="Company Dta", header=None)
    headers = df.iloc[3]
    df.columns = headers
    company_data = df.iloc[4:].reset_index(drop=True)

    # EPS & Price blocks
    eps_data = company_data.iloc[:, 9:24].apply(pd.to_numeric, errors="coerce")
    price_data = company_data.iloc[:, 24:39].apply(pd.to_numeric, errors="coerce")
    eps_data.columns = list(range(2010, 2025))
    price_data.columns = list(range(2010, 2025))

    # Tickers & sub-industry codes
    ticker_data = company_data["Ticker"].reset_index(drop=True)
    gsubind_data = company_data["gsubind"].reset_index(drop=True)

    # Median PE sheet
    median_pe = pd.read_excel(file_path, sheet_name="Median PE", header=None)
    median_pe_trim = median_pe.iloc[5:, :18].reset_index(drop=True)
    median_pe_trim.columns = [None, None, "gsubind"] + list(range(2010, 2025))
    gsubind_to_median_pe = {
        row["gsubind"]: row[3:].values for _, row in median_pe_trim.iterrows()
    }

    # Analysis sheet → actual prices
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

# ─── How-to banner ───────────────────────────────────────────────────────────
with st.container():
    st.markdown(
        """
### 🚀 Welcome to the **Equity Insight Workbench**

| What do you want to know? | Click this tab |
|---------------------------|----------------|
| **Is the stock cheap or rich *right now*?** | **💸 Valuation Advisor** |
| **Has this model worked in the past?** | **📊 Backtest** |
| **What’s happening with the company & price today?** | **🏢 Company Snapshot** |

1. **Pick a ticker** in the sidebar.  
2. Jump between tabs to answer the questions above.  
3. Use the coloured call-outs and hit-rate scores to guide your next step.
""",
        unsafe_allow_html=True,
    )

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

        # ── Logo & header ────────────────────────────────────────────────
        ticker_obj = yf.Ticker(ticker_input.upper())
        info = ticker_obj.info
        website = info.get("website", "")
        domain = urllib.parse.urlparse(website).netloc
        logo_url = info.get("logo_url") or (
            f"https://logo.clearbit.com/{domain}" if domain else None
        )

        col1, col2 = st.columns([1, 6])
        with col1:
            if logo_url:
                st.image(logo_url, width=50)
        with col2:
            st.subheader(f"Details for: {ticker_input}")

        # ── Peers & industry ────────────────────────────────────────────
        peer_indices = gsubind_data[gsubind_data == company_gsubind].index
        peers = ticker_data.loc[peer_indices].tolist()
        industry = (
            company_data.loc[idx, "Industry"]
            if "Industry" in company_data.columns
            else "N/A"
        )

        st.markdown(f"**Industry:** {industry}")
        st.markdown(f"**Competitors:** {', '.join(peers)}")

        # ── Median P/E for peers (2024) ────────────────────────────────
        pe_ratio = price_data.divide(eps_data)
        pe_ratio = pe_ratio.mask((pe_ratio <= 0) | pe_ratio.isna())
        pe_ratio["gsubind"] = gsubind_data.values
        peer_pe_ratios = pe_ratio.loc[peer_indices]
        valid_peer_pe = peer_pe_ratios[2024].dropna()

        eps_2024 = eps_data.loc[idx, 2024]
        current_price = price_data.loc[idx, 2024]
        try:
            current_price = info.get("regularMarketPrice")
            if current_price is None:
                hist = ticker_obj.history(period="1d")
                current_price = hist["Close"][-1] if not hist.empty else np.nan
        except Exception:
            current_price = np.nan

        eps_valid = (eps_2024 > 0) and not np.isnan(eps_2024)

        if eps_valid and not valid_peer_pe.empty:
            industry_pe_avg = valid_peer_pe.median()
            implied_price_avg = eps_2024 * industry_pe_avg
            implied_price_min = eps_2024 * valid_peer_pe.min()
            implied_price_max = eps_2024 * valid_peer_pe.max()
        else:
            industry_pe_avg = implied_price_avg = implied_price_min = implied_price_max = np.nan

        # ── Key inputs ─────────────────────────────────────────────────
        st.subheader("📊 Key Valuation Inputs")
        c1, c2, c3 = st.columns(3)
        c1.metric("Last Reported EPS", f"{eps_2024:.2f}" if eps_valid else "N/A")
        c2.metric(
            "Industry Median P/E",
            f"{industry_pe_avg:.2f}" if not np.isnan(industry_pe_avg) else "N/A",
        )
        c3.metric(
            "Current Price",
            f"${current_price:.2f}" if not np.isnan(current_price) else "N/A",
        )

        # ── Recommendation ────────────────────────────────────────────
        st.subheader("✅ Recommendation")
        if not np.isnan(implied_price_avg) and implied_price_avg > current_price:
            st.success("📈 Likely Undervalued — Consider Buying")
        elif not np.isnan(implied_price_avg):
            st.warning("📉 Likely Overvalued — Exercise Caution")
        else:
            st.info("ℹ️ Not enough data to provide recommendation.")

        # ── Valuation range viz ───────────────────────────────────────
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

    # Optional: reveal the code
    with st.expander("🖥️  Show backend code"):
        with open(__file__, "r") as f:
            st.code(f.read(), language="python")

# ═════════════════════════════════════════════════════════════════════════════
# Tab 2 – Backtest
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.title("📊 Company Stock Valuation Analysis")

    if ticker_input in ticker_data.values:
        idx = ticker_data[ticker_data == ticker_input].index[0]
        gsubind = gsubind_data[idx]
        industry = company_data.loc[idx, "Industry"]

        # ── Logo & header ────────────────────────────────────────────
        ticker_obj = yf.Ticker(ticker_input.upper())
        info = ticker_obj.info
        website = info.get("website", "")
        domain = urllib.parse.urlparse(website).netloc
        logo_url = info.get("logo_url") or (
            f"https://logo.clearbit.com/{domain}" if domain else None
        )

        col1, col2 = st.columns([1, 6])
        with col1:
            if logo_url:
                st.image(logo_url, width=50)
        with col2:
            st.subheader(f"Details for: {ticker_input}")

        st.write(f"**Industry:** {industry}")

        all_peers = ticker_data[gsubind_data == gsubind].tolist()
        competitors = [t for t in all_peers if t != ticker_input]
        st.write("**Competitors:**", ", ".join(competitors) or "None")

        eps_row = eps_data.loc[idx].mask(eps_data.loc[idx] <= 0)
        median_pe_row = pd.Series(
            gsubind_to_median_pe.get(gsubind, [None] * len(years)), index=years
        )
        model_price = eps_row * median_pe_row
        actual_price = actual_price_data.loc[ticker_input]

        price_df = pd.DataFrame(
            {
                "Year": years,
                "EPS": eps_row.values,
                "Median PE": median_pe_row.values,
                "Model Price": model_price.values,
                "Actual Price": actual_price.values,
            }
        )
        price_df["Prediction"] = np.where(model_price > actual_price, "Up", "Down")

        # ── Interactive price comparison ────────────────────────────
        st.subheader(f"📈 {ticker_input}: Model vs Actual Price (t → t + 1)")
        
        # x-axis for each series
        x_actual = price_df["Year"]                      # t
        y_actual = price_df["Actual Price"]
        
        x_model  = x_actual + 1                          # t + 1
        y_model  = price_df["Model Price"]
        
        import plotly.graph_objects as go
        fig_bt = go.Figure()
        
        # Model (predicted for next year)
        fig_bt.add_trace(
            go.Scatter(
                x=x_model,
                y=y_model,
                mode="lines+markers",
                name="Model (predicted t → t+1)",
                marker=dict(symbol="square"),
                line=dict(width=2),
            )
        )
        
        # Actual (realised in year t)
        fig_bt.add_trace(
            go.Scatter(
                x=x_actual,
                y=y_actual,
                mode="lines+markers",
                name="Actual Price (t)",
                marker=dict(symbol="circle"),
                line=dict(width=2, dash="dash"),
            )
        )
        
        # Layout tweaks
        fig_bt.update_layout(
            height=450,
            xaxis_title="Fiscal Year",
            yaxis_title="Share Price ($)",
            hovermode="x unified",
            xaxis=dict(dtick=1),                 # one tick per year
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            margin=dict(l=40, r=40, t=40, b=40),
        )
        
        st.plotly_chart(fig_bt, use_container_width=True)

        # ── Hit-rate calculation ────────────────────────────────────
        total_predictions = correct_predictions = 0
        for year in range(2010, 2024):
            if pd.isna(model_price.get(year)):
                continue
            model_pred = "Up" if model_price[year] > actual_price[year] else "Down"

            if (year + 1 in actual_price.index) and pd.notna(actual_price.get(year + 1)):
                m1 = "Up" if actual_price[year + 1] > actual_price[year] else "Down"
                if model_pred == m1:
                    correct_predictions += 1
                total_predictions += 1

            if (year + 2 in actual_price.index) and pd.notna(actual_price.get(year + 2)):
                m2 = "Up" if actual_price[year + 2] > actual_price[year] else "Down"
                if model_pred == m2:
                    correct_predictions += 1
                total_predictions += 1

        overall_hit_rate = (
            correct_predictions / total_predictions * 100 if total_predictions else np.nan
        )

        st.subheader("🎯 Overall Prediction Hit Rate Analysis")
        st.markdown(f"**Total Valid Predictions:** {total_predictions}")
        st.markdown(f"**Correct Predictions:** {correct_predictions}")
        if not np.isnan(overall_hit_rate):
            st.success(f"✅ Overall Average Hit Rate: **{overall_hit_rate:.2f}%**")
        else:
            st.warning("Not enough data to calculate hit rate.")

        st.dataframe(price_df, use_container_width=True)

        # ── Final prediction for 2024 + context ──────────────────────
        price_df.set_index("Year", inplace=True)
        if 2024 in price_df.index and not pd.isna(price_df.loc[2024, "Prediction"]):
            pred_2024 = price_df.loc[2024, "Prediction"]
            st.success(f"🔮 Final Prediction for 2024: **{pred_2024}**")

            # 1️⃣ Gap %
            model_24 = price_df.loc[2024, "Model Price"]
            actual_24 = price_df.loc[2024, "Actual Price"]
            gap_pct = (model_24 - actual_24) / actual_24 * 100
            st.markdown(f"• **Model vs Actual Gap:** {gap_pct:.1f}%")

            # 2️⃣ Typical sub-industry error
            errors = []
            for peer_idx in peer_indices:
                peer_actual = actual_price_data.loc[ticker_data[peer_idx]]
                peer_eps = eps_data.loc[peer_idx].mask(eps_data.loc[peer_idx] <= 0)
                peer_model = peer_eps * pd.Series(
                    gsubind_to_median_pe[gsubind], index=years
                )
                for yr in range(2010, 2024):
                    if (
                        pd.notna(peer_model.get(yr))
                        and (yr + 1 in peer_actual.index)
                        and pd.notna(peer_actual.get(yr + 1))
                    ):
                        err = abs(
                            (peer_model[yr] - peer_actual[yr + 1]) / peer_actual[yr + 1]
                        ) * 100
                        errors.append(err)
            if errors:
                conf_band = np.nanmedian(errors)
                st.markdown(f"• **Typical {industry} model error:** ±{conf_band:.1f}%")
            else:
                st.markdown(
                    "• _(Not enough data to compute sub-industry confidence band)_"
                )

            st.caption(
                "🔍 *Note: This is a point-in-time signal based solely on trailing EPS × median PE. "
                "Consider forward-looking estimates, volatility, and macro factors before making any trade.*"
            )
        else:
            st.warning("Prediction for 2024 not available.")

        # ── Industry average hit rate ─────────────────────────────────
        peer_indices = gsubind_data[gsubind_data == gsubind].index
        gsubind_total = gsubind_correct = 0
        for peer_idx in peer_indices:
            peer_tkr = ticker_data[peer_idx]
            if peer_tkr not in actual_price_data.index:
                continue
            peer_eps = eps_data.loc[peer_idx].mask(eps_data.loc[peer_idx] <= 0)
            peer_actual = actual_price_data.loc[peer_tkr]
            peer_median = pd.Series(
                gsubind_to_median_pe.get(gsubind, [None] * len(years)), index=years
            )
            peer_model = peer_eps * peer_median
            for year in range(2010, 2024):
                if pd.isna(peer_model.get(year)):
                    continue
                peer_pred = "Up" if peer_model[year] > peer_actual[year] else "Down"

                if (
                    year + 1 in peer_actual.index
                    and pd.notna(peer_actual.get(year + 1))
                ):
                    n1 = "Up" if peer_actual[year + 1] > peer_actual[year] else "Down"
                    if peer_pred == n1:
                        gsubind_correct += 1
                    gsubind_total += 1

                if (
                    year + 2 in peer_actual.index
                    and pd.notna(peer_actual.get(year + 2))
                ):
                    n2 = "Up" if peer_actual[year + 2] > peer_actual[year] else "Down"
                    if peer_pred == n2:
                        gsubind_correct += 1
                    gsubind_total += 1

        gsubind_hit_rate = (
            gsubind_correct / gsubind_total * 100 if gsubind_total else np.nan
        )
        st.subheader(f"🏆 {industry} Industry Hit Rate Comparison")
        st.markdown(f"**Your Stock Hit Rate:** {overall_hit_rate:.2f}%")
        if not np.isnan(gsubind_hit_rate):
            st.success(f"🏆 Industry Average Hit Rate: **{gsubind_hit_rate:.2f}%**")
        else:
            st.warning("Not enough data for gsubind hit rate.")
        st.markdown(
            f"""
**What this means:**  
This number (📊 **{gsubind_hit_rate:.2f}%**) is the **average** one-year (and two-year) directional hit rate of our simple EPS×PE
model across *all* members of the **{industry}** industry.  
A higher value here means the model tends to work well for this industry; a lower value suggests it’s closer to a coin-flip.
"""
        )

        # ── Global model accuracy ─────────────────────────────────────
        global_total = global_correct = 0
        for peer_idx in range(len(ticker_data)):
            peer_tkr = ticker_data[peer_idx]
            peer_sub = gsubind_data[peer_idx]
            if peer_tkr not in actual_price_data.index:
                continue
            peer_eps = eps_data.loc[peer_idx].mask(eps_data.loc[peer_idx] <= 0)
            peer_actual = actual_price_data.loc[peer_tkr]
            peer_median = pd.Series(
                gsubind_to_median_pe.get(peer_sub, [None] * len(years)), index=years
            )
            peer_model = peer_eps * peer_median
            for year in range(2010, 2024):
                if pd.isna(peer_model.get(year)):
                    continue
                peer_pred = "Up" if peer_model[year] > peer_actual[year] else "Down"

                if (
                    year + 1 in peer_actual.index
                    and pd.notna(peer_actual.get(year + 1))
                ):
                    nn1 = (
                        "Up"
                        if peer_actual[year + 1] > peer_actual[year]
                        else "Down"
                    )
                    if peer_pred == nn1:
                        global_correct += 1
                    global_total += 1

                if (
                    year + 2 in peer_actual.index
                    and pd.notna(peer_actual.get(year + 2))
                ):
                    nn2 = (
                        "Up"
                        if peer_actual[year + 2] > peer_actual[year]
                        else "Down"
                    )
                    if peer_pred == nn2:
                        global_correct += 1
                    global_total += 1

        global_hit_rate = (
            global_correct / global_total * 100 if global_total else np.nan
        )
        st.subheader(
            "🌍 Overall Model Accuracy (All Stocks considered in the Prototype Universe)"
        )
        if not np.isnan(global_hit_rate):
            st.success(f"🌟 Global Model Accuracy: **{global_hit_rate:.2f}%**")
        else:
            st.warning("Not enough data to calculate global model accuracy.")
        st.markdown(
            f"""
**Why this matters:**  
The **Global Model Accuracy** of **{global_hit_rate:.2f}%** measures how often our simple EPS × PE
price-direction model would have correctly predicted next-year (and two-year) moves if applied to **every single stock** in our prototype universe.
"""
        )
    else:
        st.error("❌ Ticker not found. Please check your selection.")

# ═════════════════════════════════════════════════════════════════════════════
# Tab 3 – Company Snapshot
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.title("🏢 Company Snapshot")

    if ticker_input in ticker_data.values:
        ticker = yf.Ticker(ticker_input.upper())
        try:
            info = ticker.info
            company_name = info.get("longName", ticker_input.upper())
            website = info.get("website", "")
            domain = urllib.parse.urlparse(website).netloc
            logo_url = info.get("logo_url") or (
                f"https://logo.clearbit.com/{domain}" if domain else None
            )

            col1, col2 = st.columns([1, 10])
            with col1:
                if logo_url:
                    st.image(logo_url, width=50)
            with col2:
                st.subheader(f"{company_name} ({ticker_input.upper()})")

            # ── Price chart range selector ───────────────────────────
            interval_map = {
                "1 Day": "1d",
                "5 Days": "5d",
                "1 Month": "1mo",
                "6 Months": "6mo",
                "YTD": "ytd",
                "1 Year": "1y",
                "5 Years": "5y",
                "Max": "max",
            }
            interval_label = st.selectbox(
                "📈 Select Time Range", list(interval_map.keys()), index=0
            )
            selected_interval = interval_map[interval_label]
            hist = (
                ticker.history(period="1d", interval="5m")
                if selected_interval == "1d"
                else ticker.history(period=selected_interval)
            )

            fig_snap = go.Figure()
            fig_snap.add_trace(
                go.Scatter(
                    x=hist.index, y=hist["Close"], mode="lines", name="Close Price"
                )
            )
            fig_snap.update_layout(
                title=f"{ticker_input.upper()} Stock Price - {interval_label}",
                height=350,
                xaxis_title="Date",
                yaxis_title="Price ($)",
            )
            st.plotly_chart(fig_snap, use_container_width=True)

            # ── Key metrics grid ────────────────────────────────────
            st.markdown("### 🧾 Key Metrics")

            def safe_fmt(val, pct=False):
                if val is None or val == "N/A":
                    return "N/A"
                return (
                    f"{val*100:.2f}%"
                    if pct
                    else f"${val:.2f}"
                    if isinstance(val, (int, float))
                    else val
                )

            grid_data = [
                ("Open", safe_fmt(info.get("open"))),
                ("High", safe_fmt(info.get("dayHigh"))),
                ("Low", safe_fmt(info.get("dayLow"))),
                ("Current", safe_fmt(info.get("regularMarketPrice"))),
                ("Mkt Cap", f"${info.get('marketCap', 0)/1e9:.2f}B"),
                ("P/E Ratio", info.get("trailingPE", "N/A")),
                ("Div Yield", safe_fmt(info.get("dividendYield"), pct=True)),
                ("52-wk High", safe_fmt(info.get("fiftyTwoWeekHigh"))),
                ("52-wk Low", safe_fmt(info.get("fiftyTwoWeekLow"))),
            ]

            st.markdown(
                """
<style>
.metric-table {display:grid;grid-template-columns:repeat(4,1fr);gap:10px;border:1px solid #eee;border-radius:8px;}
.metric-item {border:1px solid #ddd;border-radius:6px;padding:10px;text-align:center;font-size:14px;background:#fafafa;}
.metric-item b {font-size:16px;}
</style>
""",
                unsafe_allow_html=True,
            )

            html = (
                "<div class='metric-table'>"
                + "".join(
                    [
                        f"<div class='metric-item'><b>{k}</b><br>{v}</div>"
                        for k, v in grid_data
                    ]
                )
                + "</div>"
            )
            st.markdown(html, unsafe_allow_html=True)

            # ── Company overview ────────────────────────────────────
            st.markdown("### 🏢 Company Overview")
            st.info(info.get("longBusinessSummary", "No description available."))
            st.markdown(f"📅 **Next Earnings Date**: {info.get('earningsDate', ['N/A'])[0]}")
            st.caption("📌 Data powered by Yahoo Finance")

        except Exception as e:
            st.error("Could not load company data.")
            st.exception(e)
    else:
        st.error("❌ Ticker not found. Please check your selection.")
