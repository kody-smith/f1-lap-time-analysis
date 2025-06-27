import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# Team color mapping
team_colors = {
    'Red Bull Racing': '#1E41FF',
    'Mercedes': '#00D2BE',
    'Ferrari': '#DC0000',
    'McLaren': '#FF8700',
    'Aston Martin': '#006F62',
    'Alpine': '#0090FF',
    'Williams': '#005AFF',
    'Alfa Romeo': '#900000',
    'AlphaTauri': '#2B4562',
    'Haas F1 Team': '#FFFFFF',
}

# Secondary team color mapping for visual differentiation
team_secondary_colors = {
    'Red Bull Racing': '#FF1E41',
    'Mercedes': '#007D8A',
    'Ferrari': '#FFA400',
    'McLaren': '#00575B',
    'Aston Martin': "#00C04D",
    'Alpine': '#FF4FF8',
    'Williams': '#002366',
    'Alfa Romeo': '#FFDD00',
    'AlphaTauri': '#C1C7D0',
    'Haas F1 Team': '#999999',
}

# -----------------------------
# Page Config and Theme
# -----------------------------
st.set_page_config(
    page_title="F1 Lap Times Comparison",
    page_icon=":racing_car:",
    layout="wide"
)
st.markdown("""
<style>
    .main {
        background-color: #1E1E1E;
        color: white;
    }
    .block-container {
        padding: 2rem;
    }
    .stSelectbox > div {
        background-color: #2E2E2E;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏎️ F1 Lap Times Comparison")

# -----------------------------
# 1. Get all race sessions
# -----------------------------
sessions_url = "https://api.openf1.org/v1/sessions"
sessions_response = requests.get(sessions_url)

if sessions_response.status_code == 200:
    sessions_data = sessions_response.json()
    sessions_df = pd.DataFrame(sessions_data)
else:
    st.error("Failed to fetch sessions data.")
    st.stop()

# Filter to races only
races_df = sessions_df[sessions_df['session_type'] == "Race"]

# Build a map of meeting_key to meeting_name using the /meetings endpoint
meeting_names = {}
years = races_df['year'].unique()
for year in years:
    meetings_url = f"https://api.openf1.org/v1/meetings?year={year}"
    meetings_response = requests.get(meetings_url)
    if meetings_response.status_code == 200:
        meetings_data = meetings_response.json()
        for m in meetings_data:
            meeting_names[m['meeting_key']] = m['meeting_name']

# Create session selection dict using official meeting names (e.g. 'Bahrain Grand Prix')
session_dict = {
    f"{row['year']} {meeting_names.get(row['meeting_key'], row['circuit_short_name'])}": row['session_key']
    for _, row in races_df.iterrows()
}

# -------------------------------
# 2. Select Session
# -------------------------------
session_name = st.selectbox("Select a Grand Prix", list(session_dict.keys()))
session_key = session_dict[session_name]

# -------------------------------
# 3. Fetch lap data for selected session
# -------------------------------
laps_url = f"https://api.openf1.org/v1/laps?session_key={session_key}"
laps_response = requests.get(laps_url)

if laps_response.status_code == 200:
    laps_data = laps_response.json()
    df = pd.DataFrame(laps_data)
    df = df.dropna(subset=['lap_duration', 'driver_number'])
else:
    st.error("Failed to fetch lap data for this session.")
    st.stop()

# -------------------------------
# 4. Build driver selection options
# -------------------------------
# Fetch driver names
drivers_url = "https://api.openf1.org/v1/drivers"
drivers_response = requests.get(drivers_url)

if drivers_response.status_code == 200:
    drivers_data = drivers_response.json()
    drivers_df = pd.DataFrame(drivers_data)
else:
    st.error("Failed to fetch driver info.")
    st.stop()

# Create mapping: driver_number -> driver full name
# Restrict driver list to those in this session's lap data
valid_driver_numbers = df['driver_number'].unique()

# Extract meeting_key for the selected session
meeting_key = df['meeting_key'].iloc[0] if 'meeting_key' in df.columns else None

# Filter drivers to those in the lap data and from the same meeting
if meeting_key is not None:
    drivers_map = (
        drivers_df[
            (drivers_df['driver_number'].isin(valid_driver_numbers)) &
            (drivers_df['meeting_key'] == meeting_key)
        ][['driver_number', 'full_name']]
        .drop_duplicates()
        .set_index('driver_number')['full_name']
        .to_dict()
    )
else:
    drivers_map = (
        drivers_df[drivers_df['driver_number'].isin(valid_driver_numbers)][['driver_number', 'full_name']]
        .drop_duplicates()
        .set_index('driver_number')['full_name']
        .to_dict()
    )

# Map driver_number to team name
driver_to_team = (
    drivers_df[
        (drivers_df['driver_number'].isin(valid_driver_numbers)) &
        (drivers_df['meeting_key'] == meeting_key)
    ][['driver_number', 'team_name']]
    .drop_duplicates()
    .set_index('driver_number')['team_name']
    .to_dict()
)

driver_choices = list(drivers_map.keys())

driver_1 = st.selectbox(
    "Select Driver 1",
    driver_choices,
    index=driver_choices.index(44) if 44 in driver_choices else 0,
    format_func=lambda x: drivers_map[x]
)
driver_2 = st.selectbox(
    "Select Driver 2",
    driver_choices,
    index=driver_choices.index(1) if 1 in driver_choices else 0,
    format_func=lambda x: drivers_map[x]
)

# -------------------------------
# 5. Filter + Interpolate
# -------------------------------
def get_driver_laps(df, driver_number):
    d = df[df['driver_number'] == driver_number].sort_values('lap_number')
    d = d[['lap_number', 'lap_duration', 'is_pit_out_lap']].dropna()
    max_lap = d['lap_number'].max()
    lap_range = pd.RangeIndex(1, max_lap + 1)
    d_interp = (
        d.set_index('lap_number')[['lap_duration']]
        .reindex(lap_range)
        .interpolate(method='linear')
    )
    pit_laps = d[d['is_pit_out_lap'] == True]['lap_number']
    return d_interp, pit_laps

driver1_data, driver1_pits = get_driver_laps(df, driver_1)
driver2_data, driver2_pits = get_driver_laps(df, driver_2)

# Visual styling for each driver
line_styles = ['solid', 'dash']
marker_shapes = ['circle', 'square']
driver_styles = {
    driver_1: {'dash': line_styles[0], 'marker': marker_shapes[0]},
    driver_2: {'dash': line_styles[1], 'marker': marker_shapes[1]}
}

# Determine line colors
team1 = driver_to_team.get(driver_1, '')
team2 = driver_to_team.get(driver_2, '')
color1 = team_colors.get(team1, 'white')
color2 = (team_secondary_colors.get(team2, 'lightgray') if team1 == team2 else team_colors.get(team2, 'white'))

# -------------------------------
# 6. Plotting
# -------------------------------
fig = go.Figure()

# Main Lines
fig.add_trace(go.Scatter(
    x=driver1_data.index,
    y=driver1_data['lap_duration'],
    mode='lines+markers',
    name=f"{drivers_map[driver_1]} ({team1})",
    line=dict(color=color1,
              dash=driver_styles[driver_1]['dash']),
    marker=dict(size=5, symbol=driver_styles[driver_1]['marker'])
))
fig.add_trace(go.Scatter(
    x=driver2_data.index,
    y=driver2_data['lap_duration'],
    mode='lines+markers',
    name=f"{drivers_map[driver_2]} ({team2})",
    line=dict(color=color2,
              dash=driver_styles[driver_2]['dash']),
    marker=dict(size=5, symbol=driver_styles[driver_2]['marker'])
))

# Pit Stops
fig.add_trace(go.Scatter(
    x=driver1_pits,
    y=driver1_data.loc[driver1_pits]['lap_duration'],
    mode='markers',
    name=f"{drivers_map[driver_1]} ({team1}) Pit Stops",
    marker=dict(symbol='triangle-down', size=10,
                color=color1,
                line=dict(width=2, color='white')))
)
fig.add_trace(go.Scatter(
    x=driver2_pits,
    y=driver2_data.loc[driver2_pits]['lap_duration'],
    mode='markers',
    name=f"{drivers_map[driver_2]} ({team2}) Pit Stops",
    marker=dict(symbol='triangle-down', size=10,
                color=color2,
                line=dict(width=2, color='white')))
)

# Layout
fig.update_layout(
    title=f"Lap Times Comparison: {drivers_map[driver_1]} vs {drivers_map[driver_2]}",
    xaxis_title="Lap Number",
    yaxis_title="Lap Duration (seconds)",
    template="plotly_dark",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)