import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# ---------------------------
# Quadrant classification logic
# ---------------------------
def get_quadrant(net_margin, pe_ratio):
    if net_margin < 10 and pe_ratio < 15:
        return "Q1: Low margin, Low multiple"
    elif net_margin < 10 and pe_ratio >= 15:
        return "Q2: Low margin, High multiple"
    elif net_margin >= 10 and pe_ratio < 15:
        return "Q3: High margin, Low multiple"
    else:
        return "Q4: High margin, High multiple"

# ---------------------------
# Screener.in API logic
# ---------------------------
def get_screener_data(stock_code):
    try:
        url = f"https://www.screener.in/api/company/{stock_code}/"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"Name": stock_code, "Net Margin": None, "PE Ratio": None}

        data = response.json()
        ratios = data.get("ratios", {})

        pe_ratio = ratios.get("Stock P/E")
        net_margin = ratios.get("Net Profit Margin")

        return {
            "Name": stock_code,
            "Net Margin": float(net_margin) if net_margin else None,
            "PE Ratio": float(pe_ratio) if pe_ratio else None
        }

    except Exception as e:
        return {"Name": stock_code, "Net Margin": None, "PE Ratio": None}

# ---------------------------
# Streamlit app
# ---------------------------
st.set_page_config(page_title="Stock Quadrant Analyzer", layout="wide")
st.title("Indian Stock Quadrant Analyzer")

# Sidebar input
st.sidebar.subheader("Enter Stock Codes (e.g., TCS, HDFCBANK, INFY)")
stock_input = st.sidebar.text_area("Stock Codes (comma separated)", "TCS,HDFCBANK,ZOMATO")
stock_codes = [code.strip().upper() for code in stock_input.split(',') if code.strip()]

# Fetch data from Screener
stock_data = []
for code in stock_codes:
    data = get_screener_data(code)
    st.write(f"🔍 Debug: fetched {data}")
    if data["Net Margin"] and data["PE Ratio"]:
        data["Quadrant"] = get_quadrant(data["Net Margin"], data["PE Ratio"])
    else:
        data["Quadrant"] = "Not found"
    stock_data.append(data)

# Create DataFrame
df = pd.DataFrame(stock_data)

# Show Table
st.subheader("Stock Classification Table")
st.dataframe(df, use_container_width=True)

# Scatter Plot
st.subheader("Quadrant Visualization")

fig, ax = plt.subplots(figsize=(10, 6))
colors = {'Q1': 'red', 'Q2': 'orange', 'Q3': 'green', 'Q4': 'blue'}

for i, row in df.iterrows():
    quadrant = row["Quadrant"]
    if "Q" in quadrant:
        quad_code = quadrant.split(":")[0]
        ax.scatter(row["PE Ratio"], row["Net Margin"], color=colors.get(quad_code, "black"), s=80)
        ax.text(row["PE Ratio"] + 0.5, row["Net Margin"], row["Name"], fontsize=9)

ax.axhline(y=10, color='gray', linestyle='--')
ax.axvline(x=15, color='gray', linestyle='--')
ax.set_xlabel("PE Ratio")
ax.set_ylabel("Net Margin (%)")
ax.set_title("Stock Quadrant Map")
st.pyplot(fig)
