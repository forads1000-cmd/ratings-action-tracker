import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from dateutil import parser as dateparser

st.set_page_config(page_title="Rating Action Tracker", layout="wide")

# Define rating order for comparisons
RATING_SCALE = [
    "B-", "B", "B+",
    "BB-", "BB", "BB+",
    "BBB-", "BBB", "BBB+"
]

RATING_REGEX = r"(BBB[+-]?|BB[+-]?|B[+-]?)"

# Helper: parse rating from text
def parse_rating_change(text):
    matches = re.findall(RATING_REGEX, text)
    if len(matches) >= 2:
        return matches[0], matches[1]
    elif len(matches) == 1:
        return None, matches[0]
    return None, None

# Helper: compare ratings
def compare_ratings(old, new):
    try:
        old_idx = RATING_SCALE.index(old)
        new_idx = RATING_SCALE.index(new)
        if new_idx > old_idx:
            return "Upgrade"
        elif new_idx < old_idx:
            return "Downgrade"
    except:
        pass
    return "Unchanged"

# Helper: highlight ratings
def highlight_title(title, move):
    def repl(match):
        rating = match.group(0)
        if move == "Upgrade":
            return f"<span style='color:green;font-weight:bold'>{rating}</span>"
        elif move == "Downgrade":
            return f"<span style='color:red;font-weight:bold'>{rating}</span>"
        return f"<b>{rating}</b>"

    return re.sub(RATING_REGEX, repl, title)

# Helper: parse date
def parse_date(text):
    try:
        return dateparser.parse(text, fuzzy=True).date()
    except:
        return None

# Scrapers for agencies (simplified placeholders)
def fetch_crisil():
    url = "https://www.crisil.com/en/home/newsroom/press-releases.html"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for art in soup.select(".press-release-card")[:15]:
        title = art.get_text(strip=True)
        link = art.find("a")['href'] if art.find("a") else url
        date_text = art.find("span", class_="date")
        date = parse_date(date_text.text) if date_text else None
        old, new = parse_rating_change(title)
        move = compare_ratings(old, new) if new else "Unchanged"
        items.append({"Agency": "CRISIL", "Title": title, "Date": date, "Old": old, "New": new, "Move": move, "Link": link})
    return items

def fetch_icra():
    url = "https://www.icra.in/Rating/PressRelease"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for row in soup.select(".grid tbody tr")[:15]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        date = parse_date(cols[0].get_text(strip=True))
        title = cols[1].get_text(strip=True)
        link = cols[1].find("a")['href'] if cols[1].find("a") else url
        old, new = parse_rating_change(title)
        move = compare_ratings(old, new) if new else "Unchanged"
        items.append({"Agency": "ICRA", "Title": title, "Date": date, "Old": old, "New": new, "Move": move, "Link": link})
    return items

def fetch_care():
    url = "https://www.careratings.com/pressRelease.aspx"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for row in soup.select(".table tbody tr")[:15]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        date = parse_date(cols[0].get_text(strip=True))
        title = cols[1].get_text(strip=True)
        link = cols[1].find("a")['href'] if cols[1].find("a") else url
        old, new = parse_rating_change(title)
        move = compare_ratings(old, new) if new else "Unchanged"
        items.append({"Agency": "CARE", "Title": title, "Date": date, "Old": old, "New": new, "Move": move, "Link": link})
    return items

def fetch_indiaratings():
    url = "https://www.indiaratings.co.in/pressrelease"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for art in soup.select(".pressReleaseContent")[:15]:
        title = art.get_text(strip=True)
        link = art.find("a")['href'] if art.find("a") else url
        date_text = art.find_previous("span", class_="date")
        date = parse_date(date_text.text) if date_text else None
        old, new = parse_rating_change(title)
        move = compare_ratings(old, new) if new else "Unchanged"
        items.append({"Agency": "India Ratings", "Title": title, "Date": date, "Old": old, "New": new, "Move": move, "Link": link})
    return items

# Streamlit UI
st.title("📊 Rating Action Tracker")

if st.button("🔄 Refresh Data"):
    crisil = fetch_crisil()
    icra = fetch_icra()
    care = fetch_care()
    india = fetch_indiaratings()

    all_data = crisil + icra + care + india
    df = pd.DataFrame(all_data)
    df = df.sort_values(by="Date", ascending=False)

    # Sidebar filter
    move_filter = st.sidebar.selectbox("Filter by Rating Action", ["All", "Upgrades", "Downgrades"])
    if move_filter == "Upgrades":
        df = df[df["Move"] == "Upgrade"]
    elif move_filter == "Downgrades":
        df = df[df["Move"] == "Downgrade"]

    # Highlight ratings in title
    df_display = df.copy()
    df_display["Title"] = [highlight_title(t, m) for t, m in zip(df_display["Title"], df_display["Move"])]

    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode("utf-8"), "rating_actions.csv", "text/csv")

else:
    st.info("Click 'Refresh Data' to fetch the latest rating actions.")
