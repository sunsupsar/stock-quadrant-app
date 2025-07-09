import streamlit as st
import pandas as pd
import requests
import json

# -------------------------------------------
# CONFIGURATION
# -------------------------------------------
TIJORI_API_KEY = "54bca8a40bmsh3a8ba8452230a07p17c34djsn05a34956e4af"
TIJORI_HOST = "tijorifinance.p.rapidapi.com"

# Optional: You can extend this list
symbol_map = {
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "RELIANCE": "RELIANCE.NS",
    "ICICIBANK": "ICICIBANK.NS"
}

# -------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------
def get_financials(symbol):
    original_symbol = symbol.strip().upper()
    api_symbol = symbol_map.get(original_symbol, original_symbol + ".NS")

    url = f"https://{TIJORI_HOST}/stocks/fundamentals?symbol={api_symbol}"
    headers = {
        "X-RapidAPI-Key": TIJORI_API_KEY,
        "X-RapidAPI-Host": TIJORI_HOST
    }

    st.write(f"\n📅 Fetching data for: {original_symbol}")
    st.write(f"🌐 API URL: {url}")

    try:
        response = requests.get(url, headers=headers)
        st.write(f"📦 Raw API response for {original_symbol}: {response.text[:500]}...")

        if response.status_code != 200:
            st.warning(f"Failed API call for {original_symbol} (Status {response.status_code})")
            return {
                "Name": original_symbol,
                "PE Ratio": None,
                "Net Margin": None,
                "Quadrant": "Not classified"
            }

        data = response.json()

        pe_ratio = data.get("valuation", {}).get("peRatio")
        net_margin = data.get("profitability", {}).get("netMargin")

        if pe_ratio is None:
            st.warning(f"⚠️ Could not find PE for {original_symbol}")
        if net_margin is None:
            st.warning(f"⚠️ Could not find Net Margin for {original_symbol}")

        quadrant = classify_quadrant(pe_ratio, net_margin)

        return {
            "Name": original_symbol,
            "PE Ratio": pe_ratio,
            "Net Margin": net_margin,
            "Quadrant": quadrant
        }

    except Exception as e:
        st.error(f"❌ Exception while fetching {original_symbol}: {e}")
        return {
            "Name": original_symbol,
            "PE Ratio": None,
            "Net Margin": None,
            "Quadrant": "Not classified"
        }


def classify_quadrant(pe, margin):
    if pe is None or margin is None:
        return "Not classified"
    if pe < 25 and margin > 15:
        return "Q1: Value + High Margin"
    elif pe >= 25 and margin > 15:
        return "Q2: Expensive + High Margin"
    elif pe < 25 and margin <= 15:
        return "Q3: Value + Low Margin"
    else:
        return "Q4: Expensive + Low Margin"


# -------------------------------------------
# MAIN APP
# -------------------------------------------
st.set_page_config(page_title="Indian Stock Quadrant Analyzer", layout="centered")
st.title("📊 Indian Stock Quadrant Analyzer (Tijori API)")

symbols_input = st.text_input("Enter stock symbols like TCS, INFY, HDFCBANK")

if symbols_input:
    symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]
    results = []
    for sym in symbols:
        result = get_financials(sym)
        results.append(result)

    df = pd.DataFrame(results)
    st.subheader("📋 Stock Classification Table")
    st.dataframe(df)

    csv = df.to_csv(index=False)
    st.download_button("📥 Download CSV", csv, "stock_analysis.csv", "text/csv")
