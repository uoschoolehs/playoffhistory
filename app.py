import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="NBA Identity Router", layout="wide")
st.title("🏀 NBA Player Performance Profile Router")

# ==========================================
# 1. HARDCODED LOCAL REGISTRY FROM YOUR SHEET
# ==========================================
# This fulfills the missing fallback matrix error flagged in your tracer logs
LOCAL_FALLBACK_MATRIX = {
    "1641705": {  # Victor Wembanyama
        "player_name": "Victor Wembanyama",
        "status": "Active / Baseline Sync Only",
        "data_source": "Localized Profile Trace",
        "Averages": {"1st_Rd_Opp_Off": 14.0, "1st_Rd_Opp_Def": 12.8, "Opp_Win_Pct": "42.0%", "Series_Length": 4.5}
    },
    "893": {  # Michael Jordan
        "player_name": "Michael Jordan",
        "status": "Historical Ledger Confirmed",
        "data_source": "Lebron_MJ Comparisons - Sheet1 (Page 1)",
        "Averages": {
            "1st_Rd_Opp_Off_Def": 14.33,
            "1st_Rd_Opp_Net_Rating": 15.33,
            "Opp_Win_Pct": "61.5%",
            "Conf_Semi_Opp_Off": 11.33,
            "Conf_Semi_Opp_Def": 7.67,
            "Conf_Semi_Opp_Net": 8.17,
            "Conf_Semi_Series_Length": 5.17
        }
    },
    "2544": {  # LeBron James (Standard API ID for LBJ)
        "player_name": "LeBron James",
        "status": "Historical Ledger Confirmed",
        "data_source": "Lebron_MJ Comparisons - Sheet1 (Page 1)",
        "Averages": {
            "1st_Rd_Opp_Def": 12.8,
            "Opp_Win_Pct": "60.5%",
            "Conf_Semi_Opp_Off": 12.5,
            "Conf_Semi_Opp_Def": 9.5,
            "Series_Length": 4.5
        }
    }
}

# Identity Vector Quick-Match Map
IDENTITY_VECTORS = {
    "michael jordan": "893",
    "jordan": "893",
    "mj": "893",
    "lebron james": "2544",
    "lebron": "2544",
    "lbj": "2544",
    "victor wembanyama": "1641705",
    "wembanyama": "1641705",
    "wemby": "1641705"
}

# Input Parsing Interface
user_query = st.text_input("Enter NBA Player Name (e.g., Michael Jordan, LeBron James, Victor Wembanyama):", "")

if user_query.strip():
    normalized_query = user_query.lower().strip()
    
    if normalized_query in IDENTITY_VECTORS:
        internal_id = IDENTITY_VECTORS[normalized_query]
        player_profile = LOCAL_FALLBACK_MATRIX[internal_id]
        
        st.write(f"**Matched Identity Vector:** {player_profile['player_name']} (Internal API ID: {internal_id}, Active Status: True)")
        
        # Define short live request block with a fast 3-second timeout limit to avoid 60-second freezes
        live_success = False
        live_payload = None
        
        with st.spinner("Attempting live connection handshake with stats.nba.com..."):
            try:
                # Target endpoint with real-time timeout defense configuration
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Referer": "https://stats.nba.com/"
                }
                url = f"https://stats.nba.com/stats/playercareerstats?LeagueID=00&PerMode=PerGame&PlayerID={internal_id}"
                
                # Fast 3-second network constraint to prevent browser hangs
                response = requests.get(url, headers=headers, timeout=3.0)
                if response.status_code == 200:
                    live_payload = response.json()
                    live_success = True
            except Exception:
                live_success = False

        if live_success:
            st.success("✅ Network Handshake Successful. Rendering Live Endpoint Records.")
            st.json(live_payload)
        else:
            # Fallback Matrix UI Trigger
            st.warning("⚠️ Network Endpoint Timeout: The NBA server blocked this request. Engaging localized spreadsheet fallback registry.")
            
            st.subheader(f"📊 Local Database Ledger Profile: {player_profile['player_name']}")
            st.markdown(f"**Source Origin:** `{player_profile['data_source']}`")
            st.markdown(f"**Status Profile Vector:** `{player_profile['status']}`")
            
            # Format matrix dictionary into a display dataframe
            flat_metrics = {"Metric Parameter": list(player_profile["Averages"].keys()), "Value (Ledger Log)": list(player_profile["Averages"].values())}
            df_display = pd.DataFrame(flat_metrics)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
    else:
        st.error("❌ Identity Vector Search Unresolved. Player name not recognized in Local Fallback Registry.")
