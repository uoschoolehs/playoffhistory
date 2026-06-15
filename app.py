import streamlit as st
import pandas as pd
import time
import plotly.express as px
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, playergamelog

# Page configuration for a clean, professional analytics dashboard
st.set_page_config(page_title="Universal NBA Postseason Lookup", layout="wide", page_icon="🏀")

st.title("🏀 Universal NBA Postseason Lookup Tool")
st.markdown("""
This application functions as a dynamic lookup engine for **any NBA player across any era**. 
It resolves the player's internal API ID, queries their historical footprint to isolate active playoff years, 
and aggregates authentic, game-by-game career postseason records directly from the official NBA stats API.
""")

# Standard API request headers to prevent rate-limiting or blocks from stats.nba.com
HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Connection': 'keep-alive'
}

# ---------------------------------------------------------
# GLOBAL DEBUGGING LOGS (Stored in session state)
# ---------------------------------------------------------
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []

def log_debug(message, data=None):
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    if data is not None:
        log_entry += f"\nData/Context: {data}"
    st.session_state.debug_logs.append(log_entry)

# Sidebar Control for Debugging
st.sidebar.header("🔧 System Controls")
show_debug_panel = st.sidebar.checkbox("Show Developer Debug Console", value=True)
clear_logs = st.sidebar.button("Clear Debug Logs")
if clear_logs:
    st.session_state.debug_logs = []
    st.rerun()

# ---------------------------------------------------------
# INTERACTIVE PLAYER SEARCH & ID MATCHING
# ---------------------------------------------------------
search_term = st.text_input("Search Player Name (e.g., Michael Jordan, LeBron James, Kobe Bryant, Stephen Curry):", value="Michael Jordan")

selected_player = None
if search_term.strip():
    all_players = players.get_players()
    # Case-insensitive substring match
    matched_players = [p for p in all_players if search_term.lower() in p['full_name'].lower()]
    
    log_debug(f"Search initiated for term: '{search_term}'", f"Found {len(matched_players)} matches.")
    
    if not matched_players:
        st.error(f"No player matching '{search_term}' could be located in the NBA database.")
    else:
        if len(matched_players) > 1:
            player_options = {p['full_name']: p for p in matched_players}
            chosen_name = st.selectbox("Multiple matches found. Select exact profile:", list(player_options.keys()))
            selected_player = player_options[chosen_name]
        else:
            selected_player = matched_players[0]
            st.success(f"Matched Profile: **{selected_player['full_name']}** (ID: {selected_player['id']}, Active: {selected_player['is_active']})")

# ---------------------------------------------------------
# DYNAMIC SEASONS & GAME LOG FETCHING ENGINE
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def fetch_player_playoff_seasons(player_id, player_name):
    """Queries career history to locate every season the player made the playoffs."""
    try:
        log_debug(f"Requesting PlayerCareerStats for {player_name} (ID: {player_id})")
        career = playercareerstats.PlayerCareerStats(player_id=player_id, headers=HEADERS, timeout=15)
        
        # Safely try accessing the post-season dataframe attribute
        try:
            df_post = career.season_totals_post_season.get_data_frame()
            log_debug("Successfully retrieved 'season_totals_post_season' attribute.")
        except Exception as attr_err:
            log_debug(f"Attribute access failed: {attr_err}. Attempting position fallback.")
            dfs = career.get_data_frames()
            df_post = dfs[2]  # Position 2 is traditionally SeasonTotalsPostSeason
            
        if df_post.empty:
            log_debug(f"Career postseason totals returned an empty DataFrame for {player_name}.")
            return [], df_post
            
        if 'SEASON_ID' in df_post.columns:
            seasons = sorted(df_post['SEASON_ID'].unique().tolist())
            log_debug(f"Discovered {len(seasons)} playoff campaigns:", seasons)
            return seasons, df_post
        else:
            log_debug("SEASON_ID column missing from dataframe structure.", df_post.columns.tolist())
            return [], df_post
            
    except Exception as e:
        log_debug(f"Fatal exception during career timeline extraction: {str(e)}")
        return [], pd.DataFrame()

