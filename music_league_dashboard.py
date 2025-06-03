import pandas as pd
import plotly.express as px
import streamlit as st

# purple header bar
st.markdown("""
    <div style="background-color:#9e01c4;padding:1rem 1.5rem;margin-bottom:1.5rem;border-radius:8px">
        <h1 style="color:white;text-align:center;">🎶 Marvel Rivals Waiting Room🎶</h1>
    </div>
""", unsafe_allow_html=True)

# Footer bar
st.markdown("""
    <style>
        footer {
            visibility: hidden;
        }
        .css-cio0dv.egzxvld1 {
            visibility: visible;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #1e1e1e;
            color: #9e01c4;
            text-align: center;
            padding: 0.5rem;
            font-size: 0.85rem;
        }
    </style>
    <div class="css-cio0dv egzxvld1">Made with ❤️ by Leslie & ChatGPT</div>
""", unsafe_allow_html=True)

# Load data
votes = pd.read_csv("votes.csv")
submissions = pd.read_csv("submissions.csv")
rounds = pd.read_csv("rounds.csv")
competitors = pd.read_csv("competitors.csv")

# --- Preprocess Submissions ---
# Use only the first artist (ignores features, splits on commas)
submissions["Primary Artist"] = submissions["Artist(s)"].apply(lambda x: str(x).split(",")[0].strip())

# Most submitted primary artists (with more than 1 submission)
top_artists = submissions["Primary Artist"].value_counts().reset_index()
top_artists.columns = ["Artist", "Submission Count"]
top_artists = top_artists[top_artists["Submission Count"] > 1]

# Most submitted songs with unique (Title + Primary Artist) combination (more than once)
top_songs = submissions.groupby(["Title", "Primary Artist"]).size().reset_index(name="Submission Count")
top_songs = top_songs[top_songs["Submission Count"] > 1]
top_songs = top_songs.sort_values(by="Submission Count", ascending=False)

# Player leaderboard
votes_with_submitter = votes.merge(submissions[["Spotify URI", "Submitter ID"]], on="Spotify URI")
votes_with_submitter = votes_with_submitter.merge(competitors, left_on="Submitter ID", right_on="ID")
player_leaderboard = votes_with_submitter.groupby("Name")["Points Assigned"].sum().reset_index()
player_leaderboard.columns = ["Username", "Total Points"]
player_leaderboard = player_leaderboard.sort_values(by="Total Points", ascending=False)

# --- Streamlit Layout ---
st.title("🎵 Music League Dashboard")

st.header("🏆 Unofficial Player Leaderboard")
fig1 = px.bar(player_leaderboard.head(10), x="Total Points", y="Username", orientation="h")
st.plotly_chart(fig1)

st.header("🎤 Most Submitted Primary Artists")
fig2 = px.bar(top_artists.head(10), x="Submission Count", y="Artist", orientation="h")
st.plotly_chart(fig2)

st.header("🎶 Most Submitted Songs")
fig3 = px.bar(top_songs.head(10), x="Submission Count", y="Title", orientation="h",
              hover_data={"Primary Artist": True, "Title": False})
st.plotly_chart(fig3)


# 🎯 Snub Analysis Section
st.header("🥲 Most Snubbed Players (0-Vote Submissions)")

round_map = rounds.set_index("ID")["Name"]
submitter_map = competitors.set_index("ID")["Name"]

snubbed = submissions.copy()
snubbed["Primary Artist"] = snubbed["Artist(s)"].apply(lambda x: str(x).split(",")[0].strip())
snubbed["Username"] = snubbed["Submitter ID"].map(submitter_map)
snubbed["Round"] = snubbed["Round ID"].map(round_map)

vote_counts = votes.groupby("Spotify URI")["Points Assigned"].sum().reset_index()
vote_counts.columns = ["Spotify URI", "Total Points"]
snubbed = snubbed.merge(vote_counts, on="Spotify URI", how="left").fillna({"Total Points": 0})
snubbed["Total Points"] = snubbed["Total Points"].astype(int)

snubbed_stats = snubbed[snubbed["Total Points"] == 0].groupby("Username").size().reset_index(name="Zero Vote Songs")
submission_counts = submissions["Submitter ID"].map(submitter_map).value_counts().reset_index()
submission_counts.columns = ["Username", "Total Submissions"]
snubbed_stats = snubbed_stats.merge(submission_counts, on="Username", how="left")
snubbed_stats["Snub Rate (%)"] = (snubbed_stats["Zero Vote Songs"] / snubbed_stats["Total Submissions"] * 100).round(1)
snubbed_stats = snubbed_stats.sort_values(by="Zero Vote Songs", ascending=False)

