import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid

# Load the CSV file
df = pd.read_csv('modified_data.csv', usecols=['timestamp', 'acc_x'], on_bad_lines='skip')

# Clean the data (remove rows with missing values)
df = df.dropna(subset=['timestamp', 'acc_x'])

# Convert timestamps to relative time in seconds
timestamps = df['timestamp'].values
t = timestamps - timestamps[0]  # Relative time starting from 0

# Get acceleration data (convert to m/s² if needed)
acc_x = df['acc_x'].values

# Time step (calculate average delta between timestamps)
dt = np.mean(np.diff(t))

# Integrate acceleration to get velocity
velocity = cumulative_trapezoid(acc_x, x=t, initial=0)

# Integrate velocity to get position
position = cumulative_trapezoid(velocity, x=t, initial=0)

# Plot the results
plt.figure(figsize=(12, 6))

plt.subplot(3, 1, 1)
plt.plot(t, acc_x)
plt.ylabel('Acceleration (m/s²)')
plt.title('X-Axis Acceleration')

plt.subplot(3, 1, 2)
plt.plot(t, velocity)
plt.ylabel('Velocity (m/s)')

plt.subplot(3, 1, 3)
plt.plot(t, position)
plt.ylabel('Position (m)')
plt.xlabel('Time (s)')

plt.tight_layout()
plt.show()

# Print summary
print(f"Final position: {position[-1]:.2f} m")
print(f"Maximum velocity: {np.max(np.abs(velocity)):.2f} m/s")