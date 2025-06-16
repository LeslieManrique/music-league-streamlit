import os
import random

import pandas as pd
import plotly.express as px
import streamlit as st

COLOR_PALETTE = [
    "#9e01c4",  # purple
    "#ff69b4",  # pink
    "#eb4034",  # red-orange
    "#00bcd4",  # teal
    "#ffc107",  # amber
    "#4caf50",  # green
    "#3f51b5",  # indigo
    "#f50057",  # hot pink
]

# --- Dynamic Season Setup ---
season_dirs = [d for d in os.listdir("exports") if d.startswith("season_") and os.path.isdir(os.path.join("exports", d))]
season_numbers = sorted([int(d.split("_")[1]) for d in season_dirs])
latest_season = season_numbers[-1] if season_numbers else 1

SEASON_METADATA = {
    1: {"title": "🎶 Overwatch 3 Waiting Room 🎶"},
    2: {"title": "🎮 Marvel Rivals Waiting Room 🎮"},
    3: {"title": "💦 Gonning Corner 💦"},
}
season_number = st.sidebar.selectbox("Select a Season", season_numbers, index=len(season_numbers) - 1)
season_path = f"exports/season_{season_number}"
meta = SEASON_METADATA.get(season_number, {"title": "🎵 Music League 🎵"})
meta["color"] = random.choice(COLOR_PALETTE)

# Hide GitHub and footer branding
st.markdown(
    f"""
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {{ display: none; }}
    footer {{ visibility: hidden; }}
    .css-cio0dv.egzxvld1 {{
        visibility: visible;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #1e1e1e;
        color: {meta['color']};
        text-align: center;
        padding: 0.5rem;
        font-size: 0.85rem;
    }}
    </style>
    <div style="background-color:{meta['color']};padding:1rem 1.5rem;margin-bottom:1.5rem;border-radius:8px">
        <h1 style="color:white;text-align:center;">{meta['title']}</h1>
    </div>
    <div class="css-cio0dv egzxvld1">Made with ❤️ by Leslie & ChatGPT</div>
    """,
    unsafe_allow_html=True
)

# Load data
def load_data(path):
    return {
        "votes": pd.read_csv(os.path.join(path, "votes.csv")),
        "submissions": pd.read_csv(os.path.join(path, "submissions.csv")),
        "rounds": pd.read_csv(os.path.join(path, "rounds.csv")),
        "competitors": pd.read_csv(os.path.join(path, "competitors.csv"))
    }

data = load_data(season_path)
votes, submissions, rounds, competitors = data.values()

# --- Preprocess Data ---
rounds["Created"] = pd.to_datetime(rounds["Created"]).dt.date

# Tabs
overview_tab, leaderboard_tab, snub_tab, explore_tab, profile_tab, metrics_tab = st.tabs([
    "📅 Rounds & Participation",
    "🏆 Leaderboard",
    "🥲 Snubs",
    "🔍 Explore",
    "🎧 Player Profile",
    "📈 Metrics Summary"
])
with overview_tab:
    round_user_counts = (
        submissions.groupby("Round ID")["Submitter ID"]
        .nunique()
        .reset_index()
        .rename(columns={"Submitter ID": "Number of Participants"})
    )
    round_user_counts = round_user_counts.merge(
        rounds[["ID", "Name", "Created"]],
        left_on="Round ID",
        right_on="ID",
        how="left"
    )
    round_user_counts = round_user_counts[["Name", "Created", "Number of Participants"]]
    round_user_counts = round_user_counts.rename(columns={"Name": "Round Name", "Created": "Created At"})
    round_user_counts = round_user_counts.sort_values("Created At")
    st.dataframe(round_user_counts, use_container_width=True)

with leaderboard_tab:
    st.subheader("Top Players by Points")
    votes_with_submitter = votes.merge(submissions[["Spotify URI", "Submitter ID", "Round ID"]], on=["Spotify URI", "Round ID"])
    votes_with_submitter = votes_with_submitter.merge(competitors, left_on="Submitter ID", right_on="ID")
    player_leaderboard = votes_with_submitter.groupby("Name")["Points Assigned"].sum().reset_index()
    player_leaderboard.columns = ["Username", "Total Points"]
    player_leaderboard = player_leaderboard.sort_values(by="Total Points", ascending=False)
    st.dataframe(player_leaderboard, use_container_width=True)

