# rating_action_tracker_streamlit.py

import streamlit as st
import pandas as pd
import requests
import feedparser
from dateutil import parser as dateparser
import re

# -----------------------------
# Utility functions
# -----------------------------

def extract_rating_change(text):
    """Detect rating actions in text (upgrade/downgrade + ratings around B/BB/BBB)."""
    ratings_pattern = r"(B-|B\+?|BB-|BB\+?|BBB-|BBB\+?)"
    old_new_pattern = rf"({ratings_pattern}).*?({ratings_pattern})"

    action = None
    old_rating, new_rating = None, None

    text_lower = text.lower()
    if "upgrade" in text_lower or "revised upwards" in text_lower:
        action = "Upgrade"
    elif "downgrade" in text_lower or "revised downwards" in text_lower:
        action = "Downgrade"

    match = re.search(old_new_pattern, text, re.IGNORECASE)
    if match:
        old_rating, new_rating = match.group(1), match.group(2)

    return action, old_rating, new_rating


# -----------------------------
# Agency scrapers (RSS/API)
# -----------------------------

def fetch_crisil():
    """Fetch latest CRISIL rating press releases from RSS feed."""
    url = "https://www.crisil.com/en/home/rss/press-releases.rss"
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:30]:
            action, old_rating, new_rating = extract_rating_change(entry.title + " " + entry.get("summary", ""))
            results.append({
                "Agency": "CRISIL",
                "Date": dateparser.parse(entry.published).date() if "published" in entry else None,
                "Title": entry.title,
                "Link": entry.link,
                "Action": action,
                "Old Rating": old_rating,
                "New Rating": new_rating,
            })
        return results
    except Exception as e:
        st.error(f"CRISIL fetch failed: {e}")
        return []


def fetch_care():
    """Fetch latest CARE Ratings press releases from RSS feed."""
    url = "https://www.careratings.com/rss-feed-rationale.aspx"
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:30]:
            action, old_rating, new_rating = extract_rating_change(entry.title + " " + entry.get("summary", ""))
            results.append({
                "Agency": "CARE",
                "Date": dateparser.parse(entry.published).date() if "published" in entry else None,
                "Title": entry.title,
                "Link": entry.link,
                "Action": action,
                "Old Rating": old_rating,
                "New Rating": new_rating,
            })
        return results
    except Exception as e:
        st.error(f"CARE fetch failed: {e}")
        return []


def fetch_icra():
    st.warning("ICRA scraping not yet implemented (JS-heavy site)")
    return []


def fetch_india_ratings():
    st.warning("India Ratings scraping not yet implemented (JS-heavy site)")
    return []


# -----------------------------
# Streamlit App
# -----------------------------

st.set_page_config(page_title="Ratings Action Tracker", layout="wide")

st.title("📊 Ratings Action Tracker")
st.markdown("Track recent **rating upgrades/downgrades** around the B, BB, BBB levels from major Indian rating agencies.")

st.sidebar.header("Filters")
filter_action = st.sidebar.radio("Show only:", ["All", "Upgrades", "Downgrades"])
if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()

@st.cache_data(ttl=900)  # cache for 15 min
def load_data():
    results = []
    results.extend(fetch_crisil())
    results.extend(fetch_care())
    results.extend(fetch_icra())
    results.extend(fetch_india_ratings())
    df = pd.DataFrame(results)
    if not df.empty and "Date" in df.columns:
        df = df.sort_values(by="Date", ascending=False)
    return df

df = load_data()

if df.empty:
    st.warning("⚠️ No results found. Try again later.")
else:
    # Apply filters
    if filter_action != "All":
        df = df[df["Action"] == filter_action]

    # Highlight ratings
    def highlight_action(val):
        if val == "Upgrade":
            return "color: green; font-weight: bold"
        elif val == "Downgrade":
            return "color: red; font-weight: bold"
        return ""

    st.dataframe(
        df[["Date", "Agency", "Action", "Old Rating", "New Rating", "Title", "Link"]]
        .style.applymap(highlight_action, subset=["Action"])
    )
