import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# --- Constants ---
API_KEY = "54bca8a40bmsh3a8ba8452230a07p17c34djsn05a34956e4af"
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "tijorifinance.p.rapidapi.com"
}
TIJORI_BASE_URL = "https://tijorifinance.p.rapidapi.com"

# --- Streamlit App ---
st.title("📊 Indian Stock Quadrant Analyzer (Tijori API)")
st.markdown("Enter stock symbols like `TCS`, `INFY`, `HDFCBANK`")

symbols_input = st.text_input("Enter stock symbols (comma-separated):", "TCS,INFY,HDFCBANK")
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

# --- Helper Function ---
def get_tijori_data(symbol):
    try:
        st.write(f"\n📅 Fetching data for: {symbol}")

        url = f"{TIJORI_BASE_URL}/stock/summary"
        params = {"symbol": symbol}

        response = requests.get(url, headers=HEADERS, params=params)
        st.write(f"📦 Raw API response for {symbol}:", response.text)

        if response.status_code != 200:
            st.warning(f"Failed API call for {symbol} (Status {response.status_code})")
            return None

        data = response.json()
        pe_ratio = data.get("data", {}).get("ratios", {}).get("peRatio")
        net_margin = data.get("data", {}).get("ratios", {}).get("netMargin")

        if pe_ratio is None or net_margin is None:
            st.warning(f"⚠️ Could not find PE or Net Margin for {symbol}")
            return None

        return {
            "Name": symbol,
            "PE Ratio": round(pe_ratio, 2),
            "Net Margin": round(net_margin, 2)
        }

    except Exception as e:
        st.error(f"❌ Exception for {symbol}: {e}")
        return None

# --- Quadrant Assignment ---
def classify_stock(pe, margin):
    if pe is None or margin is None:
        return "Not classified"
    if pe < 25 and margin > 15:
        return "🟩 Value & Quality"
    elif pe >= 25 and margin > 15:
        return "🟨 Expensive but Profitable"
    elif pe < 25 and margin <= 15:
        return "🟦 Cheap but Weak"
    else:
        return "🟥 Overpriced & Weak"

# --- Main Execution ---
results = []

for symbol in symbols:
    data = get_tijori_data(symbol)
    if data:
        data["Quadrant"] = classify_stock(data["PE Ratio"], data["Net Margin"])
    else:
        data = {"Name": symbol, "PE Ratio": None, "Net Margin": None, "Quadrant": "Not classified"}
    results.append(data)

# --- Display Table ---
df = pd.DataFrame(results)
st.markdown("### 📋 Stock Classification Table")
st.dataframe(df, use_container_width=True)

# --- Optional: Scatter Plot ---
if st.checkbox("Show Quadrant Chart") and not df["PE Ratio"].isnull().all():
    fig, ax = plt.subplots()
    for i, row in df.iterrows():
        if pd.notnull(row["PE Ratio"]) and pd.notnull(row["Net Margin"]):
            ax.scatter(row["PE Ratio"], row["Net Margin"], label=row["Name"])
            ax.text(row["PE Ratio"] + 0.5, row["Net Margin"] + 0.5, row["Name"], fontsize=9)
    ax.axhline(15, color='gray', linestyle='--')
    ax.axvline(25, color='gray', linestyle='--')
    ax.set_xlabel("PE Ratio")
    ax.set_ylabel("Net Margin (%)")
    ax.set_title("Stock Quadrant Classification")
    st.pyplot(fig)
