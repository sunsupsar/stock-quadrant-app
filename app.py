import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import traceback

# ---------------------------
# Quadrant classification logic
# ---------------------------
def get_quadrant(net_margin, pe_ratio):
    if net_margin is None or pe_ratio is None:
        return "Not classified"
    if net_margin < 10 and pe_ratio < 15:
        return "Q1: Low margin, Low multiple"
    elif net_margin < 10 and pe_ratio >= 15:
        return "Q2: Low margin, High multiple"
    elif net_margin >= 10 and pe_ratio < 15:
        return "Q3: High margin, Low multiple"
    else:
        return "Q4: High margin, High multiple"

# ---------------------------
# Screener.in data fetch using updated logic
# ---------------------------
def get_screener_data(stock_code):
    try:
        url = f"https://www.screener.in/company/{stock_code}/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract PE Ratio from top ratios section
        pe_value = None
        pe_label = soup.find("label", string="Stock P/E")
        if pe_label:
            pe_value_str = pe_label.find_next("span").text.strip().replace(",", "")
            pe_value = float(pe_value_str)

        # Extract Net Margin from Profitability section
        net_margin = None
        tables = soup.find_all("table", class_="ranges-table")
        for table in tables:
            if "Net profit margin" in table.text:
                rows = table.find_all("tr")
                for row in rows:
                    if "Net profit margin" in row.text:
                        cells = row.find_all("td")
                        if cells and len(cells) >= 2:
                            margin_str = cells[-1].text.strip().replace("%", "").replace(",", "")
                            net_margin = float(margin_str)
                        break

        return {
            "Name": stock_code,
            "Net Margin": net_margin,
            "PE Ratio": pe_value
        }
    except Exception as e:
        st.error(f"❌ Error fetching {stock_code}: {e}")
        st.code(traceback.format_exc())
        return {
            "Name": stock_code,
            "Net Margin": None,
            "PE Ratio": None
        }

# ---------------------------
# Streamlit app
# ---------------------------
st.set_page_config(page_title="Stock Quadrant Analyzer", layout="wide")
st.title("Indian Stock Quadrant Analyzer")

# Sidebar input
st.sidebar.subheader("Enter Stock Codes (e.g., TCS, HDFCBANK, INFY)")
stock_input = st.sidebar.text_area("Stock Codes (comma separated)", "TCS,HDFCBANK,INFY")
stock_codes = [code.strip().upper() for code in stock_input.split(',') if code.strip()]

# Fetch data with debug
stock_data = []
for code in stock_codes:
    st.markdown(f"### 📥 Fetching data for: `{code}`")
    data = get_screener_data(code)
    st.json(data)
    data["Quadrant"] = get_quadrant(data["Net Margin"], data["PE Ratio"])
    st.markdown(f"🧭 Assigned Quadrant: **{data['Quadrant']}**")
    stock_data.append(data)

# Create DataFrame
df = pd.DataFrame(stock_data)

# Show Table
st.subheader("Stock Classification Table")
st.dataframe(df, use_container_width=True)

# Download Excel
excel_file = BytesIO()
df.to_excel(excel_file, index=False)
excel_file.seek(0)
st.download_button("Download Excel", excel_file, file_name="stock_data.xlsx")

# Analysis Summary
st.subheader("Insight Summary")
summaries = []
for _, row in df.iterrows():
    q = row['Quadrant']
    if "Q" in q:
        if 'Q4' in q:
            summary = f"{row['Name']} is in {q}, suggesting it is a premium valued strong performer."
        elif 'Q3' in q:
            summary = f"{row['Name']} is in {q}, suggesting it is a potentially undervalued high performer."
        elif 'Q2' in q:
            summary = f"{row['Name']} is in {q}, suggesting it is a lower margin stock with higher valuation."
        else:
            summary = f"{row['Name']} is in {q}, suggesting it is a lower margin stock with lower valuation."
        summaries.append(summary)

if summaries:
    st.markdown("\n".join([f"- {s}" for s in summaries]))
else:
    st.info("ℹ️ No data available for summary.")

# Scatter Plot
st.subheader("Quadrant Visualization")
fig, ax = plt.subplots(figsize=(10, 6))
colors = {'Q1': 'red', 'Q2': 'orange', 'Q3': 'green', 'Q4': 'blue'}
for _, row in df.iterrows():
    quadrant = row["Quadrant"]
    if "Q" in quadrant:
        quad_code = quadrant.split(":")[0]
        ax.scatter(row["PE Ratio"], row["Net Margin"] if row["Net Margin"] is not None else 0, 
                   color=colors.get(quad_code, "black"), s=80)
        ax.text(row["PE Ratio"] + 0.5, 
                row["Net Margin"] if row["Net Margin"] is not None else 0, 
                row["Name"], fontsize=9)
ax.axhline(y=10, color='gray', linestyle='--')
ax.axvline(x=15, color='gray', linestyle='--')
ax.set_xlabel("PE Ratio")
ax.set_ylabel("Net Margin (%)")
ax.set_title("Stock Quadrant Map")
st.pyplot(fig)

# Filter control
st.subheader("Filter Stocks")
min_margin = st.slider("Minimum Net Margin %", 0, 50, 10)
max_pe = st.slider("Maximum PE Ratio", 5, 100, 30)
filtered_df = df[(df["PE Ratio"] <= max_pe)]
if "Net Margin" in filtered_df.columns:
    filtered_df = filtered_df[(filtered_df["Net Margin"].fillna(0) >= min_margin)]
st.dataframe(filtered_df, use_container_width=True)
