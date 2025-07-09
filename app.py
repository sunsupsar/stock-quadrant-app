import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# Your FMP API Key
API_KEY = "F2u4eU8RPSA2o7QLTuIXHJMYYzVAkxsY"
BASE_URL = "https://financialmodelingprep.com/api/v3/profile/"
INCOME_URL = "https://financialmodelingprep.com/api/v3/income-statement/"

# Quadrant logic based on PE and Net Margin
def classify_stock(pe_ratio, net_margin):
    if pe_ratio is None or net_margin is None:
        return "Not classified"
    if pe_ratio < 30 and net_margin > 20:
        return "🟩 High Margin & Undervalued"
    elif pe_ratio >= 30 and net_margin > 20:
        return "🟨 High Margin & Overvalued"
    elif pe_ratio < 30 and net_margin <= 20:
        return "🟦 Low Margin & Undervalued"
    else:
        return "🟥 Low Margin & Overvalued"

# Fetch data from FMP
@st.cache_data(show_spinner=False)
def fetch_fmp_data(symbol):
    profile_url = f"{BASE_URL}{symbol}.NS?apikey={API_KEY}"
    income_url = f"{INCOME_URL}{symbol}.NS?limit=1&apikey={API_KEY}"

    profile_res = requests.get(profile_url)
    income_res = requests.get(income_url)

    if profile_res.status_code != 200 or income_res.status_code != 200:
        return None

    try:
        profile_data = profile_res.json()[0]
        income_data = income_res.json()[0]

        pe_ratio = float(profile_data.get("pe", None))
        net_income = float(income_data.get("netIncome", 0))
        revenue = float(income_data.get("revenue", 1))  # Avoid zero division
        net_margin = round((net_income / revenue) * 100, 2)

        return {
            "Name": symbol,
            "PE Ratio": pe_ratio,
            "Net Margin": net_margin,
            "Quadrant": classify_stock(pe_ratio, net_margin)
        }
    except Exception as e:
        return None

# Streamlit UI
st.title("📊 Indian Stock Quadrant Analyzer (via FMP API)")
st.markdown("Analyze Indian stocks by Net Margin and PE Ratio to understand valuation quadrant.")

user_input = st.text_input("Enter stock symbols like TCS, INFY, HDFCBANK", "TCS,INFY,HDFCBANK")
symbols = [s.strip().upper() for s in user_input.split(",") if s.strip()]

if symbols:
    results = []
    for symbol in symbols:
        st.markdown(f"### \U0001F4C5 Fetching data for: {symbol}")
        data = fetch_fmp_data(symbol)
        if data:
            st.json(data)
            results.append(data)
        else:
            st.error(f"❌ Failed to fetch or parse data for {symbol}")

    if results:
        df = pd.DataFrame(results)

        st.markdown("### \U0001F4CB Stock Classification Table")
        st.dataframe(df, use_container_width=True)

        # Plot quadrant
        st.markdown("### \U0001F5FA Stock Quadrant Plot")
        fig, ax = plt.subplots()
        for _, row in df.iterrows():
            if pd.notna(row["PE Ratio"]) and pd.notna(row["Net Margin"]):
                ax.scatter(row["PE Ratio"], row["Net Margin"], label=row["Name"], s=100)
                ax.text(row["PE Ratio"] + 0.5, row["Net Margin"] + 0.5, row["Name"])

        ax.axhline(y=20, color='gray', linestyle='--')
        ax.axvline(x=30, color='gray', linestyle='--')
        ax.set_xlabel("PE Ratio")
        ax.set_ylabel("Net Margin (%)")
        ax.set_title("Valuation Quadrant")
        st.pyplot(fig)
