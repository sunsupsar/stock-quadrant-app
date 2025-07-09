import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO

st.set_page_config(page_title="Indian Stock Quadrant Analyzer", layout="wide")

def get_financials(symbol):
    st.write(f"📅 Fetching data for: {symbol}")
    url = f"https://www.screener.in/company/{symbol}/export/"
    st.write(f"🌐 CSV URL: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.warning(f"❌ Failed to fetch data for {symbol} (Status {response.status_code})")
            return {
                "Name": symbol,
                "PE Ratio": None,
                "Net Margin": None,
                "Quadrant": "Not classified"
            }

        df = pd.read_csv(StringIO(response.text))

        pe_row = df[df.iloc[:, 0].str.contains("P/E", na=False)]
        net_margin_row = df[df.iloc[:, 0].str.contains("Net profit margin", na=False)]

        pe_ratio = float(pe_row.iloc[0, 1]) if not pe_row.empty else None
        net_margin = float(net_margin_row.iloc[0, 1]) if not net_margin_row.empty else None

        if pe_ratio is not None:
            st.write(f"📌 PE Ratio for {symbol}: {pe_ratio}")
        else:
            st.warning(f"⚠️ Could not find PE Ratio for {symbol}")

        if net_margin is not None:
            st.write(f"📌 Net Margin for {symbol}: {net_margin}")
        else:
            st.warning(f"⚠️ Could not find Net Margin for {symbol}")

        # Determine quadrant
        if pe_ratio is not None and net_margin is not None:
            if pe_ratio < 20 and net_margin > 15:
                quadrant = "Q1: Value + Quality"
            elif pe_ratio >= 20 and net_margin > 15:
                quadrant = "Q2: Expensive but Profitable"
            elif pe_ratio < 20 and net_margin <= 15:
                quadrant = "Q3: Cheap but Low Margin"
            else:
                quadrant = "Q4: Overvalued + Low Margin"
        else:
            quadrant = "Not classified"

        return {
            "Name": symbol,
            "PE Ratio": pe_ratio,
            "Net Margin": net_margin,
            "Quadrant": quadrant
        }

    except Exception as e:
        st.error(f"❌ Error fetching {symbol}: {e}")
        return {
            "Name": symbol,
            "PE Ratio": None,
            "Net Margin": None,
            "Quadrant": "Not classified"
        }

# --------------------------
# 🚀 Streamlit UI Starts Here
# --------------------------

st.title("📊 Indian Stock Quadrant Analyzer (Screener.in)")

symbols_input = st.text_input("Enter stock symbols (comma-separated):", "TCS, INFY, HDFCBANK")

if st.button("Analyze"):
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    results = [get_financials(symbol) for symbol in symbols]
    df = pd.DataFrame(results)

    st.markdown("### 📋 Stock Classification Table")
    st.dataframe(df, use_container_width=True)

    if not df.empty and df["PE Ratio"].notna().sum() > 0:
        st.markdown("### 📈 Quadrant Scatter Plot")
        fig, ax = plt.subplots()
        colors = {
            "Q1: Value + Quality": "green",
            "Q2: Expensive but Profitable": "blue",
            "Q3: Cheap but Low Margin": "orange",
            "Q4: Overvalued + Low Margin": "red",
            "Not classified": "gray"
        }

        for _, row in df.iterrows():
            if pd.notna(row["PE Ratio"]) and pd.notna(row["Net Margin"]):
                ax.scatter(row["PE Ratio"], row["Net Margin"],
                           label=row["Name"], color=colors.get(row["Quadrant"], "gray"))
                ax.annotate(row["Name"], (row["PE Ratio"], row["Net Margin"]))

        ax.set_xlabel("P/E Ratio")
        ax.set_ylabel("Net Profit Margin (%)")
        ax.grid(True)
        st.pyplot(fig)
