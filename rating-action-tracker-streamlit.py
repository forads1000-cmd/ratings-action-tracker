# rating_tracker.py
import streamlit as st
import pandas as pd
import feedparser
from dateutil import parser as dateparser

# CARE Ratings RSS feed for Rating Rationales
CARE_FEED_URL = "https://www.careratings.com/rss/RR.xml"

# Function to fetch and parse CARE RSS feed
def fetch_care_ratings():
    feed = feedparser.parse(CARE_FEED_URL)
    records = []
    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        published = entry.get("published", "")
        try:
            date = dateparser.parse(published).date()
        except Exception:
            date = None

        # Detect upgrade / downgrade / reaffirmation
        action = None
        if "upgrade" in title.lower():
            action = "Upgrade"
        elif "downgrade" in title.lower():
            action = "Downgrade"
        elif "reaffirm" in title.lower():
            action = "Reaffirmed"

        records.append({
            "Agency": "CARE",
            "Title": title,
            "Date": date,
            "Action": action,
            "Link": link,
        })

    return pd.DataFrame(records)

# Streamlit app
st.set_page_config(page_title="Rating Action Tracker", layout="wide")

st.title("📊 Rating Action Tracker (Pilot Version)")
st.write("Currently tracking **CARE Ratings** (via RSS feed).")

if st.button("🔄 Refresh Data"):
    df = fetch_care_ratings()
    if df.empty:
        st.warning("⚠️ No records found.")
    else:
        df = df.sort_values(by="Date", ascending=False)

        # Filters
        action_filter = st.multiselect("Filter by Action", ["Upgrade", "Downgrade", "Reaffirmed"], default=[])
        if action_filter:
            df = df[df["Action"].isin(action_filter)]

        # Show results
        st.dataframe(df, use_container_width=True)

        # Download option
        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", data=csv, file_name="care_rating_actions.csv", mime="text/csv")
else:
    st.info("Click **Refresh Data** to load the latest rating actions.")
