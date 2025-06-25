import requests
import pandas as pd
import json

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
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

# Data Analysis
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
import matplotlib.pyplot as plt

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
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


# Find fastest lap for each driver
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
hamilton_fastest_lap = hamilton_interp['lap_duration'].idxmin()
verstappen_fastest_lap = verstappen_interp['lap_duration'].idxmin()

# Get lap duration for fastest laps
hamilton_fastest_time = hamilton_interp.loc[hamilton_fastest_lap, 'lap_duration']
verstappen_fastest_time = verstappen_interp.loc[verstappen_fastest_lap, 'lap_duration']
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#



# Identify pit-out laps
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
hamilton_pit_lap_nums = hamilton_sorted[hamilton_sorted['is_pit_out_lap'] == True]['lap_number']
verstappen_pit_lap_nums = verstappen_sorted[verstappen_sorted['is_pit_out_lap'] == True]['lap_number']

hamilton_pit_laps = hamilton_interp.loc[hamilton_pit_lap_nums]
verstappen_pit_laps = verstappen_interp.loc[verstappen_pit_lap_nums]
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#




#Exclude pit laps from the main trend lines
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
hamilton_clean = hamilton_sorted[~hamilton_sorted['is_pit_out_lap']]
verstappen_clean = verstappen_sorted[~verstappen_sorted['is_pit_out_lap']]

# Ensure no NaN values in lap_duration before plotting
hamilton_clean = hamilton_clean.dropna(subset=['lap_duration'])
verstappen_clean = verstappen_clean.dropna(subset=['lap_duration'])
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#




#Lap consistency analysis
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


#find the standard deviation of lap times for each driver
hamilton_std = hamilton_clean['lap_duration'].std()
verstappen_std = verstappen_clean['lap_duration'].std()

print(f"Hamilton's standard deviation of lap times: {hamilton_std:.2f} seconds")
print(f"Verstappen's standard deviation of lap times: {verstappen_std:.2f} seconds")



#Rolling average of lap times
hamilton_clean_sorted = hamilton_clean.sort_values('lap_number')
verstappen_clean_sorted = verstappen_clean.sort_values('lap_number')

hamilton_clean_sorted['rolling_avg'] = hamilton_clean_sorted['lap_duration'].rolling(window=3).mean()
verstappen_clean_sorted['rolling_avg'] = verstappen_clean_sorted['lap_duration'].rolling(window=3).mean()



# #plotting the rolling averages
# plt.figure(figsize=(12, 6))

# plt.plot(hamilton_clean_sorted['lap_number'], hamilton_clean_sorted['rolling_avg'],
#          label='Hamilton Rolling Avg', color='blue', linestyle='-')

# plt.plot(verstappen_clean_sorted['lap_number'], verstappen_clean_sorted['rolling_avg'],
#          label='Verstappen Rolling Avg', color='red', linestyle='--')

# plt.xlabel('Lap Number')
# plt.ylabel('Rolling Avg Lap Time (sec)')
# plt.title('Rolling Average Lap Time – Consistency Trends')
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#





# Plotting the interpolated lap times for both drivers

plt.figure(figsize=(12, 6))

# Trend lines
plt.plot(hamilton_interp.index, hamilton_interp['lap_duration'], color='blue', label='Hamilton')
plt.plot(verstappen_interp.index, verstappen_interp['lap_duration'], color='red', linestyle='--', label='Verstappen')

# Fastest lap markers
plt.scatter(    
    [hamilton_fastest_lap],
    [hamilton_fastest_time],
    color='blue',
    edgecolor='black',
    label='Hamilton Fastest Lap',
    s=150,
    marker='*',
    zorder=6
)

plt.scatter(   
    [verstappen_fastest_lap],
    [verstappen_fastest_time],
    color='red',
    edgecolor='black',
    label='Verstappen Fastest Lap',
    s=150,
    marker='*',
    zorder=6
)

# Annotate fastest laps
plt.annotate(f"{hamilton_fastest_time:.2f}s",
             (hamilton_fastest_lap, hamilton_fastest_time),
             textcoords="offset points",
             xytext=(0,10),
             ha='left',
             fontsize=9,
             color='blue')

plt.annotate(f"{verstappen_fastest_time:.2f}s",
             (verstappen_fastest_lap, verstappen_fastest_time),
             textcoords="offset points",
             xytext=(0,10),
             ha='left',
             fontsize=9,
             color='red')

# Pit lap markers
plt.scatter(
    hamilton_pit_laps.index,
    hamilton_pit_laps['lap_duration'],
    color='cyan',
    edgecolor='black',
    label='Hamilton Pit Out',
    s=100,
    marker='o',
    zorder=5
)

plt.scatter(
    verstappen_pit_laps.index,
    verstappen_pit_laps['lap_duration'],
    color='orange',
    edgecolor='black',
    label='Verstappen Pit Out',
    s=100,
    marker='s',
    zorder=5
)

# Labels & formatting
plt.xlabel('Lap Number')
plt.ylabel('Lap Time (seconds)')
plt.title('Lap Time Trend with Pit Stops – Hamilton vs. Verstappen')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()