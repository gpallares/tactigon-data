import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def compare_aruco_imu(aruco_csv, imu_csv):
    # Load and process both datasets
    aruco_df = pd.read_csv(aruco_csv)
    imu_df = pd.read_csv(imu_csv, parse_dates=False)

      # Create figure with subplots - FIXED SECTION
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(4, 2)
    
    # Create orientation axes sequentially
    axes_orientation = {}
    axes_orientation['roll'] = fig.add_subplot(gs[0, 0])
    axes_orientation['pitch'] = fig.add_subplot(gs[1, 0], sharex=axes_orientation['roll'])
    axes_orientation['yaw'] = fig.add_subplot(gs[2, 0], sharex=axes_orientation['roll'])

    # Create other axes
    ax_pos = fig.add_subplot(gs[0, 1])
    ax_conf = fig.add_subplot(gs[1, 1])
    ax_accel = fig.add_subplot(gs[2, 1])
    ax_gyro = fig.add_subplot(gs[3, 1])
    
    # Convert timestamps to relative seconds
    for df in [aruco_df, imu_df]: 
        if 'system_time' in df.columns:  # ArUco data
            df['time'] = df['system_time'] - df['system_time'].iloc[0]
            df['source'] = 'ArUco'
        else:  # IMU data
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
            df['time'] = df['timestamp'] - df['timestamp'].iloc[0]
            df['source'] = 'IMU'
    
    # Combine datasets
    combined_orientation = pd.concat([
        aruco_df[['time', 'roll_deg', 'pitch_deg', 'yaw_deg', 'source']]
            .rename(columns={'roll_deg': 'yaw', 'pitch_deg': 'pitch', 'yaw_deg': 'roll'}),
        imu_df[['time', 'roll', 'pitch', 'yaw', 'source']]
    ])
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(4, 2)
    
    # Orientation comparison plots
    axes_orientation = {
        'roll': fig.add_subplot(gs[0, 0]),
        'pitch': fig.add_subplot(gs[1, 0], sharex=axes_orientation['roll']),
        'yaw': fig.add_subplot(gs[2, 0], sharex=axes_orientation['roll'])
    }
    
    # Position and confidence plots
    ax_pos = fig.add_subplot(gs[0, 1])
    ax_conf = fig.add_subplot(gs[1, 1])
    
    # IMU-specific plots
    ax_accel = fig.add_subplot(gs[2, 1])
    ax_gyro = fig.add_subplot(gs[3, 1])
    
    # Plot orientation comparison
    for axis, ax in axes_orientation.items():
        for source, group in combined_orientation.groupby('source'):
            ax.plot(group['time'], group[axis], label=source, alpha=0.7)
            ax.set_title(f'{axis.capitalize()} Comparison')
            ax.set_ylabel('Degrees')
            ax.grid(True)
        ax.legend()
    
    # Plot ArUco position data
    ax_pos.plot(aruco_df['time'], aruco_df['pos_x_cm'], label='X')
    ax_pos.plot(aruco_df['time'], aruco_df['pos_y_cm'], label='Y')
    ax_pos.plot(aruco_df['time'], aruco_df['pos_z_cm'], label='Z')
    ax_pos.set_title('ArUco Position Tracking')
    ax_pos.set_ylabel('milimiters')
    ax_pos.legend()
    ax_pos.grid(True)
    
    # Plot detection confidence
    ax_conf.scatter(aruco_df['time'], aruco_df['detection_confidence'], 
                   c='red', s=10, alpha=0.5)
    ax_conf.set_title('ArUco Detection Confidence')
    ax_conf.set_ylabel('Confidence Score')
    ax_conf.grid(True)
    
    # Plot IMU sensor data
    imu_df.plot(x='time', y=['acc_x', 'acc_y', 'acc_z'], ax=ax_accel)
    ax_accel.set_title('IMU Acceleration')
    ax_accel.set_ylabel('m/s²')
    
    imu_df.plot(x='time', y=['gyro_x', 'gyro_y', 'gyro_z'], ax=ax_gyro)
    ax_gyro.set_title('IMU Gyroscope')
    ax_gyro.set_ylabel('rad/s')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    aruco_file = "/home/banjov2/Tactigon-SDK/aruco_log_20250319_113300.csv"
    imu_file = "/home/banjov2/Tactigon-SDK/tskin_log_20250319_113249.csv"
    
    compare_aruco_imu(aruco_file, imu_file)