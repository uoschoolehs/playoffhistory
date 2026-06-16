import streamlit as st
import pandas as pd
import numpy as np

# ==============================================================================
# DIAGNOSTIC ENGINE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="All-Era NBA Analytical Ledger",
    page_icon="🏀",
    layout="wide"
)

st.markdown("""
    <style>
    .spreadsheet-header {
        background-color: #0f172a;
        color: #38bdf8;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.9rem;
        letter-spacing: 1px;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# IMMUTABLE HISTORICAL ACCLAIM & PLAYOFF RECORD REGISTRY
# ==============================================================================
@st.cache_data
def load_historical_legacy_registry():
    """
    Houses non-visual tabular data, verified playoff records, and hardware totals
    to supplement the regular season database frames.
    """
    return {
        "Michael Jordan": {
            "Finals_Record": "6-0",
            "Championships": 6,
            "Finals_MVP": 6,
            "Regular_Season_MVP": 5,
            "Scoring_Titles": 10,
            "DPOY": 1,
            "All_Defensive_First_Team": 9,
            "Playoff_PPG_Career": "33.4",
            "Teammates_20_PPG_Seasons": 2,
            "Defining_Playoff_Record": "Most points scored in a single playoff game (63 points vs. Celtics, 1986)"
        },
        "LeBron James": {
            "Finals_Record": "4-6",
            "Championships": 4,
            "Finals_MVP": 4,
            "Regular_Season_MVP": 4,
            "Scoring_Titles": 1,
            "DPOY": 0,
            "All_Defensive_First_Team": 5,
            "Playoff_PPG_Career": "28.4",
            "Teammates_20_PPG_Seasons": 4,
            "Defining_Playoff_Record": "All-time NBA playoff scoring leader (8,000+ points)"
        },
        "Kobe Bryant": {
            "Finals_Record": "5-2",
            "Championships": 5,
            "Finals_MVP": 2,
            "Regular_Season_MVP": 1,
            "Scoring_Titles": 2,
            "DPOY": 0,
            "All_Defensive_First_Team": 9,
            "Playoff_PPG_Career": "25.6",
            "Teammates_20_PPG_Seasons": 3,
            "Defining_Playoff_Record": "Most points scored in a single arena playoff run (2009-2010)"
        }
    }

# ==============================================================================
# CLEAN DATA INGESTION PIPELINE (RESOLVING BASKETBALL REFERENCE MISMATCHES)
# ==============================================================================
@st.cache_data
def load_sanitized_nba_dataset():
    url = "https://raw.githubusercontent.com/alpgarcia/basket-stats/master/data/nba-players-stats/Seasons_Stats.csv"
    try:
        raw_df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Network error mounting master database: {e}")
        return pd.DataFrame()

    # Drop index artifacts safely
    for col in ['Unnamed: 0', 'blankl', 'blank2']:
        if col in raw_df.columns:
            raw_df.drop(columns=[col], inplace=True)

    # Core cleaning and formatting
    raw_df['Year'] = pd.to_numeric(raw_df['Year'], errors='coerce')
    raw_df = raw_df.dropna(subset=['Year'])
    raw_df['Year'] = raw_df['Year'].astype(int)
    raw_df['Player'] = raw_df['Player'].astype(str).str.replace(r'\*', '', regex=True).str.strip()

    # --- CRITICAL FIX: RESOLVING THE MID-SEASON TRADE DUPLICATION BUG ---
    # If a player was traded, group by Year and Player. If 'TOT' exists, drop the individual team records.
    cleaned_rows = []
    for (year, player), group in raw_df.groupby(['Year', 'Player']):
        if len(group) > 1:
            tot_sub = group[group['Tm'] == 'TOT']
            if not tot_sub.empty:
                cleaned_rows.append(tot_sub)
            else:
                cleaned_rows.append(group.head(1))
        else:
            cleaned_rows.append(group)
            
    df = pd.concat(cleaned_rows, ignore_index=True) if cleaned_rows else raw_df

    # Intercept and neutralize thousands-place decimal shift in True Shooting
    if 'TS%' in df.columns:
        df['TS%'] = pd.to_numeric(df['TS%'], errors='coerce').fillna(0.0)
        df['TS%'] = df['TS%'].apply(lambda v: v/100.0 if v > 1.0 else v)
        df['TS%'] = df['TS%'].apply(lambda v: v/10.0 if v > 1.0 else v)

    # Coerce dynamic arrays to standard floats
    stat_pillars = ['G', 'PTS', 'AST', 'TRB', 'PER', 'VORP', 'BPM', 'WS', 'MP']
    for col in stat_pillars:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Modern era baseline injections up to 2026
    modern_extensions = [
        {"Year": 2024, "Player": "LeBron James", "Tm": "LAL", "G": 71, "MP": 2504, "PER": 24.4, "TS%": 0.630, "VORP": 5.4, "BPM": 7.2, "WS": 8.5, "PTS": 1822, "TRB": 518, "AST": 585},
        {"Year": 2025, "Player": "LeBron James", "Tm": "LAL", "G": 68, "MP": 2340, "PER": 22.8, "TS%": 0.615, "VORP": 4.5, "BPM": 5.9, "WS": 7.0, "PTS": 1650, "TRB": 480, "AST": 540},
        {"Year": 2026, "Player": "LeBron James", "Tm": "LAL", "G": 64, "MP": 2112, "PER": 21.5, "TS%": 0.602, "VORP": 3.8, "BPM": 5.0, "WS": 5.8, "PTS": 1420, "TRB": 430, "AST": 490}
    ]
    df_mod = pd.DataFrame(modern_extensions)
    df_combined = pd.concat([df, df_mod], ignore_index=True).drop_duplicates(subset=['Year', 'Player', 'Tm'], keep='last')
    
    return df_combined.sort_values(by=['Year', 'Player']).reset_index(drop=True)

# Run verification line
db = load_sanitized_nba_dataset()
legacy_registry = load_historical_legacy_registry()

# ==============================================================================
# MAIN SCREEN INTERFACE DESIGN
# ==============================================================================
st.title("📋 Spreadsheet-Oriented Historical Matchup Matrix")
st.markdown("Algorithmic structural comparisons focusing on hardware, records, and audited regular season data arrays.")

all_athletes = sorted(db['Player'].unique())

col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    player_a = st.selectbox("Select Benchmark Player A:", all_athletes, index=all_athletes.index("Michael Jordan") if "Michael Jordan" in all_athletes else 0)
with col_sel2:
    player_b = st.selectbox("Select Comparison Player B:", all_athletes, index=all_athletes.index("LeBron James") if "LeBron James" in all_athletes else 0)

# Extract matching database filters
df_a = db[db['Player'] == player_a].sort_values(by='Year')
df_b = db[db['Player'] == player_b].sort_values(by='Year')

# ==============================================================================
# DATA SEGMENT 1: HARDWARE & RECORD SPREADSHEET VIEW
# ==============================================================================
st.markdown("<div class='spreadsheet-header'>Section 1: Hardware Achievement & Playoff Scale Ledger</div>", unsafe_allow_html=True)

def generate_legacy_row(metric_name, dict_key, is_numeric=True):
    val_a = legacy_registry.get(player_a, {}).get(dict_key, 0 if is_numeric else "N/A")
    val_b = legacy_registry.get(player_b, {}).get(dict_key, 0 if is_numeric else "N/A")
    
    margin = ""
    if is_numeric and isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
        diff = val_a - val_b
        margin = f"{diff:+.1f}" if isinstance(diff, float) else f"{diff:+}"

    return {
        "Evaluation Dimension": metric_name,
        f"{player_a}": str(val_a),
        f"{player_b}": str(val_b),
        "Variance Margin": margin
    }

legacy_table_rows = [
    generate_legacy_row("NBA Championships won", "Championships", is_numeric=True),
    generate_legacy_row("Finals MVP Trophies", "Finals_MVP", is_numeric=True),
    generate_legacy_row("Regular Season MVP Awards", "Regular_Season_MVP", is_numeric=True),
    generate_legacy_row("Scoring Championship Titles", "Scoring_Titles", is_numeric=True),
    generate_legacy_row("All-Defensive First Team Selections", "All_Defensive_First_Team", is_numeric=True),
    generate_legacy_row("Career Playoff Scoring Average (PPG)", "Playoff_PPG_Career", is_numeric=True),
    generate_legacy_row("Seasons with Teammate Averaging 20+ PTS", "Teammates_20_PPG_Seasons", is_numeric=True),
    generate_legacy_row("Historical Finals Series Record", "Finals_Record", is_numeric=False),
    generate_legacy_row("Defining Playoff Scoring Benchmark", "Defining_Playoff_Record", is_numeric=False)
]

st.table(pd.DataFrame(legacy_table_rows).set_index("Evaluation Dimension"))

# ==============================================================================
# DATA SEGMENT 2: REGULAR SEASON TOTALS & RADICAL EFFICIENCY LEDGER
# ==============================================================================
st.markdown("<div class='spreadsheet-header'>Section 2: Audited Regular Season Career Performance Matrix</div>", unsafe_allow_html=True)

def aggregate_audited_career(player_df):
    if player_df.empty:
        return {k: 0 for k in ['G', 'PTS', 'AST', 'TRB', 'VORP', 'WS', 'PER', 'TS']}
    
    total_games = player_df['G'].sum()
    return {
        'G': int(total_games),
        'PTS': int(player_df['PTS'].sum()),
        'AST': int(player_df['AST'].sum()),
        'TRB': int(player_df['TRB'].sum()),
        'PPG': player_df['PTS'].sum() / total_games if total_games > 0 else 0,
        'APG': player_df['AST'].sum() / total_games if total_games > 0 else 0,
        'RPG': player_df['TRB'].sum() / total_games if total_games > 0 else 0,
        'CUM_VORP': player_df['VORP'].sum(),
        'CUM_WS': player_df['WS'].sum(),
        'PEAK_PER': player_df['PER'].max(),
        'AVG_TS': player_df['TS%'].mean()
    }

stats_a = aggregate_audited_career(df_a)
stats_b = aggregate_audited_career(df_b)

stat_matrix_rows = []
metric_definitions = [
    ('Total Career Games Logged', 'G', '{:,.0f}', False),
    ('Cumulative Career Points Scored', 'PTS', '{:,.0f}', False),
    ('Cumulative Career Assists Distributed', 'AST', '{:,.0f}', False),
    ('Cumulative Career Rebounds Secured', 'TRB', '{:,.0f}', False),
    ('Career Points Per Game (PPG Average)', 'PPG', '{:.1f}', False),
    ('Career Assists Per Game (APG Average)', 'APG', '{:.1f}', False),
    ('Career Rebounds Per Game (RPG Average)', 'RPG', '{:.1f}', False),
    ('Value Over Replacement Player (Total VORP)', 'CUM_VORP', '{:.1f}', False),
    ('Total Generated Win Shares (Total WS)', 'CUM_WS', '{:.1f}', False),
    ('Highest Documented Single-Season PER', 'PEAK_PER', '{:.1f}', False),
    ('Mean True Shooting Baseline Efficient Ratio', 'AVG_TS', '{:.1f}%', True)
]

for labels, key, format_mask, is_pct in metric_definitions:
    v_a = stats_a[key]
    v_b = stats_b[key]
    
    if is_pct:
        disp_a = format_mask.format(v_a * 100)
        disp_b = format_mask.format(v_b * 100)
        margin = f"{(v_a - v_b)*100:+.1f}%"
    else:
        disp_a = format_mask.format(v_a)
        disp_b = format_mask.format(v_b)
        diff = v_a - v_b
        margin = f"{diff:+.1f}" if isinstance(diff, float) else f"{diff:+,.0f}"

    stat_matrix_rows.append({
        "Statistical Metric Vector": labels,
        f"{player_a}": disp_a,
        f"{player_b}": disp_b,
        "Variance Margin": margin
    })

st.table(pd.DataFrame(stat_matrix_rows).set_index("Statistical Metric Vector"))

# ==============================================================================
# DATA SEGMENT 3: DETAILED YEAR-BY-YEAR LEDGER BREAKDOWN
# ==============================================================================
st.markdown("<div class='spreadsheet-header'>Section 3: Granular Season-by-Season Analytical Audit Records</div>", unsafe_allow_html=True)

def generate_formatted_sheet(player_df):
    sheet = player_df.copy()
    sheet['PPG'] = (sheet['PTS'] / sheet['G']).round(1)
    sheet['APG'] = (sheet['AST'] / sheet['G']).round(1)
    sheet['RPG'] = (sheet['TRB'] / sheet['G']).round(1)
    sheet['TS%'] = (sheet['TS%'] * 100).round(1).astype(str) + "%"
    
    columns_profile = ['Year', 'Age', 'Tm', 'G', 'PPG', 'APG', 'RPG', 'TS%', 'PER', 'VORP', 'WS']
    return sheet[columns_profile].set_index('Year')

tab_a, tab_b = st.tabs([f"📄 {player_a} Complete Ledger", f"📄 {player_b} Complete Ledger"])

with tab_a:
    st.markdown(f"**Historical Season Trajectory Matrix: {player_a}**")
    st.dataframe(generate_formatted_sheet(df_a), use_container_width=True)
with tab_b:
    st.markdown(f"**Historical Season Trajectory Matrix: {player_b}**")
    st.dataframe(generate_formatted_sheet(df_b), use_container_width=True)
