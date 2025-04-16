import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- Load and preprocess the data ---
# Replace 'data.csv' with the path to your CSV file.
df = pd.read_csv('modified_data.csv')

# Keep rows with valid acceleration data
df = df.dropna(subset=['acc_x', 'acc_y', 'acc_z'])

# Ensure the timestamp column is numeric
df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')

# Sort the DataFrame by timestamp
df = df.sort_values('timestamp').reset_index(drop=True)

# Compute time differences (dt) between consecutive measurements
df['dt'] = df['timestamp'].diff().fillna(0)

# --- Initialize arrays for velocity and position ---
n = len(df)
v_x = np.zeros(n)
v_y = np.zeros(n)
v_z = np.zeros(n)

x = np.zeros(n)
y = np.zeros(n)
z = np.zeros(n)

# --- Perform integration using a simple Euler method ---
# Here we assume the accelerations are already in the global coordinate system.
for i in range(1, n):
    dt = df.loc[i, 'dt']
    # Update velocity: v = v_previous + acceleration * dt
    v_x[i] = v_x[i-1] + df.loc[i-1, 'acc_x'] * dt
    v_y[i] = v_y[i-1] + df.loc[i-1, 'acc_y'] * dt
    v_z[i] = v_z[i-1] + df.loc[i-1, 'acc_z'] * dt

    # Update position: pos = pos_previous + velocity * dt [assuming constant velocity]
    x[i] = x[i-1] + v_x[i-1] * dt
    y[i] = y[i-1] + v_y[i-1] * dt
    z[i] = z[i-1] + v_z[i-1] * dt

# Add the computed positions back into the DataFrame
df['x'] = x
df['y'] = y
df['z'] = z

# --- Plot position over time ---
plt.figure(figsize=(10, 8))

plt.subplot(3, 1, 1)
plt.plot(df['timestamp'], df['x'], label='X Position', color='r')
plt.ylabel('X Position')
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(df['timestamp'], df['y'], label='Y Position', color='g')
plt.ylabel('Y Position')
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(df['timestamp'], df['z'], label='Z Position', color='b')
plt.xlabel('Time (s)')
plt.ylabel('Z Position')
plt.legend()

plt.tight_layout()
plt.show()

# --- Plot the 3D trajectory ---
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
ax.plot(df['x'], df['y'], df['z'], label='Trajectory', color='m')
ax.set_xlabel('X Position')
ax.set_ylabel('Y Position')
ax.set_zlabel('Z Position')
ax.legend()
plt.show()
