import streamlit as st
import pandas as pd
import time
import urllib.request
import json

# Page configuration for a professional scouting ledger layout
st.set_page_config(page_title="Scouting Analytics Ledger", layout="wide", page_icon="🏀")

st.title("🏀 Advanced Postseason Resume Explorer")
st.markdown("""
This platform combines real-time endpoints from the official NBA stats API with high-resolution historical records. 
If the NBA stats server throttles or drops the cloud connection, the engine utilizes a localized fallback matrix 
loaded with the exact macro ratings and playoff splits from historical ledger tracking sheets.
""")

# ---------------------------------------------------------
# STEP-BY-STEP TECHNICAL DEBUG SYSTEM
# ---------------------------------------------------------
if "tech_debug_logs" not in st.session_state:
    st.session_state.tech_debug_logs = []

def trace_step(step_name, status, details=None):
    """Logs granular technical steps, parameters, and payloads to the console."""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [STEP: {step_name}] -> STATUS: {status.upper()}"
    if details:
        log_entry += f"\n   Context: {details}"
    st.session_state.tech_debug_logs.append(log_entry)

# Sidebar Controls for Deep Debugging
st.sidebar.header("🔧 Developer Diagnostics")
show_tracer = st.sidebar.checkbox("Show Step-by-Step Execution Tracer", value=True)
if st.sidebar.button("Clear Diagnostic Memory Logs"):
    st.session_state.tech_debug_logs = []
    st.rerun()

# Standardized headers to simulate clean browser handshakes
HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Connection': 'keep-alive'
}

# ---------------------------------------------------------
# HARDCODED SPREADSHEET MATRIX (From Your Provided PDF Sheets)
# ---------------------------------------------------------
HISTORICAL_LEDGER = {
    "michael jordan": {
        "metadata": {"id": 893, "full_name": "Michael Jordan", "is_active": False},
        "overall": {
            "Finals Record": "6-0", "Wins Per Finals": "4.0", "Margin of W/L (Games)": "2.17",
            "Career Playoff BPM": "11.40", "Career Playoff PER": "28.78", "Losses to Future Champions": "4",
            "Times Missing Playoffs": "2 (2002, 2003)", "Avg 1st Rd Opp Off Rating": "11.89", "Avg 1st Rd Opp Def Rating": "13.06"
        },
        "making_finals_splits": {
            "Metric Group": ["1st Rd Opp Offense", "1st Rd Opp Defense", "1st Rd Series Length", "Conf Semi Opp Offense", "Conf Semi Opp Defense", "Conf Semi Series Length"],
            "Value/Rank": ["14.33", "15.33", "3.5 Games", "11.33", "7.67", "5.17 Games"]
        },
        "missing_finals_splits": {
            "Metric Group": ["1st Rd Opp Offense", "1st Rd Opp Defense", "1st Rd Net Rating", "Conf Semi Opp Offense", "Conf Semi Opp Defense", "Conf Semi Series Length"],
            "Value/Rank": ["12.38", "5.50", "6.37", "4.67", "9.33", "5.33 Games"]
        },
        "teammates": {
            "Teammate": ["Scottie Pippen", "Horace Grant", "Dennis Rodman", "Toni Kukoc", "Orlando Woolridge"],
            "Peak Postseason Context": ["All-NBA 1st Team, All-Defense 1st", "All-Defense 2nd Team, Core Rim Protector", "Elite Rebounding Engine, All-Defense", "6th Man of the Year, Playmaking Wing", "Early Career Scoring Support (0.153 WS/48)"]
        }
    },
    "lebron james": {
        "metadata": {"id": 2544, "full_name": "LeBron James", "is_active": True},
        "overall": {
            "Finals Record": "4-6", "Wins Per Finals": "2.2", "Margin of W/L (Games)": "-1.10",
            "Career Playoff BPM": "10.44", "Career Playoff PER": "26.00", "Losses to Future Champions": "2",
            "Times Missing Playoffs": "4 (04, 05, 19, 22)", "Avg 1st Rd Opp Off Rating": "13.39", "Avg 1st Rd Opp Def Rating": "13.03"
        },
        "making_finals_splits": {
            "Metric Group": ["1st Rd Opp Offense", "1st Rd Opp Defense", "1st Rd Series Length", "Conf Semi Opp Offense", "Conf Semi Opp Defense", "Conf Semi Series Length"],
            "Value/Rank": ["14.40", "12.80", "4.5 Games", "12.50", "9.50", "4.93 Games"]
        },
        "missing_finals_splits": {
            "Metric Group": ["1st Rd Opp Offense", "1st Rd Opp Defense", "1st Rd Net Rating", "Conf Semi Opp Offense", "Conf Semi Opp Defense", "Conf Semi Series Length"],
            "Value/Rank": ["12.38", "12.25", "13.75", "14.67", "9.33", "5.33 Games"]
        },
        "teammates": {
            "Teammate": ["Dwyane Wade", "Kyrie Irving", "Anthony Davis", "Chris Bosh", "Kevin Love"],
            "Peak Postseason Context": ["All-NBA Finish / Elite Per-Game Impact", "Clutch Scoring Guard (0.143 WS/48)", "All-NBA 1st Team / Defensive Engine (0.210 WS/48)", "All-Star / Defensive Spaces Setter", "Double-Double Machine / Floor Spacing Big"]
        }
    }
}

