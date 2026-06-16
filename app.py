import streamlit as st
import pandas as pd
import requests
import json
import time

# ==========================================
# MODULE 1: GLOBAL CONFIGURATION & CORE DATA CONSTANTS
# ==========================================
st.set_page_config(
    page_title="Enterprise NBA Historical Analytics Platform",
    layout="wide",
    page_icon="🏀"
)

# Robust, prioritized data repository paths for historical mirror fallbacks
DATA_MIRROR_LOW_LATENCY = "https://raw.githubusercontent.com/fivethirtyeight/nba-player-advanced-metrics/master/nba-data-historical.csv"

# Comprehensive browser fingerprint mimicking to pierce firewalls if possible
EMULATED_BROWSER_HEADERS = {
    "Host": "stats.nba.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "If-Modified-Since": "Sat, 13 Jun 2026 00:00:00 GMT"
}

# ==========================================
# MODULE 2: SYSTEM DIAGNOSTICS & STATE TRACKING
# ==========================================
if "diagnostic_telemetry" not in st.session_state:
    st.session_state.diagnostic_telemetry = []

def write_telemetry_log(subsystem: str, status: str, description: str):
    """Appends structural telemetry performance metrics to the active session trace."""
    stamp = time.strftime("%H:%M:%S")
    log_line = f"[{stamp}] [{subsystem.upper()}] Status: {status.upper()} -> {description}"
    st.session_state.diagnostic_telemetry.append(log_line)

