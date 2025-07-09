import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import BytesIO
from bs4 import BeautifulSoup
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
# Screener.in Web Scraper
# ---------------------------
def fetch_html(symbol):
    try:
        url = f"https://www.screener.in/company/{symbol}/consolidated/"
        st.markdown(f"🌐 Fetching URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.text
        else:
            st.warning(f"⚠️ Failed to fetch {symbol}: Status code {resp.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching HTML for {symbol}: {e}")
        st.code(traceback.format_exc())
        return None

def parse_pe_and_margin(html, symbol):
    soup = BeautifulSoup(html, 'lxml')

    pe_ratio = None
    net_margin = None

    try:
        pe_tag = soup.select_one("li:has(span.sub:contains('P/E'))")
        if pe_tag:
            pe_text = pe_tag.get_text(strip=True).replace('P/E', '').strip()
            pe_ratio = float(pe_text)
        else:
            # Alternative extraction
            ratio_block = soup.find("section", class_="company-ratios")
            if ratio_block:
                for li in ratio_block.find_all("li"):
                    if "P/E" in li.text:
                        value = li.text.split()[-1]
                        pe_ratio = float(value.replace(',', ''))
                        break
        if pe_ratio is None:
            st.warning(f"⚠️ Could not find PE label for {symbol}")
    except Exception as e:
        st.warning(f"⚠️ PE parsing error for {symbol}: {e}")

    try:
        ratios_table = soup.find("section", id="ratio")
        if ratios_table:
            rows = ratios_table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if cols and "Net profit margin" in cols[0].text:
                    net_margin_text = cols[1].text.replace('%', '').replace(',', '').strip()
                    if net_margin_text:
                        net_margin = float(net_margin_text)
                    break
        if net_margin is None:
            st.warning(f"⚠️ Could not find Net Margin for {symbol}")
    except Exception as e:
        st.warning(f"⚠️ Net Margin parsing error for {symbol}: {e}")

    return pe_ratio, net_margin

def get_financials(symbol):
    html = fetch_html(symbol)
    if html is None:
        return {"Name": symbol, "PE Ratio": None, "Net Margin": None}
    
    pe, margin = parse_pe_and_margin(html, symbol)
    return {"Name": symbol, "PE Ratio": pe, "Net Margin": margin}

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(page_title="Stock Quadrant Analyzer", layout="wide")
st.title("📊 Indian Stock Quadrant Analyzer (Screener.in)")

st.sidebar.subheader("Enter Stock Codes (e.g., TCS, HDFCBANK, INFY)")
stock_input = st.sidebar.text_area("Stock Codes (comma separated)", "TCS,HDFCBANK,INFY")
stock_codes = [c.strip().upper() for c in stock_input.split(',') if c.strip()]

stock_data = []
for code in stock_codes:
    st.markdown(f"### 📅 Fetching data for: {code}")
    data = get_financials(code)
    st.json(data)
    data["Quadrant"] = get_quadrant(data["Net Margin"], data["PE Ratio"])
    st.markdown(f"🧭 Assigned Quadrant: **{data['Quadrant']}**")
    stock_data.append(data)

df = pd.DataFrame(stock_data)

st.subheader("📋 Stock Classification Table")
st.dataframe(df, use_container_width=True)

excel_file = BytesIO()
df.to_excel(excel_file, index=False)
excel_file.seek(0)
st.download_button("📥 Download Excel", excel_file, file_name="stock_data.xlsx")

st.subheader("🧠 Insight Summary")
summaries = []
for _, row in df.iterrows():
    q = row['Quadrant']
    if "Q" in q:
        if 'Q4' in q:
            summaries.append(f"{row['Name']} is in {q}, suggesting it is a premium valued strong performer.")
        elif 'Q3' in q:
            summaries.append(f"{row['Name']} is in {q}, suggesting it is a potentially undervalued high performer.")
        elif 'Q2' in q:
            summaries.append(f"{row['Name']} is in {q}, suggesting it is a lower margin stock with higher valuation.")
        else:
            summaries.append(f"{row['Name']} is in {q}, suggesting it is a lower margin stock with lower valuation.")
if summaries:
    st.markdown("\n".join(f"- {s}" for s in summaries))
else:
    st.info("ℹ️ No data available for summary.")

st.subheader("📈 Quadrant Visualization")
fig, ax = plt.subplots(figsize=(10, 6))
colors = {'Q1': 'red', 'Q2': 'orange', 'Q3': 'green', 'Q4': 'blue'}
for _, row in df.iterrows():
    q = row["Quadrant"]
    if "Q" in q:
        quad_code = q.split(":")[0]
        ax.scatter(row["PE Ratio"] or 0, row["Net Margin"] or 0, color=colors.get(quad_code, "black"), s=80)
        ax.text((row["PE Ratio"] or 0) + 0.5, (row["Net Margin"] or 0), row["Name"], fontsize=9)
ax.axhline(10, color='gray', linestyle='--')
ax.axvline(15, color='gray', linestyle='--')
ax.set_xlabel("PE Ratio")
ax.set_ylabel("Net Margin (%)")
ax.set_title("Stock Quadrant Map")
st.pyplot(fig)

st.subheader("🔍 Filter Stocks")
min_margin = st.slider("Minimum Net Margin %", 0, 50, 10)
max_pe = st.slider("Maximum PE Ratio", 5, 100, 30)
filtered = df[(df["PE Ratio"] <= max_pe) & (df["Net Margin"].fillna(0) >= min_margin)]
st.dataframe(filtered, use_container_width=True)
