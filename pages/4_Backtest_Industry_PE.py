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
        industry = company_data.loc[idx, "Industry"] if "Industry" in company_data.columns else "N/A"

        st.markdown(f"**Industry:** {industry}")
        st.markdown(f"**Competitors:** {', '.join(peers)}")

        # ── Median P/E for peers (2024) ────────────────────────────────
        pe_ratio = price_data.divide(eps_data)
        pe_ratio = pe_ratio.mask((pe_ratio <= 0) | pe_ratio.isna())
        pe_ratio["gsubind"] = gsubind_data.values
        peer_pe_ratios = pe_ratio.loc[peer_indices]
        valid_peer_pe = peer_pe_ratios[2024].dropna()

        eps_2024 = eps_data.loc[idx, 2024]

        # ✅ Fetch current market price from yfinance
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
        c2.metric("Industry Median P/E", f"{industry_pe_avg:.2f}" if not np.isnan(industry_pe_avg) else "N/A")
        c3.metric("Current Price", f"${current_price:.2f}" if not np.isnan(current_price) else "N/A")

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
            ax.hlines(1, implied_price_min, implied_price_max, color="gray", linewidth=10, alpha=0.4)
            ax.vlines(implied_price_avg, 0.9, 1.1, color="blue", linewidth=2, label="Avg Implied Price")
            ax.plot(current_price, 1, "ro", markersize=10, label="Current Price")
            ax.text(implied_price_min, 1.15, f"Low:  ${implied_price_min:.2f}", ha="center", fontsize=9)
            ax.text(implied_price_avg, 1.27, f"Avg:  ${implied_price_avg:.2f}", ha="center", fontsize=9, color="blue")
            ax.text(implied_price_max, 1.15, f"High: ${implied_price_max:.2f}", ha="center", fontsize=9)
            ax.set_xlim(implied_price_min * 0.85, implied_price_max * 1.15)
            ax.set_ylim(0.8, 1.4)
            ax.axis("off")
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.35), ncol=2)
            st.pyplot(fig)

            gap = ((implied_price_avg - current_price) / implied_price_avg) * 100
            if gap > 0:
                st.caption(f"📉 Current price is **{gap:.1f}% below** the implied valuation average.")
            else:
                st.caption(f"📈 Current price is **{abs(gap):.1f}% above** the implied valuation average.")
        else:
            st.warning("⚠️ Not enough valid peer data to create a proper visualization.")
    else:
        st.error("❌ Ticker not found. Please check your selection.")