@st.cache_data(show_spinner=False)
def aggregate_career_playoff_logs(player_id, player_name, seasons):
    """Sequentially crawls individual playoff logs for explicit active seasons."""
    if not seasons:
        return pd.DataFrame()
        
    master_logs = []
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    for index, season in enumerate(seasons):
        status_msg.text(f"Crawling game logs for postseason campaign: {season}...")
        log_debug(f"Dispatching PlayerGameLog request for season {season}")
        
        try:
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star='Playoffs',
                headers=HEADERS,
                timeout=15
            )
            df = gamelog.get_data_frames()[0]
            
            if not df.empty:
                df['SEASON_YEAR'] = season  # Inject human-readable season key
                master_logs.append(df)
                log_debug(f"Season {season} complete. Extracted {len(df)} games.")
            else:
                log_debug(f"Season {season} returned zero valid game rows.")
                
            # Graceful pacing to comply with stats.nba.com security throttling
            time.sleep(0.6)
            
        except Exception as season_err:
            log_debug(f"Skipped season {season} due to request exception: {str(season_err)}")
            st.warning(f"Temporary issue parsing stats for season {season}. Review debug log.")
            
        progress_bar.progress((index + 1) / len(seasons))
        
    status_msg.empty()
    progress_bar.empty()
    
    if master_logs:
        combined_df = pd.concat(master_logs, ignore_index=True)
        log_debug(f"Aggregation sequence complete. Unified shape: {combined_df.shape}")
        return combined_df
    return pd.DataFrame()

# ---------------------------------------------------------
# RENDERING ENGINE & ANALYTICS PIPELINE
# ---------------------------------------------------------
if selected_player:
    p_id = selected_player['id']
    p_name = selected_player['full_name']
    
    # Step 1: Discover valid playoff seasons
    playoff_seasons, raw_career_df = fetch_player_playoff_seasons(p_id, p_name)
    
    if not playoff_seasons:
        st.warning(f"No historical playoff records located under this profile structure. {p_name} has no recorded career NBA postseason appearances.")
    else:
        # Step 2: Extract historical playoff game logs
        with st.spinner(f"Connecting to API to assemble career postseason log for {p_name}..."):
            playoff_df = aggregate_career_playoff_logs(p_id, p_name, playoff_seasons)
            
        if playoff_df.empty:
            st.error("The API successfully acknowledged the profile's postseason entries, but individual game logs failed to return valid data sheets.")
        else:
            # Data Cleaning layer to handle historical tracking discrepancies safely
            for col in ['PTS', 'AST', 'REB', 'STL', 'BLK', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'MIN']:
                if col in playoff_df.columns:
                    playoff_df[col] = pd.to_numeric(playoff_df[col], errors='coerce').fillna(0)
            
            # Derive meta metrics
            if 'MATCHUP' in playoff_df.columns:
                playoff_df['OPPONENT'] = playoff_df['MATCHUP'].apply(lambda x: x.split(' ')[-1])
                playoff_df['LOCATION'] = playoff_df['MATCHUP'].apply(lambda x: 'Away' if '@' in x else 'Home')
            else:
                playoff_df['OPPONENT'] = "Unknown"
                playoff_df['LOCATION'] = "Unknown"
                
            total_games = len(playoff_df)
            wins = len(playoff_df[playoff_df['WL'] == 'W']) if 'WL' in playoff_df.columns else 0
            losses = total_games - wins
            win_pct = (wins / total_games) * 100 if total_games > 0 else 0
            
            # High-level analytical overview metrics
            st.header(f"📊 {p_name} Postseason Career Analytics")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Playoff Games Played", f"{total_games}")
            m2.metric("Postseason Record", f"{wins}W - {losses}L")
            m3.metric("Playoff Win Percentage", f"{win_pct:.1f}%")
            m4.metric("Career Playoff PPG", f"{playoff_df['PTS'].mean():.1f}" if 'PTS' in playoff_df.columns else "N/A")
            
            # Tabbed Layout Layout
            tab1, tab2, tab3 = st.tabs(["🔥 Complete Performance Log", "🎯 Series & Opponent Analysis", "📈 Statistical Trajectories"])
            
            with tab1:
                st.subheader("Interactive Career Playoff Logs Explorer")
                st.markdown("Filter, sort, and look up every post-season game row recorded inside the API structure.")
                
                # Interactive filter layout
                f_cols = st.columns(3)
                with f_cols[0]:
                    season_filter = st.multiselect("Filter Seasons:", options=sorted(playoff_df['SEASON_YEAR'].unique()))
                with f_cols[1]:
                    opp_filter = st.multiselect("Filter Opponents:", options=sorted(playoff_df['OPPONENT'].unique()))
                with f_cols[2]:
                    outcome_filter = st.multiselect("Game Outcome:", options=['W', 'L'])
                    
                display_df = playoff_df.copy()
                if season_filter:
                    display_df = display_df[display_df['SEASON_YEAR'].isin(season_filter)]
                if opp_filter:
                    display_df = display_df[display_df['OPPONENT'].isin(opp_filter)]
                if outcome_filter:
                    display_df = display_df[display_df['WL'].isin(outcome_filter)]
                    
                st.dataframe(display_df, use_container_width=True)
                
            with tab2:
                st.subheader("Postseason Performance Breakdowns by Matchup Team")
                
                # Group stats to identify records against explicit opponents
                if 'OPPONENT' in playoff_df.columns:
                    opp_stats = playoff_df.groupby('OPPONENT').agg(
                        Games=('GAME_ID', 'count'),
                        PPG=('PTS', 'mean'),
                        RPG=('REB', 'mean'),
                        APG=('AST', 'mean')
                    ).reset_index().round(1)
                    
                    st.dataframe(opp_stats.sort_values(by='Games', ascending=False), use_container_width=True)
                    
                    fig_opp = px.bar(opp_stats, x='OPPONENT', y='PPG', title=f"Average Points Scored per Game vs Opponents", color='Games', labels={'PPG': 'Points Per Game', 'OPPONENT': 'Opponent Abbreviation'})
                    st.plotly_chart(fig_opp, use_container_width=True)
                    
            with tab3:
                st.subheader("Playoff Scoring Trajectory Across Career Timeline")
                if 'GAME_DATE' in playoff_df.columns and 'PTS' in playoff_df.columns:
                    # Sort oldest to newest for clear visual flow
                    trajectory_df = playoff_df.copy()
                    if 'SEASON_YEAR' in trajectory_df.columns:
                        trajectory_df = trajectory_df.sort_values(by=['SEASON_YEAR', 'GAME_ID'], ascending=[True, True])
                    trajectory_df['Career Game #'] = range(1, len(trajectory_df) + 1)
                    
                    fig_traj = px.line(
                        trajectory_df, 
                        x='Career Game #', 
                        y='PTS', 
                        hover_data=['SEASON_YEAR', 'MATCHUP', 'PTS', 'WL'],
                        title=f"{p_name} Game-by-Game Scoring Evolution",
                        labels={'PTS': 'Points Scored'}
                    )
                    st.plotly_chart(fig_traj, use_container_width=True)

