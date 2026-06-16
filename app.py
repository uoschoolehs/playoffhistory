import streamlit as st
import pandas as pd
import urllib.request
import urllib.parse
import json
import time

# Page configuration for a professional scouting dashboard
st.set_page_config(page_title="Universal NBA Postseason Engine", layout="wide", page_icon="🏀")

st.title("🏀 Universal Postseason Lookup Engine")
st.markdown("""
This platform implements a dynamic network routing matrix to query live playoff statistics for **any NBA player across any era**. 
To circumvent data-center IP blocks implemented by official firewalls, this engine wraps live requests through a multi-node public gateway proxy system.
""")

# Standardized browser identity headers to simulate clean traffic
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
}

# Dynamic Tracking System for complete transparency
if "execution_logs" not in st.session_state:
    st.session_state.execution_logs = []

def log_debug_step(step, status, context=""):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.execution_logs.append(f"[{timestamp}] [{step.upper()}] Status: {status.upper()} | {context}")

# Sidebar controller
st.sidebar.header("🔧 System Core Control Router")
show_logs = st.sidebar.checkbox("Show Live Step Execution Logs", value=True)
if st.sidebar.button("Reset Session Engine"):
    st.session_state.execution_logs = []
    st.rerun()

# ---------------------------------------------------------
# PHASE 1: DYNAMIC IDENTITY INTERSECTION RESOLUTION
# ---------------------------------------------------------
# Pulls directly from the built-in static package array (instant, zero network calls required)
from nba_api.stats.static import players

search_term = st.text_input("Search Player Name (e.g., Michael Jordan, LeBron James, Kobe Bryant, Victor Wembanyama):", value="Michael Jordan")

resolved_player = None

if search_term.strip():
    log_debug_step("Identity Resolution", "Initiated", f"Searching string profile: '{search_term}'")
    try:
        all_players = players.get_players()
        # Scan for any substring name matches across the entire NBA encyclopedia array
        matched_profiles = [p for p in all_players if search_term.lower() in p['full_name'].lower()]
        
        if matched_profiles:
            log_debug_step("Local Registry Filter", "Success", f"Identified {len(matched_profiles)} match vectors.")
            if len(matched_profiles) > 1:
                profile_options = {p['full_name']: p for p in matched_profiles}
                selected_name = st.selectbox("Multiple matching player profiles found. Select target profile:", list(profile_options.keys()))
                resolved_player = profile_options[selected_name]
            else:
                resolved_player = matched_profiles[0]
                
            st.success(f"🎯 **Bound Target Profile:** {resolved_player['full_name']} (ID: {resolved_player['id']} | Active Status: {resolved_player['is_active']})")
        else:
            st.error(f"No player vector found matching '{search_term}' in the historical database.")
            log_debug_step("Local Registry Filter", "Failed", f"No record intersections found.")
    except Exception as e:
        log_debug_step("Local Registry Filter", "Exception", str(e))

# ---------------------------------------------------------
# PHASE 2: PROXIED MULTI-NODE NETWORK CALLER ENGINE
# ---------------------------------------------------------
def fetch_proxied_nba_stats(player_id):
    """
    Constructs a live query to the official NBA Stats API, routing requests through 
    public node structures to prevent cloud data-center blocklists from dropping packets.
    """
    base_target_url = f"https://stats.nba.com/stats/playercareerstats?LeagueID=00&PerMode=PerGame&PlayerID={player_id}"
    
    # Sequence of dynamic alternative proxy bypass tunnels
    routing_strategies = [
        {
            "name": "Node A (AllOrigins Gateway)",
            "url_factory": lambda target: f"https://api.allorigins.win/raw?url={urllib.parse.quote_plus(target)}"
        },
        {
            "name": "Node B (CORSProxy Bypass)",
            "url_factory": lambda target: f"https://corsproxy.io/?{urllib.parse.quote_plus(target)}"
        },
        {
            "name": "Node C (Direct Connection Ingress)",
            "url_factory": lambda target: target
        }
    ]
    
    for strategy in routing_strategies:
        node_name = strategy["name"]
        proxied_url = strategy["url_factory"](base_target_url)
        log_debug_step("Network Dispatch", "Pending", f"Attempting connection handshake via {node_name}")
        
        try:
            req = urllib.request.Request(proxied_url, headers=HEADERS)
            # 8-second execution cutoff per channel to keep performance fast
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.getcode() == 200:
                    raw_data = response.read().decode('utf-8')
                    parsed_json = json.loads(raw_data)
                    log_debug_step("Network Dispatch", "Connected", f"Payload verified and extracted via {node_name}")
                    return parsed_json
        except Exception as err:
            log_debug_step("Network Dispatch", "Throttled / Failed", f"Channel {node_name} returned exception: {type(err).__name__}")
            continue
            
    log_debug_step("Network Core Execution", "Exhausted", "All network bypass routing channels failed to resolve standard frames.")
    return None

