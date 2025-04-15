import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.integrate import cumulative_trapezoid


FS = 47.0               # Sampling frequency (Hz)
CUTOFF = 2.0            # Low-pass cutoff (Hz)

def butter_lowpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(data, cutoff, fs):
    b, a = butter_lowpass(cutoff, fs)
    return filtfilt(b, a, data)

def remove_initial_bias(data, num_samples=100):
    return data - np.mean(data[:num_samples])

df = pd.read_csv('tskin_log_20250415_174409.csv', on_bad_lines='skip', engine='python')
acc_df = df[['acc_x', 'acc_y', 'acc_z']].dropna().astype(float)

# Preprocessing: Remove initial bias and filter
filtered_acc = acc_df.copy()
for axis in acc_df.columns:
    # Remove initial offset (assuming device starts at rest)
    filtered_acc[axis] = remove_initial_bias(acc_df[axis].values)
    
    # Apply low-pass filter
    filtered_acc[axis] = lowpass_filter(filtered_acc[axis], CUTOFF, FS)

# Integration parameters
dt = 1/FS
times = np.arange(len(acc_df)) * dt

# Integrate to get velocity and position
results = {}
for acc_type, data in [('Raw', acc_df), ('Filtered', filtered_acc)]:
    velocity = pd.DataFrame()
    position = pd.DataFrame()
    
    for axis in data.columns:
        # Integrate acceleration to velocity
        vel = cumulative_trapezoid(data[axis], dx=dt, initial=0)
        
        # Remove velocity drift (high-pass filter)
        vel = lowpass_filter(vel, CUTOFF, FS)  
        
        # Integrate velocity to position
        pos = cumulative_trapezoid(vel, dx=dt, initial=0)
        
        velocity[axis] = vel
        position[axis] = pos
    
    results[acc_type] = {'velocity': velocity, 'position': position}

# === Plotting ===
fig, axs = plt.subplots(3, 1, figsize=(12, 8))
for i, axis in enumerate(['acc_x', 'acc_y', 'acc_z']):
    axs[i].plot(times, results['Raw']['position'][axis], alpha=0.6, label='Raw')
    axs[i].plot(times, results['Filtered']['position'][axis], label='Filtered')
    axs[i].set_title(f'{axis.upper()} Position')
    axs[i].set_ylabel('Position (m)')
    axs[i].legend()
axs[-1].set_xlabel('Time (s)')
plt.tight_layout()
plt.show()