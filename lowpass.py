import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
import os # Added to check if file exists

# --- Configuration ---
# <<< CHANGE THIS TO THE ACTUAL PATH OF YOUR LOG FILE >>>
log_file_path = 'tskin_log_20250403_175238.csv'

# Filter parameters (ADJUST THESE AS NEEDED)
filter_order = 3      # Order of the Butterworth filter
cutoff_freq_hz = 2.0  # Cutoff frequency in Hz (filters out frequencies above this)
# --- End Configuration ---

# Columns to apply the filter to
columns_to_filter = [
    'roll', 'pitch', 'yaw',
    'acc_x', 'acc_y', 'acc_z',
    'gyro_x', 'gyro_y', 'gyro_z'
]

# 1. Load Data from File
if not os.path.exists(log_file_path):
    print(f"Error: Log file not found at '{log_file_path}'")
    exit()

try:
    # Read the CSV file, explicitly naming columns as the first line is the header
    df = pd.read_csv(log_file_path, header=0) # Use header=0 since the first line IS the header
    print(f"Successfully loaded data from '{log_file_path}'.")
    print(f"Initial data shape: {df.shape}")
    # print("Initial data head:\n", df.head()) # Optional: Check first few rows
except Exception as e:
    print(f"Error reading log file: {e}")
    exit()

# 2. Clean Data
# Convert sensor columns to numeric, coercing errors (like empty strings) to NaN
for col in columns_to_filter:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    else:
        print(f"Warning: Column '{col}' not found in the file.")
        columns_to_filter.remove(col) # Remove if not present

# Drop rows where ALL specified sensor columns are NaN (like the first few lines)
df.dropna(subset=columns_to_filter, how='all', inplace=True)
print(f"Data shape after dropping full NaN rows: {df.shape}")

# Handle any remaining isolated NaNs using forward fill then backward fill
# This is simple; interpolation might be better for some signals.
if df.isnull().any().any():
    print("Filling remaining NaN values...")
    df.ffill(inplace=True)
    df.bfill(inplace=True) # Handle NaNs at the very beginning

if df.empty:
    print("Error: No valid data remaining after cleaning.")
    exit()

print("Data cleaning complete.")
# print("Cleaned data head:\n", df.head()) # Optional: Check cleaned data

# 3. Estimate Sampling Rate
# Calculate time differences between consecutive samples
# time_diffs = df['timestamp'].diff().dropna() # dropna() removes the first NaN difference

# if time_diffs.empty or (time_diffs <= 0).any():
#     print("Error: Could not determine a valid sampling rate from timestamps.")
#     print("Check timestamps for monotonicity and sufficient data points.")
#     # Optionally, you could hardcode an expected sampling rate here if known
#     # fs = 10.0 # Example: If you know it's roughly 10 Hz
#     exit()


# # Use the median time difference for robustness against outliers
# median_sample_period = time_diffs.median()
# fs = 1.0 / median_sample_period # Sampling frequency in Hz

fs = 50 # Hardcoded for testing purposes
# print(f"Estimated Sampling Period: {median_sample_period:.6f} seconds")
# print(f"Estimated Sampling Frequency (fs): {fs:.2f} Hz")

# Check if cutoff frequency is valid for the sampling rate (Nyquist theorem)
if cutoff_freq_hz >= fs / 2:
    print(f"Warning: Cutoff frequency ({cutoff_freq_hz} Hz) is too high for the estimated sampling rate ({fs:.2f} Hz).")
    print(f"Setting cutoff frequency to slightly below Nyquist frequency: {fs / 2.1:.2f} Hz")
    cutoff_freq_hz = fs / 2.1 # Adjust to be safe

# 4. Design Filter
# Get Butterworth filter coefficients (b, a)
try:
    b, a = butter(filter_order, cutoff_freq_hz, btype='low', analog=False, fs=fs)
    print(f"Designed Butterworth low-pass filter: Order={filter_order}, Cutoff={cutoff_freq_hz} Hz")
except ValueError as e:
     print(f"Error designing filter: {e}")
     print("Check filter order and cutoff frequency relative to sampling rate.")
     exit()

# 5. Apply Filter
print("Applying filter to columns:", columns_to_filter)
for col in columns_to_filter:
    # Ensure the column exists and has data
    if col in df.columns and not df[col].isnull().all():
        # Get the signal data as a NumPy array
        signal_data = df[col].values
        # Apply the filter using filtfilt for zero phase distortion
        filtered_signal = filtfilt(b, a, signal_data)
        # Store the filtered signal in a new column
        df[col + '_filtered'] = filtered_signal
    else:
        print(f"Skipping filtering for column '{col}' (not found or all NaN).")



# 6. Visualize (Example: Plot Accelerometer and Gyroscope data)
print("Plotting results...")
signals_to_plot = {
    'Orientation': ['roll', 'pitch', 'yaw'],
    'Acceleration': ['acc_x', 'acc_y', 'acc_z'],
    'Gyroscope': ['gyro_x', 'gyro_y', 'gyro_z']
}

time_axis = df['timestamp'] # Use timestamp for the x-axis

for group_name, cols in signals_to_plot.items():
    # Check if at least one column in the group exists and was filtered
    valid_cols = [col for col in cols if col in df.columns and col + '_filtered' in df.columns]
    if not valid_cols:
        print(f"Skipping plot for {group_name}: No valid/filtered columns found.")
        continue

    num_cols = len(valid_cols)
    fig, axes = plt.subplots(num_cols, 1, figsize=(12, num_cols * 2.5), sharex=True)
    if num_cols == 1: # Make axes iterable even if only one subplot
       axes = [axes]

    fig.suptitle(f'{group_name} Data: Original vs. Low-Pass Filtered (Cutoff={cutoff_freq_hz} Hz)', fontsize=14)

    for i, col in enumerate(valid_cols):
        ax = axes[i]
        ax.plot(time_axis, df[col], label='Original', alpha=0.7)
        ax.plot(time_axis, df[col + '_filtered'], label='Filtered', linewidth=2)
        ax.set_ylabel(col)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)

    axes[-1].set_xlabel('Timestamp (seconds)')
    plt.tight_layout(rect=[0, 0.03, 1, 0.96]) # Adjust layout to prevent title overlap
    plt.show()

print("\nFiltered data is available in the DataFrame 'df'. Example:")
print(df[['timestamp'] + [col + '_filtered' for col in columns_to_filter if col + '_filtered' in df.columns]].head())