import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.integrate import cumulative_simpson, cumulative_trapezoid

# === Step 1: Load and clean the CSV ===
file_path = 'position_3.csv'  # Change to your path
df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')

# Extract acceleration columns and drop NaNs
acc_df = df[['acc_x', 'acc_y', 'acc_z']].dropna().astype(float)

# === Step 2: Apply low-pass filter ===
def low_pass_filter(data, cutoff=2.0, fs=48.946, order=2):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='lowpass', analog=False)
    return filtfilt(b, a, data)

filtered_acc = acc_df.copy()
for axis in ['acc_x', 'acc_y', 'acc_z']:
    filtered_acc[axis] = low_pass_filter(acc_df[axis].values)

# === Step 3: Integrate acceleration to get position ===
def integrate_acceleration(acc_data, dt):
    velocity = cumulative_trapezoid(acc_data, dx=dt, initial=0)
    position = cumulative_trapezoid(velocity, dx=dt, initial=0)
    return position

fs = 48.946  # Sampling rate in Hz
dt = 1.0 / fs

position_raw = pd.DataFrame()
position_filtered = pd.DataFrame()

for axis in ['acc_x', 'acc_y', 'acc_z']:
    position_raw[axis] = integrate_acceleration(acc_df[axis].values, dt)
    position_filtered[axis] = integrate_acceleration(filtered_acc[axis].values, dt)

# === Step 4: Plot acceleration comparison ===
plt.figure(figsize=(15, 8))
for i, axis in enumerate(['acc_x', 'acc_y', 'acc_z']):
    plt.subplot(3, 1, i + 1)
    plt.plot(acc_df[axis].values, label=f'Raw {axis}', alpha=0.5)
    plt.plot(filtered_acc[axis].values, label=f'Filtered {axis}', linewidth=2)
    plt.legend()
    plt.title(f'{axis.upper()} Acceleration')
    plt.xlabel('Sample')
    plt.ylabel('Acceleration (m/s2)')
plt.tight_layout()
plt.show()

# === Step 5: Plot position comparison ===
plt.figure(figsize=(15, 8))
for i, axis in enumerate(['acc_x', 'acc_y', 'acc_z']):
    plt.subplot(3, 1, i + 1)
    plt.plot(position_raw[axis], label=f'Raw {axis}', alpha=0.5)
    plt.plot(position_filtered[axis], label=f'Filtered {axis}', linewidth=2)
    plt.legend()
    plt.title(f'{axis.upper()} Position (Integrated)')
    plt.xlabel('Sample')
    plt.ylabel('Position (m)')
plt.tight_layout()
plt.show()