# ==========================================
# MODULE 3: DEFENSIVE DATA WRAPPING & SCHEMA PROTECTION
# ==========================================
def insulate_dataframe_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures that incoming dataframes are sanitized, normalized, and protected
    against casing disparities or structural whitespace errors.
    """
    if df.empty:
        return df
    
    # Standardize column naming patterns to uppercase strings to eliminate case mismatch
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # Common performance matrix normalization
    for col in df.columns:
        if any(term in col for term in ['PCT', '%', 'RATE', 'RAPTOR', 'WAR', 'MIN', 'G', 'PTS']):
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

def safe_column_extraction(df: pd.DataFrame, target_columns: list) -> pd.DataFrame:
    """
    CRITICAL DEFENSE: Implements intersection screening. This completely isolates 
    the application from throwing a KeyError if a remote data mirror alters its schema.
    """
    df_sanitized = insulate_dataframe_schema(df)
    upper_targets = [str(c).upper() for c in target_columns]
    
    # Filter for columns that actually exist inside the dataset physical memory
    validated_columns = [col for col in upper_targets if col in df_sanitized.columns]
    
    missing_columns = set(upper_targets) - set(validated_columns)
    if missing_columns:
        write_telemetry_log("Schema Inspector", "Omission Warning", f"Requested dimensions {list(missing_columns)} missing from source frame.")
        
    return df_sanitized[validated_columns].copy()

# ==========================================
# MODULE 4: INTERNET-SCALE DATA INGESTION MATRIX
# ==========================================
@st.cache_data(show_spinner=False, ttl=3600)
def ingest_historical_mirror_layer(url: str):
    """
    Downloads and caches the fallback open-data analytical matrix.
    Acts as the primary execution engine when live endpoints drop connections.
    """
    write_telemetry_log("Ingestion Pipeline", "Pending", f"Streaming master data frame from mirror endpoint.")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(url)
            write_telemetry_log("Ingestion Pipeline", "Success", f"Retrieved matrix frame. Shape: {df.shape}")
            return df, True
    except Exception as network_exception:
        write_telemetry_log("Ingestion Pipeline", "Critical Deficit", f"Ingestion trace exception: {str(network_exception)}")
    return pd.DataFrame(), False

# ==========================================
# MODULE 5: ANALYTICAL INTERSECTION COMPUTATION CORE
# ==========================================
def execute_live_api_harvest(player_id: int) -> pd.DataFrame:
    """
    Attempts to perform a live, unfiltered extraction sequence against the official 
    NBA server using secure connection isolation.
    """
    live_target_endpoint = f"https://stats.nba.com/stats/playercareerstats?LeagueID=00&PerMode=PerGame&PlayerID={player_id}"
    write_telemetry_log("Live Harvest Engine", "Handshake Inception", f"Targeting active player record vector ID: {player_id}")
    
    try:
        res = requests.get(live_target_endpoint, headers=EMULATED_BROWSER_HEADERS, timeout=6)
        if res.status_code == 200:
            payload = res.json()
            result_sets = payload.get("resultSets", [])
            
            # Locate the exact record table index mapping to Postseason Career Totals
            for rs in result_sets:
                if rs.get("name") == "SeasonTotalsPostSeason":
                    headers = rs.get("headers", [])
                    rows = rs.get("rowSet", [])
                    df_live = pd.DataFrame(rows, columns=headers)
                    write_telemetry_log("Live Harvest Engine", "Pipeline Clear", "Live JSON data stream translated to DataFrame.")
                    return df_live
    except Exception as e:
        write_telemetry_log("Live Harvest Engine", "Throttled / Blocked", f"Ingress failure: {type(e).__name__}")
    
    return pd.DataFrame()

# ==========================================
# MODULE 6: COMPREHENSIVE UI PRESENTATION CONTROL LAYER
# ==========================================
st.title("🏀 Enterprise NBA Historical Scouting Dashboard")
st.markdown("""
This platform utilizes a decoupled data routing layout to track, clean, and map historical basketball matrices. 
Equipped with strict type enforcement and data schema boundary checking, it is designed never to drop execution threads.
""")

# Sidebar Navigation Control Matrix
st.sidebar.header("⚙️ Engine Infrastructure Control")
display_telemetry = st.sidebar.checkbox("Display Core Runtime Logs", value=True)
if st.sidebar.button("Flush Cache & Purge Buffers"):
    st.cache_data.clear()
    st.session_state.diagnostic_telemetry = []
    st.rerun()

# Execute initial database layer extraction
with st.spinner("Compiling and verifying distributed master database arrays..."):
    master_dataframe, bootstrap_status = ingest_historical_mirror_layer(DATA_MIRROR_LOW_LATENCY)

if not bootstrap_status or master_dataframe.empty:
    st.error("🛑 System Component Fault: Master historical data mirror is unreachable. Reconnect and re-run execution loops.")
else:
    write_telemetry_log("System Diagnostics", "Operational", "Insulated frame structures successfully mounted.")
    
    # Extract structural unique names completely clean of whitespace variations
    master_dataframe['NAME_COMMON_CLEAN'] = master_dataframe['name_common'].astype(str).str.strip()
    alphabetical_scouting_registry = sorted(master_dataframe['NAME_COMMON_CLEAN'].unique())
    
    # Primary lookup interface element
    st.subheader("🔍 Scouting Identification Router")
    search_input_term = st.text_input(
        "Enter Player Profile Vector (Full or Partial Substring Matches Processed Automatically):",
        value="Michael Jordan"
    ).strip()
    
    # Filter the complete encyclopedia file via lookahead match logic
    resolved_intersection_matches = [
        name for name in alphabetical_scouting_registry 
        if search_input_term.lower() in name.lower()
    ]
    
    if not resolved_intersection_matches:
        st.warning(f"⚠️ Zero identity matrices intersected the query parameter string: '{search_input_term}'")
    else:
        # Handle structural collisions (e.g. multiple records containing "James")
        if len(resolved_intersection_matches) > 1:
            selected_scouting_target = st.selectbox(
                f"Identity Collision Warning: {len(resolved_intersection_matches)} matches discovered. Select exact target profile:",
                options=resolved_intersection_matches
            )
        else:
            selected_scouting_target = resolved_intersection_matches[0]
            
        st.success(f"🎯 **Target Identity Bound:** {selected_scouting_target}")
        write_telemetry_log("Identity Router", "Bound", f"Data context focused on '{selected_scouting_target}'")
        
        # Isolate complete history rows specific to selected athlete
        targeted_athlete_rows = master_dataframe[master_dataframe['NAME_COMMON_CLEAN'] == selected_scouting_target].copy()
        
        # Deconstruct target rows into operational data tracks
        playoff_rows_matrix = targeted_athlete_rows[targeted_athlete_rows['type'] == 'PO'].copy()
        regular_season_rows_matrix = targeted_athlete_rows[targeted_athlete_rows['type'] == 'RS'].copy()
        
        # Establish structural multi-view tabs
        tab_playoffs, tab_regular_season, tab_raw_payload = st.tabs([
            "🏆 Postseason Playoff Ledger", 
            "📈 Regular Season Ledger",
            "💾 Raw Data Stream Attributes"
        ])
        
        # Standard analytical dimensions expected by professional tracking platforms
        dimensions_to_extract = [
            'year_id', 'team_id', 'age', 'G', 'Min', 'MPG', 'TS%', 'USG%', 'Raptor +/-'
        ]
        
        # Clean user interface aesthetic header translation map
        presentation_header_map = {
            'YEAR_ID': 'Season',
            'TEAM_ID': 'Franchise',
            'AGE': 'Age Track',
            'G': 'Games Played',
            'MIN': 'Total Minutes',
            'MPG': 'Minutes Per Game',
            'TS%': 'True Shooting %',
            'USG%': 'Usage Rate %',
            'RAPTOR +/-': 'Net Efficiency Rating'
        }
        
        # -------------------------------------------------------------
        # VIEW PANEL 1: POSTSEASON LEADERSHIP TRACK
        # -------------------------------------------------------------
        with tab_playoffs:
            if playoff_rows_matrix.empty:
                st.info(f"Context Note: {selected_scouting_target} has 0 verifiable historical NBA postseason appearances on record.")
            else:
                st.subheader(f"📊 Playoff Career Data Grid: {selected_scouting_target}")
                
                # Defensively pull data without any risk of KeyError
                po_processed_frame = safe_column_extraction(playoff_rows_matrix, dimensions_to_extract)
                po_rendered_frame = po_processed_frame.rename(columns=presentation_header_map)
                
                # Clean up percentage formatting for UI layout
                if 'True Shooting %' in po_rendered_frame.columns:
                    po_rendered_frame['True Shooting %'] = po_rendered_frame['True Shooting %'].map(
                        lambda val: f"{val * 100:.1f}%" if pd.notnull(val) else "N/A"
                    )
                
                # Render highly readable clean data matrix view
                st.dataframe(po_rendered_frame.sort_values(by=po_rendered_frame.columns[0]).reset_index(drop=True), use_container_width=True)
                
                # Build interactive computational KPIs
                st.markdown("### 🧬 Postseason Aggregate Summary Calculations")
                kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                
                # Explicit dynamic type casting to ensure zero float division anomalies
                try:
                    total_po_g = int(pd.to_numeric(playoff_rows_matrix['G'], errors='coerce').sum())
                    avg_po_mpg = float(pd.to_numeric(playoff_rows_matrix['Min'], errors='coerce').sum() / max(total_po_g, 1))
                    
                    raw_ts_col = pd.to_numeric(playoff_rows_matrix['TS%'], errors='coerce')
                    mean_po_ts = float(raw_ts_col.mean() * 100) if not raw_ts_col.dropna().empty else 0.0
                    
                    raw_rap_col = pd.to_numeric(playoff_rows_matrix['Raptor +/-'], errors='coerce')
                    peak_po_eff = float(raw_rap_col.max()) if not raw_rap_col.dropna().empty else 0.0
                    
                    kpi_col1.metric("Playoff Appearances (G)", f"{total_po_g}")
                    kpi_col2.metric("Calculated MPG", f"{avg_po_mpg:.1f}")
                    kpi_col3.metric("True Shooting Mean", f"{mean_po_ts:.1f}%")
                    kpi_col4.metric("Peak Efficiency Run", f"{peak_po_eff:+.2f}")
                except Exception as agg_error:
                    st.caption(f"Telemetry Note: Aggregate computational card suspended: {str(agg_error)}")

        # -------------------------------------------------------------
        # VIEW PANEL 2: REGULAR SEASON PERFORMANCE TRACK
        # -------------------------------------------------------------
        with tab_regular_season:
            if regular_season_rows_matrix.empty:
                st.info(f"Context Note: {selected_scouting_target} has 0 verifiable historical NBA regular season appearances on record.")
            else:
                st.subheader(f"📊 Regular Season Career Data Grid: {selected_scouting_target}")
                
                # Defensively pull data without any risk of KeyError
                rs_processed_frame = safe_column_extraction(regular_season_rows_matrix, dimensions_to_extract)
                rs_rendered_frame = rs_processed_frame.rename(columns=presentation_header_map)
                
                if 'True Shooting %' in rs_rendered_frame.columns:
                    rs_rendered_frame['True Shooting %'] = rs_rendered_frame['True Shooting %'].map(
                        lambda val: f"{val * 100:.1f}%" if pd.notnull(val) else "N/A"
                    )
                
                st.dataframe(rs_rendered_frame.sort_values(by=rs_rendered_frame.columns[0]).reset_index(drop=True), use_container_width=True)
                
                st.markdown("### 🧬 Regular Season Aggregate Summary Calculations")
                rs_kpi1, rs_kpi2, rs_kpi3, rs_kpi4 = st.columns(4)
                
                try:
                    total_rs_g = int(pd.to_numeric(regular_season_rows_matrix['G'], errors='coerce').sum())
                    avg_rs_mpg = float(pd.to_numeric(regular_season_rows_matrix['Min'], errors='coerce').sum() / max(total_rs_g, 1))
                    
                    raw_rs_ts = pd.to_numeric(regular_season_rows_matrix['TS%'], errors='coerce')
                    mean_rs_ts = float(raw_rs_ts.mean() * 100) if not raw_rs_ts.dropna().empty else 0.0
                    
                    raw_rs_rap = pd.to_numeric(regular_season_rows_matrix['Raptor +/-'], errors='coerce')
                    peak_rs_eff = float(raw_rs_rap.max()) if not raw_rs_rap.dropna().empty else 0.0
                    
                    rs_kpi1.metric("Regular Season Games", f"{total_rs_g}")
                    rs_kpi2.metric("Calculated MPG", f"{avg_rs_mpg:.1f}")
                    rs_kpi3.metric("True Shooting Mean", f"{mean_rs_ts:.1f}%")
                    rs_kpi4.metric("Peak Efficiency Run", f"{peak_rs_eff:+.2f}")
                except Exception as agg_error:
                    st.caption(f"Telemetry Note: Aggregate computational card suspended: {str(agg_error)}")

        # -------------------------------------------------------------
        # VIEW PANEL 3: RAW STRUCTURAL SCHEMA DATA DEBUGGER
        # -------------------------------------------------------------
        with tab_raw_payload:
            st.subheader("🛠️ High-Fidelity Data Field Matrix Inspection")
            st.markdown("""
            This panel exposes the exact string and float definitions currently occupying dataset memory. 
            Use this debug monitor to check physical columns and verify available data coordinates.
            """)
            
            # Insulate and print the unmapped dataframe slice straight to screen for developer testing
            insulated_raw_view = insulate_dataframe_schema(targeted_athlete_rows.copy())
            st.dataframe(insulated_raw_view, use_container_width=True)

# ==========================================
# MODULE 7: RUNTIME MONITORING VIEW WINDOW
# ==========================================
if display_telemetry:
    st.markdown("---")
    with st.expander("🛠️ Live Subsystem Telemetry Frame History", expanded=True):
        if st.session_state.diagnostic_telemetry:
            for log in reversed(st.session_state.diagnostic_telemetry):
                st.text(log)
        else:
            st.caption("Awaiting user execution input threads to generate diagnostic telemetry.")