st.header("📉 Snub Rate Leaderboard")
ranked_snubbers = snubbed_stats[snubbed_stats["Total Submissions"] >= 2].copy()
ranked_snubbers = ranked_snubbers.sort_values(by="Snub Rate (%)", ascending=False).reset_index(drop=True)
ranked_snubbers.insert(0, "Rank", range(1, len(ranked_snubbers) + 1))
st.dataframe(
    ranked_snubbers[["Rank", "Username", "Zero Vote Songs", "Total Submissions", "Snub Rate (%)"]],
    use_container_width=True
)

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

st.header("🗳️ Who Voted For Me")

# Join votes → get submitter + voter names
votes_extended = votes.merge(submissions[["Spotify URI", "Submitter ID"]], on="Spotify URI")
votes_extended = votes_extended.merge(competitors, left_on="Submitter ID", right_on="ID", suffixes=("", "_submitter"))
votes_extended = votes_extended.merge(competitors, left_on="Voter ID", right_on="ID", suffixes=("", "_voter"))

# Build pivot table: Voter → Submitter
pivot = votes_extended.pivot_table(
    index="Name_voter",
    columns="Name",
    values="Points Assigned",
    aggfunc="sum",
    fill_value=0
)

# Optional: sort by total points given
pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

# Plot heatmap
fig_heatmap = px.imshow(
    pivot,
    text_auto=True,
    labels=dict(x="Submitter", y="Voter", color="Points"),
    title="Who Gave Points to Whom",
    color_continuous_scale="YlGnBu"
)

st.plotly_chart(fig_heatmap, use_container_width=True)


st.header("🎧 Player Profile")

# Select a player
all_players = competitors["Name"].dropna().sort_values().unique()
selected_player = st.selectbox("Select a player", all_players)

# Map round and submitter names
round_map = rounds.set_index("ID")["Name"]
submitter_map = competitors.set_index("ID")["Name"]

# Merge data
profile_subs = submissions.copy()
profile_subs["Round"] = profile_subs["Round ID"].map(round_map)
profile_subs["Username"] = profile_subs["Submitter ID"].map(submitter_map)
profile_subs["Primary Artist"] = profile_subs["Artist(s)"].apply(lambda x: str(x).split(",")[0].strip())

# Add vote counts
vote_counts = votes.groupby("Spotify URI")["Points Assigned"].sum().reset_index()
vote_counts.columns = ["Spotify URI", "Total Points"]
profile_subs = profile_subs.merge(vote_counts, on="Spotify URI", how="left").fillna({"Total Points": 0})
profile_subs["Total Points"] = profile_subs["Total Points"].astype(int)

# Filter to this player's submissions
player_subs = profile_subs[profile_subs["Username"] == selected_player]

# Summary stats
total = player_subs["Total Points"].sum()
avg = player_subs["Total Points"].mean()
best = player_subs.sort_values("Total Points", ascending=False).head(1)
worst = player_subs.sort_values("Total Points").head(1)

st.subheader(f"📊 Summary for {selected_player}")
st.write(f"**Total Points:** {total}")
st.write(f"**Average Points per Song:** {avg:.2f}")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 🔝 Best Song")
    st.write(best[["Title", "Primary Artist", "Total Points", "Round"]].reset_index(drop=True))
with col2:
    st.markdown("#### 🥶 Lowest Scoring Song")
    st.write(worst[["Title", "Primary Artist", "Total Points", "Round"]].reset_index(drop=True))

# Voters who supported them the most
votes_extended = votes.merge(submissions[["Spotify URI", "Submitter ID"]], on="Spotify URI")
votes_extended = votes_extended[votes_extended["Submitter ID"] == competitors[competitors["Name"] == selected_player]["ID"].values[0]]
votes_extended = votes_extended.merge(competitors, left_on="Voter ID", right_on="ID", suffixes=("", "_voter"))
supporters = votes_extended.groupby("Name")["Points Assigned"].sum().reset_index().sort_values("Points Assigned", ascending=False)

st.subheader("🙌 Top Supporters")
st.write(supporters.rename(columns={"Name": "Voter", "Points Assigned": "Total Points Given"}).reset_index(drop=True))

st.subheader("🎼 Submission History")
st.dataframe(player_subs[["Round", "Title", "Primary Artist", "Total Points"]].sort_values(by="Round"), use_container_width=True)

