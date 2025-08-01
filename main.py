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
    3: {"title": "💦 G00ning Corner 💦"},
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

    st.subheader("🔥 Voting Heatmap")

    # Merge votes with voter and submitter names
    heatmap_df = votes.merge(
        submissions[["Spotify URI", "Round ID", "Submitter ID"]],
        on=["Spotify URI", "Round ID"],
        how="left"
    )
    heatmap_df = heatmap_df.merge(
        competitors[["ID", "Name"]].rename(columns={"ID": "Submitter ID", "Name": "Submitter Name"}),
        on="Submitter ID",
        how="left"
    )
    heatmap_df = heatmap_df.merge(
        competitors[["ID", "Name"]].rename(columns={"ID": "Voter ID", "Name": "Voter Name"}),
        on="Voter ID",
        how="left"
    )

    # Create pivot table: rows = Voters, columns = Submitters, values = total points given
    pivot = heatmap_df.pivot_table(
        index="Voter Name",
        columns="Submitter Name",
        values="Points Assigned",
        aggfunc="sum",
        fill_value=0
    )

    fig = px.imshow(
        pivot,
        labels=dict(x="Submitter", y="Voter", color="Points"),
        color_continuous_scale="viridis"
    )
    fig.update_layout(height=600, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

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

    st.subheader("😤 Your Biggest Haters")

    # Get the selected player's ID
    selected_player_id = competitors[competitors["Name"] == selected_player]["ID"].values[0]

    # Get selected player's submissions
    player_songs = submissions[submissions["Submitter ID"] == selected_player_id]

    if len(player_songs) == 0:
        st.write("No submissions found for this player.")
    else:
        # Calculate hate points using the proper method:
        # Hate = (Total points voter had in round) - (Points given to target player)
        hate_stats = []
        other_players = competitors[competitors["ID"] != selected_player_id]
        
        for _, hater in other_players.iterrows():
            hater_id = hater["ID"]
            hater_name = hater["Name"]
            total_hate_points = 0
            round_breakdown = []
            
            # Check each round
            for _, round_info in rounds.iterrows():
                round_id = round_info["ID"]
                round_name = round_info["Name"]
                
                # Get all votes this potential hater made in this round
                hater_votes_in_round = votes[
                    (votes["Voter ID"] == hater_id) & 
                    (votes["Round ID"] == round_id)
                ]
                
                if len(hater_votes_in_round) == 0:
                    # Hater didn't participate - no hate points
                    round_breakdown.append({
                        "round": round_name,
                        "participated": False,
                        "total_points": 0,
                        "points_to_player": 0,
                        "hate_points": 0,
                        "detail": "Didn't vote"
                    })
                else:
                    # Calculate total points this hater had in this round
                    total_points_in_round = hater_votes_in_round["Points Assigned"].sum()
                    
                    # Get selected player's songs in this round
                    player_songs_in_round = player_songs[player_songs["Round ID"] == round_id]
                    player_uris_in_round = player_songs_in_round["Spotify URI"].tolist()
                    
                    # Calculate points given to selected player in this round
                    points_to_player = hater_votes_in_round[
                        hater_votes_in_round["Spotify URI"].isin(player_uris_in_round)
                    ]["Points Assigned"].sum()
                    
                    # Hate points = total points available - points given to player
                    # BUT only if player had songs in this round
                    hate_points_this_round = 0
                    if len(player_songs_in_round) > 0:
                        hate_points_this_round = total_points_in_round - points_to_player
                    
                    total_hate_points += hate_points_this_round
                    
                    round_breakdown.append({
                        "round": round_name,
                        "participated": True,
                        "total_points": total_points_in_round,
                        "points_to_player": points_to_player,
                        "hate_points": hate_points_this_round,
                        "player_songs_count": len(player_songs_in_round),
                        "detail": f"Had {total_points_in_round} points, gave {points_to_player} to you = {hate_points_this_round} hate" if len(player_songs_in_round) > 0 else "You had no songs in this round"
                    })
            
            hate_stats.append({
                "hater": hater_name,
                "total_hate_points": total_hate_points,
                "round_breakdown": round_breakdown
            })
        
        # Filter for people with more than 1 hate point and sort
        hate_stats = [h for h in hate_stats if h["total_hate_points"] > 1]
        hate_stats = sorted(hate_stats, key=lambda x: x["total_hate_points"], reverse=True)
        
        if len(hate_stats) == 0:
            st.write("🎉 Great news! Nobody has more than 1 hate point against you. People are using their votes on you! 😊")
        else:
            # Show top 5 haters
            top_haters = hate_stats[:5]
            
            st.write(f"Found {len(hate_stats)} people with 2+ hate points against you:")
            
            # Create haters dataframe for display
            haters_display = []
            for i, hater_data in enumerate(top_haters):
                # Calculate some summary stats
                participated_rounds = [r for r in hater_data["round_breakdown"] if r["participated"]]
                total_points_available = sum(r["total_points"] for r in participated_rounds)
                total_points_given = sum(r["points_to_player"] for r in participated_rounds)
                
                haters_display.append({
                    "Rank": i + 1,
                    "Hater": hater_data["hater"],
                    "Hate Points": hater_data["total_hate_points"],
                    "Points Available": total_points_available,
                    "Points Given to You": total_points_given,
                    "Hate %": f"{(hater_data['total_hate_points']/total_points_available*100):.1f}%" if total_points_available > 0 else "0%"
                })
            
            haters_df = pd.DataFrame(haters_display)
            st.dataframe(haters_df, use_container_width=True)
            
            # Show details for the biggest hater
            if len(top_haters) > 0:
                biggest_hater = top_haters[0]
                st.markdown(f"#### 👑 Your Biggest Hater: {biggest_hater['hater']}")
                st.write(f"***{biggest_hater['total_hate_points']} total hate points***")
                
            
            # Create a bar chart of hate points
            if len(top_haters) > 1:
                chart_data = pd.DataFrame({
                    "Hater": [h["hater"] for h in top_haters],
                    "Hate Points": [h["total_hate_points"] for h in top_haters]
                })
                
                fig_hate = px.bar(
                    chart_data, 
                    x="Hate Points", 
                    y="Hater", 
                    orientation="h",
                    title=f"Who Has the Most Hate Points Against {selected_player}?",
                    color="Hate Points",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig_hate, use_container_width=True)

    # Show voting allocation summary
    st.subheader("🎯 How People Allocated Their Votes")

    vote_allocation = []
    other_players = competitors[competitors["ID"] != selected_player_id]

    for _, voter in other_players.iterrows():
        voter_id = voter["ID"]
        voter_name = voter["Name"]
        
        # Get all votes this person made to selected player's songs
        votes_to_player = votes[
            (votes["Voter ID"] == voter_id) & 
            (votes["Spotify URI"].isin(player_songs["Spotify URI"]))
        ]
        
        # Get all votes this person made total
        all_votes_by_voter = votes[votes["Voter ID"] == voter_id]
        
        if len(all_votes_by_voter) > 0:
            total_points_used = all_votes_by_voter["Points Assigned"].sum()
            points_to_player = votes_to_player["Points Assigned"].sum()
            hate_points = total_points_used - points_to_player
            
            vote_allocation.append({
                "Voter": voter_name,
                "Total Points Used": total_points_used,
                "Points to You": int(points_to_player),
                "Hate Points": hate_points,
                "Your Share %": f"{(points_to_player/total_points_used*100):.1f}%" if total_points_used > 0 else "0%"
            })

    if len(vote_allocation) > 0:
        allocation_df = pd.DataFrame(vote_allocation)
        allocation_df = allocation_df.sort_values("Points to You", ascending=False)
        st.dataframe(allocation_df, use_container_width=True)

    # Updated explanation
    with st.expander("ℹ️ How are 'Hate Points' calculated? (Vote-Based Method)"):
        st.write("""
        **PROPER METHOD - Based on Vote Allocation:**
        
        🔥 **Hate Points** = (Total points voter had in round) - (Points given to you)
        
        **Example calculation:**
        - **Round A**: Annie has 5 points, gives you 0 → **5 hate points**
        - **Round B**: Annie has 3 points, gives you 1 → **2 hate points**  
        - **Round C**: Annie has 4 points, gives you 4 → **0 hate points**
        - **Justin's total**: **7 hate points**
        
        **Why this method works:**
        - Accounts for actual voting power each person had
        - Shows how much of their available votes they chose NOT to give you
        - Fair across different rounds with different point allocations
        - Higher hate = more points they could have given you but didn't
        
        **Note**: Only counts rounds where you had songs submitted.
        """)
    st.subheader("🎼 Submission History")
    st.dataframe(player_subs[["Round", "Title", "Primary Artist", "Total Points"]].sort_values(by="Round"), use_container_width=True)