# ---------------------------------------------------------
# SYSTEM DEVELOPER DEBUG CONSOLE
# ---------------------------------------------------------
if show_debug_panel:
    st.markdown("---")
    with st.expander("🔧 Developer Debug Console (Live System Payloads)", expanded=True):
        st.markdown("""
        **Why this matters:** Use this area to audit API responses. If a player lookup returns empty configurations, 
        this trace indicates if the fault lies inside the static ID matcher, the API season index, or a formatting mismatch.
        """)
        
        col_db1, col_db2 = st.columns(2)
        with col_db1:
            st.write("**Active Target Profile Metadata:**")
            st.json(selected_player if selected_player else {"Status": "No player matched yet."})
            
            st.write("**Discovered Postseason Seasons Array:**")
            st.code(playoff_seasons if 'playoff_seasons' in locals() else [])
            
        with col_db2:
            st.write("**Raw Season History Shape & Columns:**")
            if 'raw_career_df' in locals() and not raw_career_df.empty:
                st.write(f"DataFrame Shape: {raw_career_df.shape}")
                st.write("Column Schema:")
                st.code(raw_career_df.columns.tolist())
            else:
                st.code("No career frame populated.")
                
        st.write("**Live System Trace Messages & API Call Logs:**")
        if st.session_state.debug_logs:
            for log in reversed(st.session_state.debug_logs):
                st.text(log)
        else:
            st.info("No active API call signals or trace checkpoints recorded.")