# ---------------------------------------------------------
# PHASE 3: METRIC ISOLATION & DATAFRAME RENDERING
# ---------------------------------------------------------
if resolved_player:
    player_id = resolved_player['id']
    player_name = resolved_player['full_name']
    
    with st.spinner(f"Extracting historical postseason frames for {player_name}..."):
        api_payload = fetch_proxied_nba_stats(player_id)
        
    if api_payload and "resultSets" in api_payload:
        try:
            result_sets = api_payload["resultSets"]
            postseason_data_set = None
            
            # Extract the correct postseason data grid array from the full payload
            for rs in result_sets:
                if rs.get("name") == "SeasonTotalsPostSeason":
                    postseason_data_set = rs
                    break
                    
            if postseason_data_set and postseason_data_set.get("rowSet"):
                headers = postseason_data_set.get("headers", [])
                rows = postseason_data_set.get("rowSet", [])
                
                # Assemble the complete historical dataframe dynamically
                df_postseason = pd.DataFrame(rows, columns=headers)
                
                st.header(f"📊 Real-Time Postseason Ledger: {player_name}")
                st.markdown(f"Displaying dynamic career playoff records extracted directly from official statistics.")
                
                # Render clean dataframe view
                st.dataframe(df_postseason, use_container_width=True, hide_index=True)
                
                # Calculate interactive KPI analysis chips from the data matrix live
                if "PTS" in df_postseason.columns and "GP" in df_postseason.columns:
                    df_postseason["PTS"] = pd.to_numeric(df_postseason["PTS"], errors="coerce").fillna(0)
                    df_postseason["GP"] = pd.to_numeric(df_postseason["GP"], errors="coerce").fillna(0)
                    
                    kpi1, kpi2, kpi3 = st.columns(3)
                    kpi1.metric("Playoff Campaigns", f"{len(df_postseason)}")
                    kpi2.metric("Total Postseason Games (GP)", f"{int(df_postseason['GP'].sum())}")
                    kpi3.metric("Peak Playoff Scoring Season (PPG)", f"{df_postseason['PTS'].max():.1f}")
            else:
                st.info(f"ℹ️ Core profile successfully queried, but **{player_name}** has no recorded active career NBA postseason appearances.")
                log_debug_step("Data Isolation", "Empty Return", "Player data resolved but contains 0 playoff vectors.")
                
        except Exception as parse_error:
            st.error("Parsing anomaly encountered during dataframe structural generation mapping.")
            log_debug_step("Data Isolation", "Parsing Exception", str(parse_error))
    else:
        st.error("❌ Complete Routing Outage: The live engine could not bypass firewall locks via any proxy node channel.")

# ---------------------------------------------------------
# TECHNICAL INTERNALS LOG TRACER WINDOW
# ---------------------------------------------------------
if show_logs:
    st.markdown("---")
    with st.expander("🔧 Step-by-Step System Internal Debug Logs", expanded=True):
        if st.session_state.execution_logs:
            for log in reversed(st.session_state.execution_logs):
                st.text(log)
        else:
            st.caption("Awaiting user profile inputs to capture engine performance tracing logs.")
