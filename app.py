import streamlit as st
import requests
import pandas as pd

# Title
st.title("📊 Indian Stock Quadrant Analyzer (Tijori API)")

# Input
symbols_input = st.text_input("Enter stock symbols like TCS, INFY, HDFCBANK")

# API Setup
API_URL = "https://tijorifinance.p.rapidapi.com/stocks/fundamentals"
HEADERS = {
    "X-RapidAPI-Key": "54bca8a40bmsh3a8ba8452230a07p17c34djsn05a34956e4af",
    "X-RapidAPI-Host": "tijorifinance.p.rapidapi.com"
}

def get_tijori_financials(symbol):
    url = f"{API_URL}?symbol={symbol}.NS"
    st.write(f"\n📅 Fetching data for: {symbol}")
    st.write(f"🌐 API URL: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        st.write(f"📦 Raw API response for {symbol}: {response.text[:200]}...")
        if response.status_code != 200:
            st.error(f"Failed API call for {symbol} (Status {response.status_code})")
            return None, None

        data = response.json()

        pe_ratio = data.get("pe_ratio")
        net_margin = data.get("net_margin")

        if pe_ratio is None:
            st.warning(f"⚠️ Could not find PE for {symbol}")
        if net_margin is None:
            st.warning(f"⚠️ Could not find Net Margin for {symbol}")

        return pe_ratio, net_margin

    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None, None

def classify_quadrant(pe, margin):
    if pe is None or margin is None:
        return "Not classified"
    if pe >= 25 and margin >= 15:
        return "High PE, High Margin"
    elif pe >= 25 and margin < 15:
        return "High PE, Low Margin"
    elif pe < 25 and margin >= 15:
        return "Low PE, High Margin"
    else:
        return "Low PE, Low Margin"

if symbols_input:
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    results = []

    for symbol in symbols:
        pe, margin = get_tijori_financials(symbol)
        quadrant = classify_quadrant(pe, margin)

        results.append({
            "Name": symbol,
            "PE Ratio": pe,
            "Net Margin": margin,
            "Quadrant": quadrant
        })

    df = pd.DataFrame(results)
    st.subheader("📋 Stock Classification Table")
    st.dataframe(df)

    st.download_button(
        label="📥 Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="stock_quadrants.csv",
        mime="text/csv"
    )
