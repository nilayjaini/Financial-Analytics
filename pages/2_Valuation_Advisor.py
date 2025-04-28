# Load your company_data and pe_ratio_with_gsubind
file_path = 'data/Master data price eps etc.xlsx'
company_data = pd.read_excel(file_path, sheet_name='Company Dta', header=None)
headers = company_data.iloc[3]
company_data.columns = headers
company_data = company_data.iloc[4:].reset_index(drop=True)

ticker_data = company_data['Ticker'].reset_index(drop=True)
gsubind_data = company_data['gsubind'].reset_index(drop=True)

# Peer Lookup Logic
ticker_input = ticker_input.upper()
if ticker_input in ticker_data.values:
    idx = ticker_data[ticker_data == ticker_input].index[0]
    company_gsubind = gsubind_data[idx]
    peer_indices = gsubind_data[gsubind_data == company_gsubind].index
    peers = ticker_data.loc[peer_indices].tolist()
    
    # Display Peers
    st.markdown(f"**Peers (Same gsubind):** {', '.join(peers)}")

    # Calculate Median PE of all peers (you need pe_ratio_with_gsubind loaded here)
    pe_ratio = price_data.divide(eps_data)
    pe_ratio_with_gsubind = pe_ratio.copy()
    pe_ratio_with_gsubind['gsubind'] = gsubind_data.values
    
    peer_pe_ratios = pe_ratio_with_gsubind.loc[peer_indices]
    industry_pe_avg = peer_pe_ratios[2024].median()  # Example: median for 2024

    # Proceed with valuation
    eps = eps_data.loc[idx, 2024]
    current_price = price_data.loc[idx, 2024]
    implied_price = eps * industry_pe_avg

    # Show results
    st.metric("EPS (2024)", f"{eps:.2f}")
    st.metric("Median P/E (Peers)", f"{industry_pe_avg:.2f}")
    st.metric("Current Price (2024)", f"${current_price:.2f}")
    st.metric("Implied Price (Valuation)", f"${implied_price:.2f}")