# ---------------------------------------------------------
# ENGINE PART 1: PLAYER RESOLUTION MATRIX
# ---------------------------------------------------------
search_input = st.text_input("Enter NBA Player Name (e.g., Michael Jordan, LeBron James, Kobe Bryant, Stephen Curry):", value="Michael Jordan")

resolved_player = None
if search_input.strip():
    trace_step("Identity Resolution", "Initiated", f"User queried string input: '{search_input}'")
    
    # We use a localized base library dictionary map for fast identification across common players
    from nba_api.stats.static import players
    try:
        all_players_list = players.get_players()
        matches = [p for p in all_players_list if search_input.lower() in p['full_name'].lower()]
        trace_step("Static DB Scan", "Success", f"Scanned local runtime array. Identified {len(matches)} historical name intersections.")
        
        if matches:
            if len(matches) > 1:
                options_map = {p['full_name']: p for p in matches}
                selected_name = st.selectbox("Multiple historical intersection matches found. Choose profile:", list(options_map.keys()))
                resolved_player = options_map[selected_name]
            else:
                resolved_player = matches[0]
            
            st.success(f"Matched Identity Vector: **{resolved_player['full_name']}** (Internal API ID: {resolved_player['id']}, Active Status: {resolved_player['is_active']})")
            trace_step("Profile Selection", "Committed", f"Bound target context to ID {resolved_player['id']} ({resolved_player['full_name']})")
        else:
            st.error(f"No entry matched the query sequence '{search_input}' in the NBA encyclopedia registry.")
            trace_step("Profile Selection", "Failed", f"Query '{search_input}' could not be matched.")
    except Exception as db_err:
        trace_step("Static DB Scan", "Exception", str(db_err))

# ---------------------------------------------------------
# ENGINE PART 2: FAULT-TOLERANT NETWORK API CALLER
# ---------------------------------------------------------
def make_api_request_with_retry(url, label, max_retries=3, base_timeout=10):
    """Executes network calls with incremental backoff timeouts and clear step tracing."""
    for attempt in range(1, max_retries + 1):
        current_timeout = base_timeout * attempt
        trace_step(f"Network Handshake - {label}", "Pending", f"Attempt {attempt}/{max_retries} | Dispatched target timeout frame: {current_timeout}s")
        
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=current_timeout) as response:
                status_code = response.getcode()
                trace_step(f"Network Handshake - {label}", "Connected", f"Server returned HTTP status code {status_code} on attempt {attempt}")
                raw_payload = response.read().decode('utf-8')
                parsed_data = json.loads(raw_payload)
                trace_step(f"JSON Payload Parsing - {label}", "Success", f"Correctly mapped object dictionary keys: {list(parsed_data.keys())}")
                return parsed_data
        except Exception as net_err:
            trace_step(f"Network Handshake - {label}", f"Attempt {attempt} Failed", f"Exception Type: {type(net_err).__name__} | Details: {str(net_err)}")
            time.sleep(1.0 * attempt) # Incremental pacing wait
            
    trace_step(f"Network Handshake - {label}", "Exhausted", f"Failed to open live payload channel after {max_retries} full routing iterations.")
    return None

def fetch_live_career_stats(player_id):
    """Hits the explicit PlayerCareerStats endpoint with direct JSON breakdown parsing."""
    url = f"https://stats.nba.com/stats/playercareerstats?LeagueID=00&PerMode=PerGame&PlayerID={player_id}"
    data = make_api_request_with_retry(url, "PlayerCareerStats")
    
    if data and "resultSets" in data:
        # Position index 2 traditionally maps out SeasonTotalsPostSeason in the data arrays
        try:
            result_sets = data["resultSets"]
            post_season_set = None
            for rs in result_sets:
                if rs.get("name") == "SeasonTotalsPostSeason":
                    post_season_set = rs
                    break
            
            if not post_season_set and len(result_sets) >= 3:
                post_season_set = result_sets[2]
                
            if post_season_set:
                headers = post_season_set.get("headers", [])
                rows = post_season_set.get("rowSet", [])
                df = pd.DataFrame(rows, columns=headers)
                trace_step("DataFrame Extraction", "Success", f"Constructed frame with dimension matrix {df.shape}")
                return df
        except Exception as parse_err:
            trace_step("DataFrame Extraction", "Exception", str(parse_err))
    return pd.DataFrame()

