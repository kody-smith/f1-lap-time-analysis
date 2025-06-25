import plotly.graph_objects as go
from plotly.offline import plot
import pandas as pd
import requests


### Getting Data ###
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# Request vairables
session_key = 9161  # Session key for the 2023 Bahrain GP
# Get lap data for 2023 Bahrain GP (Round 1)
url = f"https://api.openf1.org/v1/laps?session_key={session_key}"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
else:
    print("Failed to fetch data:", response.status_code)

# Convert JSON data to DataFrame
df = pd.DataFrame(data)
# print(df.lap_duration.describe())
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#




# Data Cleaning and Preparation
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# Filter both drivers from the full race DataFrame
selected_drivers = df[df['driver_number'].isin([1, 44])]

# Split into two DataFrames
hamilton_laps = selected_drivers[selected_drivers['driver_number'] == 44].sort_values('lap_number')
verstappen_laps = selected_drivers[selected_drivers['driver_number'] == 1].sort_values('lap_number')


# # Check
# print("Hamilton laps:", hamilton_laps.shape[0])
# print("Verstappen laps:", verstappen_laps.shape[0])

# Force correct types
for df_ in [hamilton_laps, verstappen_laps]:
    df_['lap_number'] = df_['lap_number'].astype(int)
    df_['lap_duration'] = df_['lap_duration'].astype(float)

# Make sure laps are sorted
hamilton_sorted = hamilton_laps.sort_values('lap_number')
verstappen_sorted = verstappen_laps.sort_values('lap_number')



# Interpolate lap durations for both drivers
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
max_lap = max(hamilton_sorted['lap_number'].max(), verstappen_sorted['lap_number'].max())
lap_range = pd.RangeIndex(1, max_lap + 1)

# For Hamilton
hamilton_interp = (
    hamilton_sorted
    .set_index('lap_number')[['lap_duration']]
    .reindex(lap_range)
    .interpolate(method='linear')
)
# For Verstappen
verstappen_interp = (
    verstappen_sorted
    .set_index('lap_number')[['lap_duration']]
    .reindex(lap_range)
    .interpolate(method='linear')
)


# Create a figure object
fig = go.Figure()


# Add traces for Hamilton and Verstappen
fig.add_trace(go.Scatter(
    x=hamilton_interp.index,
    y=hamilton_interp['lap_duration'],
    mode='lines+markers',
    name='Hamilton',
    line=dict(color='#00A19B'),
    marker=dict(size=5),
    hovertemplate='Lap %{x}<br>Duration: %{y:.2f}s<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=verstappen_interp.index,
    y=verstappen_interp['lap_duration'],
    mode='lines+markers',
    name='Verstappen',
    line=dict(color='red'),
    marker=dict(size=5),
    hovertemplate='Lap %{x}<br>Duration: %{y:.2f}s<extra></extra>'
))

#Pit stop markers
# Identify pit-out laps
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
hamilton_pit_lap_nums = hamilton_sorted[hamilton_sorted['is_pit_out_lap'] == True]['lap_number']
verstappen_pit_lap_nums = verstappen_sorted[verstappen_sorted['is_pit_out_lap'] == True]['lap_number']

hamilton_pit_laps = hamilton_interp.loc[hamilton_pit_lap_nums]
verstappen_pit_laps = verstappen_interp.loc[verstappen_pit_lap_nums]
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
fig.add_trace(go.Scatter(
    x=hamilton_pit_laps.index,
    y=hamilton_pit_laps['lap_duration'],
    mode='markers',
    name='Hamilton Pit Stops',
    marker=dict(size=12, color='#C8CCCE', symbol='circle'),
    hovertemplate='Hamilton Pit <br>Lap%{x}'
))

fig.add_trace(go.Scatter(
    x=verstappen_pit_laps.index,
    y=verstappen_pit_laps['lap_duration'],
    mode='markers',
    name='Verstappen Pit Stops',
    marker=dict(size=12, color='#FDD900', symbol='square'),
    hovertemplate='Verstappen Pit <br>Lap%{x}'
))
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


# Find fastest lap for each driver
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
hamilton_fastest_lap = hamilton_interp['lap_duration'].idxmin()
verstappen_fastest_lap = verstappen_interp['lap_duration'].idxmin()

# Get lap duration for fastest laps
hamilton_fastest_time = hamilton_interp.loc[hamilton_fastest_lap, 'lap_duration']
verstappen_fastest_time = verstappen_interp.loc[verstappen_fastest_lap, 'lap_duration']

#Add fastest lap markers
fig.add_trace(go.Scatter(
    x=[hamilton_fastest_lap],
    y=[hamilton_fastest_time],
    mode='markers+text',
    name='Hamilton Fastest Lap',
    marker=dict(size=14, color='#C8CCCE', symbol='star'),
    text=[f'{hamilton_fastest_time:.2f}s'],
    textposition='top center',
    hovertemplate='Hamilton Fastest Lap<br>Lap %{x}<br>Time: %{y:.2f}s<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=[verstappen_fastest_lap],
    y=[verstappen_fastest_time],
    mode='markers+text',
    name='Verstappen Fastest Lap',
    marker=dict(size=14, color='#FDD900', symbol='star'),
    text=[f'{verstappen_fastest_time:.2f}s'],
    textposition='top center',
    hovertemplate='Verstappen Fastest Lap<br>Lap %{x}<br>Time: %{y:.2f}s<extra></extra>'
))
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


# Update layout
fig.update_layout(
    title='Lap Times Comparison: Hamilton vs Verstappen (2023 Bahrain GP)',
    xaxis_title='Lap Number',
    yaxis_title='Lap Duration (seconds)',
    legend=dict(x=0.01, y=0.99),
    hovermode='x unified',
    template='plotly_dark',  # Use dark theme
    font=dict(color='white'),  # Font color for text
)

plot(fig, filename='lap_times_comparison.html', auto_open=True)

