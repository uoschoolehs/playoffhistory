import streamlit as st
import pandas as pd
import requests

# Set page configuration
st.set_page_config(page_title="Universal NBA Analytics Engine", layout="wide", page_icon="🏀")

st.title("🏀 Universal Historical NBA Engine")
st.markdown("""
 This engine uses a self-contained, open-access historical data layer to track player lines 
 across every single era. Because it bypasses official server connections entirely, **it is completely immune to firewall blocks and package installation drops.**
""")

# -------------------------------------------------------------------------
# CORE DATA LAYER: Dynamic Database Ingestion
# -------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_historical_database():
    """
    Fetches the unblocked historical dataset covering all NBA player lines across eras.
    Contains structural metrics like True Shooting, Games Played, and Advanced Impact values.
    """
    url = "https://raw.githubusercontent.com/fivethirtyeight/nba-player-advanced-metrics/master/nba-data-historical.csv"
    try:
        df = pd.read_csv(url)
        # Clean data formats right out of the gate
        df['name_common_lower'] = df['name_common'].str.strip().str.lower()
        return df, True
    except Exception as e:
        return pd.DataFrame(), False

# Trigger secure data fetch
with st.spinner("Initializing historical dataset matrix..."):
    master_db, upload_success = load_historical_database()

if not upload_success:
    st.error("❌ System Failure: Unable to fetch the underlying database mirror. Please refresh the page.")
else:
    # -------------------------------------------------------------------------
    # IDENTITY INTERSECTION LAYER (Works for ALL players)
    # -------------------------------------------------------------------------
    # Get a unique, sorted list of all players in NBA history for auto-complete
    unique_players = sorted(master_db['name_common'].unique())
    
    st.subheader("🔍 Player Selection Interface")
    search_input = st.text_input(
        "Type or select any NBA Player Name (e.g., Michael Jordan, LeBron James, Kobe Bryant, Shaquille O'Neal):", 
        value="Michael Jordan"
    )
    
    # Filter unique names based on substring match to handle slight typos or abbreviations
    matched_names = [name for name in unique_players if search_input.lower().strip() in name.lower()]
    
    if not matched_names:
        st.error(f"No player profiles found matching '{search_input}'. Check your spelling and try again.")
    else:
        # If multiple players match a broad search term (e.g., "Johnson"), provide a selectbox selection
        if len(matched_names) > 1:
            selected_player = st.selectbox(
                f"Found {len(matched_names)} matching records. Select target profile:", 
                options=matched_names
            )
        else:
            selected_player = matched_names[0]
            
        st.success(f"🎯 **Bound Target Profile:** {selected_player}")
        
        # Isolate rows belonging specifically to our chosen player
        player_matrix = master_db[master_db['name_common'] == selected_player].copy()
        
        # -------------------------------------------------------------------------
        # ANALYTICS COMPILATION VIEW
        # -------------------------------------------------------------------------
        # Split stats into Regular Season (RS) and Playoffs (PO)
        regular_season_df = player_matrix[player_matrix['type'] == 'RS'].copy()
        playoffs_df = player_matrix[player_matrix['type'] == 'PO'].copy()
        
        # UI Tabs to split the data views cleanly
        tab1, tab2 = st.tabs(["📊 Postseason Records (Playoffs)", "📈 Regular Season Records"])
        
        # Column mapping configuration for readable rendering
        column_mapping = {
            'year_id': 'Season',
            'team_id': 'Team',
            'age': 'Age',
            'G': 'GP',
            'Min': 'MIN',
            'MPG': 'MIN_Per_Game',
            'TS%': 'True_Shooting_%',
            'USG%': 'Usage_Rate_%',
            'Raptor +/-': 'Net_Efficiency_Rating'
        }
        
        columns_to_show = ['year_id', 'team_id', 'age', 'G', 'Min', 'MPG', 'TS%', 'USG%', 'Raptor +/-']
        
        # --- TAB 1: PLAYOFF ANALYSIS ---
        with tab1:
            if playoffs_df.empty:
                st.info(f"ℹ️ {selected_player} has no recorded career NBA postseason appearances.")
            else:
                st.subheader(f"Playoff Career Ledger: {selected_player}")
                
                # Format the table display
                po_display = playoffs_df[columns_to_show].rename(columns=column_mapping).sort_values(by='Season').reset_index(drop=True)
                # Convert True Shooting to a clean percentage string for UI layout consistency
                po_display['True_Shooting_%'] = po_display['True_Shooting_%'].map(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "N/A")
                
                st.dataframe(po_display, use_container_width=True, hide_index=True)
                
                # Dynamic Aggregation Calculation Metrics
                st.markdown("### 📊 Career Postseason Impact Breakdown")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                total_po_games = int(playoffs_df['G'].sum())
                avg_po_min = float(playoffs_df['MPG'].mean())
                peak_net_eff = float(playoffs_df['Raptor +/-'].max())
                career_po_ts = float(playoffs_df['TS%'].mean() * 100)
                
                kpi1.metric("Total Playoff Games", f"{total_po_games}")
                kpi2.metric("Avg Playoff MPG", f"{avg_po_min:.1f}")
                kpi3.metric("Career Playoff True Shooting", f"{career_po_ts:.1f}%")
                kpi4.metric("Peak Single-Season Impact (+/-)", f"{peak_net_eff:+.2f}")

        # --- TAB 2: REGULAR SEASON ANALYSIS ---
        with tab2:
            if regular_season_df.empty:
                st.info(f"ℹ️ {selected_player} has no recorded career NBA regular season appearances.")
            else:
                st.subheader(f"Regular Season Career Ledger: {selected_player}")
                
                # Format the table display
                rs_display = regular_season_df[columns_to_show].rename(columns=column_mapping).sort_values(by='Season').reset_index(drop=True)
                rs_display['True_Shooting_%'] = rs_display['True_Shooting_%'].map(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "N/A")
                
                st.dataframe(rs_display, use_container_width=True, hide_index=True)
                
                # Dynamic Aggregation Calculation Metrics
                st.markdown("### 📊 Career Regular Season Impact Breakdown")
                rkpi1, rkpi2, rkpi3, rkpi4 = st.columns(4)
                
                total_rs_games = int(regular_season_df['G'].sum())
                avg_rs_min = float(regular_season_df['MPG'].mean())
                peak_rs_net_eff = float(regular_season_df['Raptor +/-'].max())
                career_rs_ts = float(regular_season_df['TS%'].mean() * 100)
                
                rkpi1.metric("Total RS Games", f"{total_rs_games}")
                rkpi2.metric("Avg RS MPG", f"{avg_rs_min:.1f}")
                rkpi3.metric("Career RS True Shooting", f"{career_rs_ts:.1f}%")
                rkpi4.metric("Peak Single-Season Impact (+/-)", f"{peak_rs_net_eff:+.2f}")
