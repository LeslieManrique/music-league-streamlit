import pandas as pd
import plotly.express as px
import streamlit as st

# Load data
votes = pd.read_csv("votes.csv")
submissions = pd.read_csv("submissions.csv")
rounds = pd.read_csv("rounds.csv")
competitors = pd.read_csv("competitors.csv")

# --- Preprocess Submissions ---
# Use only the first artist (ignores features, splits on commas)
submissions["Primary Artist"] = submissions["Artist(s)"].apply(lambda x: str(x).split(",")[0].strip())

# Most submitted primary artists
top_artists = submissions["Primary Artist"].value_counts().reset_index()
top_artists.columns = ["Artist", "Submission Count"]

# Most submitted songs
top_songs = submissions["Title"].value_counts().reset_index()
top_songs.columns = ["Song", "Submission Count"]

# Player leaderboard
votes_with_submitter = votes.merge(submissions[["Spotify URI", "Submitter ID"]], on="Spotify URI")
votes_with_submitter = votes_with_submitter.merge(competitors, left_on="Submitter ID", right_on="ID")
player_leaderboard = votes_with_submitter.groupby("Name")["Points Assigned"].sum().reset_index()
player_leaderboard.columns = ["Username", "Total Points"]
player_leaderboard = player_leaderboard.sort_values(by="Total Points", ascending=False)

# --- Streamlit Layout ---
st.title("🎵 Music League Dashboard")

st.header("🏆 Player Leaderboard")
fig1 = px.bar(player_leaderboard.head(10), x="Total Points", y="Username", orientation="h")
st.plotly_chart(fig1)

st.header("🎤 Most Submitted Primary Artists")
fig2 = px.bar(top_artists.head(10), x="Submission Count", y="Artist", orientation="h")
st.plotly_chart(fig2)

st.header("🎶 Most Submitted Songs")
fig3 = px.bar(top_songs.head(10), x="Submission Count", y="Song", orientation="h")
st.plotly_chart(fig3)



# --- Wide Table for Interactive Filtering ---
# Get round names
round_map = rounds.set_index("ID")["Name"]
submitter_map = competitors.set_index("ID")["Name"]

# Merge all necessary info
summary_df = submissions.copy()
summary_df["Round Name"] = summary_df["Round ID"].map(round_map)
summary_df["Username"] = summary_df["Submitter ID"].map(submitter_map)
summary_df["Song Name"] = summary_df["Title"]
summary_df["Artist Name"] = summary_df["Artist(s)"]

# Use only first artist for summary as well
summary_df["Artist Name"] = summary_df["Artist Name"].apply(lambda x: str(x).split(",")[0].strip())

# Merge vote count
vote_counts = votes.groupby("Spotify URI")["Points Assigned"].sum().reset_index()
vote_counts.columns = ["Spotify URI", "Number of Votes"]
summary_df = summary_df.merge(vote_counts, on="Spotify URI", how="left").fillna({"Number of Votes": 0})
summary_df["Number of Votes"] = summary_df["Number of Votes"].astype(int)

# Select and reorder columns
summary_table = summary_df[["Round Name", "Username", "Song Name", "Artist Name", "Number of Votes"]]

# --- Filters ---
st.header("🔎 Explore Submissions")
with st.expander("Filter table"):
    selected_user = st.selectbox("Filter by Username", ["All"] + sorted(summary_table["Username"].dropna().unique()))
    selected_round = st.selectbox("Filter by Round", ["All"] + sorted(summary_table["Round Name"].dropna().unique()))

# Apply filters
filtered_table = summary_table.copy()
if selected_user != "All":
    filtered_table = filtered_table[filtered_table["Username"] == selected_user]
if selected_round != "All":
    filtered_table = filtered_table[filtered_table["Round Name"] == selected_round]

st.dataframe(filtered_table, use_container_width=True)

st.markdown("---")
st.markdown("Made with 💜 by Leslie & ChatGPT")