with metrics_tab:
    st.header("📈 Season Summary Metrics")
    total_votes = votes.shape[0]
    total_songs = submissions.shape[0]
    total_players = competitors.shape[0]
    avg_votes_per_song = votes.groupby("Spotify URI")["Points Assigned"].sum().mean()
    avg_points_per_user = votes.merge(submissions, on=["Spotify URI", "Round ID"], how="left")
    avg_points_per_user = avg_points_per_user.groupby("Submitter ID")["Points Assigned"].sum().mean()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Songs Submitted", total_songs)
        st.metric("Total Votes Cast", total_votes)
        st.metric("Average Votes per Song", f"{avg_votes_per_song:.2f}")
    with col2:
        st.metric("Total Players", total_players)
        st.metric("Average Points per Player", f"{avg_points_per_user:.2f}")

    st.subheader("🎨 Most Submitted Artists")
    submissions["Primary Artist"] = submissions["Artist(s)"].apply(lambda x: str(x).split(",")[0].strip())
    top_artists = submissions["Primary Artist"].value_counts().reset_index()
    top_artists.columns = ["Artist", "Submission Count"]
    fig_artist = px.bar(top_artists.head(10), x="Submission Count", y="Artist", orientation="h")
    st.plotly_chart(fig_artist)

    st.subheader("🎵 Most Submitted Songs")
    top_songs = submissions.groupby(["Title", "Primary Artist"]).size().reset_index(name="Submission Count")
    top_songs = top_songs[top_songs["Submission Count"] > 1].sort_values(by="Submission Count", ascending=False)
    fig_songs = px.bar(top_songs.head(10), x="Submission Count", y="Title", orientation="h", hover_data={"Primary Artist": True, "Title": False})
    st.plotly_chart(fig_songs)


with snub_tab:
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

    ranked_snubbers = snubbed_stats[snubbed_stats["Total Submissions"] >= 2].copy()
    ranked_snubbers = ranked_snubbers.sort_values(by="Snub Rate (%)", ascending=False).reset_index(drop=True)
    ranked_snubbers.insert(0, "Rank", range(1, len(ranked_snubbers) + 1))
    st.dataframe(
        ranked_snubbers[["Rank", "Username", "Zero Vote Songs", "Total Submissions", "Snub Rate (%)"]],
        use_container_width=True
    )

with explore_tab:
    round_map = rounds.set_index("ID")["Name"]
    submitter_map = competitors.set_index("ID")["Name"]
    summary_df = submissions.copy()
    summary_df["Round Name"] = summary_df["Round ID"].map(round_map)
    summary_df["Username"] = summary_df["Submitter ID"].map(submitter_map)
    summary_df["Song Name"] = summary_df["Title"]
    summary_df["Artist Name"] = summary_df["Artist(s)"].apply(lambda x: str(x).split(",")[0].strip())

    vote_counts = votes.groupby("Spotify URI")["Points Assigned"].sum().reset_index()
    vote_counts.columns = ["Spotify URI", "Number of Votes"]
    summary_df = summary_df.merge(vote_counts, on="Spotify URI", how="left").fillna({"Number of Votes": 0})
    summary_df["Number of Votes"] = summary_df["Number of Votes"].astype(int)
    summary_table = summary_df[["Round Name", "Username", "Song Name", "Artist Name", "Number of Votes"]]

    with st.expander("Filter table"):
        selected_user = st.selectbox("Filter by Username", ["All"] + sorted(summary_table["Username"].dropna().unique()))
        selected_round = st.selectbox("Filter by Round", ["All"] + sorted(summary_table["Round Name"].dropna().unique()))

    filtered_table = summary_table.copy()
    if selected_user != "All":
        filtered_table = filtered_table[filtered_table["Username"] == selected_user]
    if selected_round != "All":
        filtered_table = filtered_table[filtered_table["Round Name"] == selected_round]

    st.dataframe(filtered_table, use_container_width=True)

with profile_tab:
    all_players = competitors["Name"].dropna().sort_values().unique()
    selected_player = st.selectbox("Select a player", all_players)

    round_map = rounds.set_index("ID")["Name"]
    submitter_map = competitors.set_index("ID")["Name"]

    profile_subs = submissions.copy()
    profile_subs["Round"] = profile_subs["Round ID"].map(round_map)
    profile_subs["Username"] = profile_subs["Submitter ID"].map(submitter_map)
    profile_subs["Primary Artist"] = profile_subs["Artist(s)"].apply(lambda x: str(x).split(",")[0].strip())

    vote_counts = votes.groupby("Spotify URI")["Points Assigned"].sum().reset_index()
    vote_counts.columns = ["Spotify URI", "Total Points"]
    profile_subs = profile_subs.merge(vote_counts, on="Spotify URI", how="left").fillna({"Total Points": 0})
    profile_subs["Total Points"] = profile_subs["Total Points"].astype(int)

    player_subs = profile_subs[profile_subs["Username"] == selected_player]

    total = player_subs["Total Points"].sum()
    avg = player_subs["Total Points"].mean()
    best = player_subs.sort_values("Total Points", ascending=False).head(5)
    worst = player_subs.sort_values("Total Points").head(5)

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

    votes_extended = votes.merge(submissions[["Spotify URI", "Submitter ID"]], on="Spotify URI")
    votes_extended = votes_extended[votes_extended["Submitter ID"] == competitors[competitors["Name"] == selected_player]["ID"].values[0]]
    votes_extended = votes_extended.merge(competitors, left_on="Voter ID", right_on="ID", suffixes=("", "_voter"))
    supporters = votes_extended.groupby("Name")["Points Assigned"].sum().reset_index().sort_values("Points Assigned", ascending=False)

    st.subheader("🙌 Top Supporters")
    st.write(supporters.rename(columns={"Name": "Voter", "Points Assigned": "Total Points Given"}).reset_index(drop=True))

    st.subheader("🎼 Submission History")
    st.dataframe(player_subs[["Round", "Title", "Primary Artist", "Total Points"]].sort_values(by="Round"), use_container_width=True)
