import pandas as pd
import matplotlib.pyplot as plt


def visualize_tskin_data(csv_path):
    # Load data with proper parsing
    df = pd.read_csv(csv_path, parse_dates=False)
    
    # Convert timestamp to seconds since first measurement
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df['time_seconds'] = df['timestamp'] - df['timestamp'].iloc[0]
    
    # Create subplots
    fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # Plot Orientation Data
    axs[0].plot(df['time_seconds'], df['roll'], label='Roll')
    axs[0].plot(df['time_seconds'], df['pitch'], label='Pitch')
    axs[0].plot(df['time_seconds'], df['yaw'], label='Yaw')
    axs[0].set_ylabel('Degrees')
    axs[0].set_title('Orientation (Euler Angles)')
    axs[0].grid(True)
    axs[0].legend()
    
    # Plot Acceleration Data
    axs[1].plot(df['time_seconds'], df['acc_x'], label='X')
    axs[1].plot(df['time_seconds'], df['acc_y'], label='Y')
    axs[1].plot(df['time_seconds'], df['acc_z'], label='Z')
    axs[1].set_ylabel('Acceleration (m/s²)')
    axs[1].set_title('3-Axis Acceleration')
    axs[1].grid(True)
    axs[1].legend()
    
    # Plot Gyroscope Data
    axs[2].plot(df['time_seconds'], df['gyro_x'], label='X')
    axs[2].plot(df['time_seconds'], df['gyro_y'], label='Y')
    axs[2].plot(df['time_seconds'], df['gyro_z'], label='Z')
    axs[2].set_xlabel('Time (seconds)')
    axs[2].set_ylabel('Angular Velocity (rad/s)')
    axs[2].set_title('3-Axis Gyroscope')
    axs[2].grid(True)
    axs[2].legend()
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    csv_file = "modified_data.csv"  # Replace with your filename
    visualize_tskin_data(csv_file)