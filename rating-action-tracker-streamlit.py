import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser

# ---------- Headers to bypass rejections ----------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

# ---------- CRISIL ----------
def fetch_crisil():
    url = "https://www.crisilratings.com/en/home/our-ratings/latest-rating-press-releases.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        results = []
        for item in soup.select("ul.press-release-list li"):
            title = item.get_text(strip=True)
            link = item.find("a")["href"] if item.find("a") else None
            results.append({
                "Agency": "CRISIL",
                "Title": title,
                "Link": link,
                "Date": None
            })
        return results
    except Exception as e:
        print(f"CRISIL fetch failed: {e}")
        return []

# ---------- CARE ----------
def fetch_care():
    url = "https://www.careratings.com/rating-rationale.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        results = []
        rows = soup.select("table tbody tr")
        for row in rows[:20]:  # latest 20 entries
            cols = row.find_all("td")
            if len(cols) >= 2:
                date = cols[0].get_text(strip=True)
                title = cols[1].get_text(strip=True)
                link = cols[1].find("a")["href"] if cols[1].find("a") else None
                results.append({
                    "Agency": "CARE",
                    "Title": title,
                    "Link": link,
                    "Date": date
                })
        return results
    except Exception as e:
        print(f"CARE fetch failed: {e}")
        return []

# ---------- Placeholder for ICRA ----------
def fetch_icra():
    st.info("⚠️ ICRA scraping not yet implemented (JS-heavy site)")
    return []

# ---------- Placeholder for India Ratings ----------
def fetch_indiaratings():
    st.info("⚠️ India Ratings scraping not yet implemented (JS-heavy site)")
    return []

# ---------- Collect all ----------
def get_all_data():
    data = []
    for func in [fetch_crisil, fetch_care, fetch_icra, fetch_indiaratings]:
        agency_name = func.__name__.replace("fetch_", "").upper()
        records = func()
        print(f"{agency_name}: {len(records)} records fetched")
        data.extend(records)
    return pd.DataFrame(data)

# ---------- Streamlit UI ----------
st.title("📉 Credit Rating Actions Tracker")
st.write("Tracks rating changes from CRISIL, CARE, ICRA, and India Ratings.")

if st.button("🔄 Refresh Data"):
    df = get_all_data()
    if not df.empty:
        # Parse dates where possible
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.sort_values(by="Date", ascending=False, na_position="last")

        st.success(f"✅ {len(df)} total records fetched.")
        st.dataframe(df)

        # Download option
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv, "ratings.csv", "text/csv")
    else:
        st.warning("⚠️ No results found. Try again later.")
