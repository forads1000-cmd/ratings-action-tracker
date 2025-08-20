import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dateutil import parser

st.set_page_config(page_title="Rating Action Tracker", layout="wide")

st.title("📉📈 Rating Action Tracker")
st.write("Tracks upgrades/downgrades around B / BB / BBB ratings from CRISIL, ICRA, CARE, India Ratings.")

# ---- Helper function for CRISIL ----
def fetch_crisil():
    url = "https://www.crisilratings.com/mnt/winshare/Ratings/RatingList.html"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            st.warning(f"CRISIL fetch failed: HTTP {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tr")

        records = []
        for row in rows[1:]:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 4:
                try:
                    date_val = parser.parse(cols[1], dayfirst=True).date()
                except:
                    date_val = None
                records.append({
                    "Agency": "CRISIL",
                    "Entity": cols[0],
                    "Date": date_val,
                    "Action": cols[2],
                    "Rating": cols[3],
                })
        st.info(f"✅ CRISIL: {len(records)} records fetched")
        return records
    except Exception as e:
        st.error(f"CRISIL scraping error: {e}")
        return []

# ---- Helper function for ICRA ----
def fetch_icra():
    url = "https://www.icra.in/Rating/PressReleases"  # public rating actions
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            st.warning(f"ICRA fetch failed: HTTP {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tbody tr")

        records = []
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 3:
                try:
                    date_val = parser.parse(cols[0], dayfirst=True).date()
                except:
                    date_val = None
                records.append({
                    "Agency": "ICRA",
                    "Entity": cols[1],
                    "Date": date_val,
                    "Action": cols[2],
                    "Rating": cols[2],  # some ICRA pages combine action + rating
                })
        st.info(f"✅ ICRA: {len(records)} records fetched")
        return records
    except Exception as e:
        st.error(f"ICRA scraping error: {e}")
        return []

# ---- Helper function for CARE ----
def fetch_care():
    url = "https://www.careratings.com/pressRelease"  # public disclosures
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            st.warning(f"CARE fetch failed: HTTP {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tbody tr")

        records = []
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 3:
                try:
                    date_val = parser.parse(cols[0], dayfirst=True).date()
                except:
                    date_val = None
                records.append({
                    "Agency": "CARE",
                    "Entity": cols[1],
                    "Date": date_val,
                    "Action": cols[2],
                    "Rating": cols[2],
                })
        st.info(f"✅ CARE: {len(records)} records fetched")
        return records
    except Exception as e:
        st.error(f"CARE scraping error: {e}")
        return []

# ---- Helper function for India Ratings ----
def fetch_indiaratings():
    url = "https://www.indiaratings.co.in/pressrelease"  # public announcements
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            st.warning(f"India Ratings fetch failed: HTTP {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tbody tr")

        records = []
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 3:
                try:
                    date_val = parser.parse(cols[0], dayfirst=True).date()
                except:
                    date_val = None
                records.append({
                    "Agency": "India Ratings",
                    "Entity": cols[1],
                    "Date": date_val,
                    "Action": cols[2],
                    "Rating": cols[2],
                })
        st.info(f"✅ India Ratings: {len(records)} records fetched")
        return records
    except Exception as e:
        st.error(f"India Ratings scraping error: {e}")
        return []

# ---- Master fetcher ----
def fetch_all():
    all_records = []
    all_records.extend(fetch_crisil())
    all_records.extend(fetch_icra())
    all_records.extend(fetch_care())
    all_records.extend(fetch_indiaratings())
    return pd.DataFrame(all_records)

# ---- Refresh button ----
if st.button("🔄 Refresh Data"):
    df = fetch_all()

    if not df.empty:
        if "Date" in df.columns:
            df = df.sort_values(by="Date", ascending=False)

        # Highlight upgrades/downgrades
        def highlight_action(val):
            if isinstance(val, str):
                if "Upgrade" in val:
                    return "color: green; font-weight: bold"
                elif "Downgrade" in val:
                    return "color: red; font-weight: bold"
            return ""
        
        st.dataframe(df.style.applymap(highlight_action, subset=["Action"]))
        st.download_button("📥 Download CSV", df.to_csv(index=False), "rating_actions.csv")
    else:
        st.warning("⚠️ No results found. Try again later.")