# ---------------------------------------------------------
# EXECUTION ROUTER & INTERACTIVE SCORING LAYOUT
# ---------------------------------------------------------
if resolved_player:
    p_id = resolved_player['id']
    p_name = resolved_player['full_name']
    p_key = p_name.lower().strip()
    
    # Trigger the network pipeline
    with st.spinner("Connecting to official stats server network corridors..."):
        raw_postseason_summary_df = fetch_live_career_stats(p_id)
        
    # ROUTING CHECK: Did the cloud request time out / fail? If yes, look for a spreadsheet fallback
    using_fallback = False
    if raw_postseason_summary_df.empty:
        trace_step("Data Routing Engine", "API Blocked / Empty", "Redirecting execution pathway to Local Spreadsheet Fallback Registry.")
        if p_key in HISTORICAL_LEDGER:
            using_fallback = True
            st.sidebar.warning("⚡ API Throttling Detected: Local Spreadsheet Fallback Active")
        else:
            st.error("❌ Network Endpoint Timeout: The NBA server blocked this request, and no local spreadsheet backup is present for this specific player.")
            
    # --- RENDER BLOCK A: IF NATIVE LIVE API SUCCEEDED ---
    if not raw_postseason_summary_df.empty and not using_fallback:
        st.header(f"📊 Real-Time Postseason Footprint: {p_name}")
        st.info(" Authentic data stream delivered successfully from stats.nba.com")
        
        # Display the live parsed summary table
        st.dataframe(raw_postseason_summary_df, use_container_width=True)
        
        # Basic dynamic metric highlights calculated from the live rows
        if "PTS" in raw_postseason_summary_df.columns and "GP" in raw_postseason_summary_df.columns:
            raw_postseason_summary_df["PTS"] = pd.to_numeric(raw_postseason_summary_df["PTS"], errors="coerce").fillna(0)
            raw_postseason_summary_df["GP"] = pd.to_numeric(raw_postseason_summary_df["GP"], errors="coerce").fillna(0)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Recorded Playoff Campaigns", f"{len(raw_postseason_summary_df)}")
            c2.metric("Total Postseason Appearances (GP)", f"{int(raw_postseason_summary_df['GP'].sum())}")
            c3.metric("Peak Scoring Postseason PPG", f"{raw_postseason_summary_df['PTS'].max():.1f}")

    # --- RENDER BLOCK B: IF FALLBACK MATRIX TRIGGERS (JORDAN / LEBRON SHEET DATA) ---
    elif using_fallback:
        ledger = HISTORICAL_LEDGER[p_key]
        
        st.header(f"📋 Verified Advanced Ledger Overview: {p_name}")
        st.caption("Displaying exact macro-tracking analytics and split metrics extracted directly from your comparative sheet.")
        
        # 1. Macro KPI Columns
        m_cols = st.columns(4)
        keys_list = list(ledger["overall"].keys())
        for idx, key in enumerate(keys_list[:4]):
            m_cols[idx % 4].metric(key, ledger["overall"][key])
            
        m_cols_2 = st.columns(4)
        for idx, key in enumerate(keys_list[4:8]):
            m_cols_2[idx % 4].metric(key, ledger["overall"][key])
            
        # 2. Main Tabbed Panels for Splits and Teammate Profiles
        t1, t2, t3 = st.tabs(["🎯 Postseason Condition Splits", "🤝 Historical Teammate Context", "📈 Overall Career Summary Profile"])
        
        with t1:
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown(f"#### **When Making the Finals ({p_name})**")
                st.dataframe(pd.DataFrame(ledger["making_finals_splits"]), use_container_width=True, hide_index=True)
            with col_right:
                st.markdown(f"#### **When Missing the Finals ({p_name})**")
                st.dataframe(pd.DataFrame(ledger["missing_finals_splits"]), use_container_width=True, hide_index=True)
                
        with t2:
            st.markdown(f"#### **Primary Supporting Advanced Context Logs**")
            st.markdown("Automated lookup tracking of high-impact rotation units to evaluate historical help context metrics:")
            st.dataframe(pd.DataFrame(ledger["teammates"]), use_container_width=True, hide_index=True)
            
        with t3:
            st.markdown(f"#### **Complete Career Tracking Parameters Summary**")
            all_meta_summary = [{"Metric Parameter": k, "Value Pinpoint": v} for k, v in ledger["overall"].items()]
            st.dataframe(pd.DataFrame(all_meta_summary), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TECHNICAL INTERNALS LOG TRACER WINDOW
# ---------------------------------------------------------
if show_tracer:
    st.markdown("---")
    with st.expander("🔧 Technical Execution Step-by-Step Tracer Logs", expanded=True):
        st.markdown("""
        **System Core Diagnosis Panel:** Track runtime performance vectors below. 
        If an operation returns empty sheets, use this trace sequence to identify exactly where the network socket or parameter parsing shifted.
        """)
        
        if st.session_state.tech_debug_logs:
            # We display them in descending chronological order so the newest logs sit on top
            for entry in reversed(st.session_state.tech_debug_logs):
                st.text(entry)
        else:
            st.info("No network signals, tracing loops, or runtime exceptions logged inside this current context window yet.")
