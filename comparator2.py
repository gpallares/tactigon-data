import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def compare_aruco_imu(aruco_csv, imu_csv):
    # Load and process both datasets
    aruco_df = pd.read_csv(aruco_csv)
    imu_df = pd.read_csv(imu_csv, parse_dates=False)

    # Convert timestamps to absolute times
    # ArUco data uses system_time (Unix timestamp)
    aruco_df['global_time'] = pd.to_datetime(aruco_df['system_time'], unit='s')
    
    # IMU data - convert timestamp to datetime (assuming it's UNIX timestamp)
    imu_df['global_time'] = pd.to_datetime(imu_df['timestamp'], unit='s')
    
    # Find common start time and create relative timeline
    start_time = min(aruco_df['global_time'].min(), imu_df['global_time'].min())
    
    # Create relative time columns in seconds
    for df in [aruco_df, imu_df]:
        df['elapsed'] = (df['global_time'] - start_time).dt.total_seconds()

    # Create figure with subplots
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
    
    # Combine datasets with corrected column mapping
    combined_orientation = pd.concat([
        aruco_df[['elapsed', 'roll_deg', 'pitch_deg', 'yaw_deg']]
            .rename(columns={
                'roll_deg': 'yaw',
                'pitch_deg': 'pitch',
                'yaw_deg': 'roll'
            })
            .assign(source='ArUco'),
        imu_df[['elapsed', 'roll', 'pitch', 'yaw']]
            .assign(source='IMU')
    ])

    # Plot orientation comparison
    for axis, ax in axes_orientation.items():
        for source, group in combined_orientation.groupby('source'):
            ax.plot(group['elapsed'], group[axis], label=source, alpha=0.7)
            ax.set_title(f'{axis.capitalize()} Comparison')
            ax.set_ylabel('Degrees')
            ax.grid(True)
        ax.legend()
    
    # Plot ArUco position data (corrected to millimeters)
    ax_pos.plot(aruco_df['elapsed'], aruco_df['pos_x_cm']*10, label='X')
    ax_pos.plot(aruco_df['elapsed'], aruco_df['pos_y_cm']*10, label='Y')
    ax_pos.plot(aruco_df['elapsed'], aruco_df['pos_z_cm']*10, label='Z')
    ax_pos.set_title('ArUco Position Tracking')
    ax_pos.set_ylabel('Millimeters')
    ax_pos.legend()
    ax_pos.grid(True)
    
    # Plot detection confidence
    ax_conf.scatter(aruco_df['elapsed'], aruco_df['detection_confidence'], 
                   c='red', s=10, alpha=0.5)
    ax_conf.set_title('ArUco Detection Confidence')
    ax_conf.set_ylabel('Confidence Score')
    ax_conf.grid(True)
    
    # Plot IMU sensor data using aligned timeline
    imu_df.plot(x='elapsed', y=['acc_x', 'acc_y', 'acc_z'], ax=ax_accel)
    ax_accel.set_title('IMU Acceleration')
    ax_accel.set_ylabel('m/s²')
    
    imu_df.plot(x='elapsed', y=['gyro_x', 'gyro_y', 'gyro_z'], ax=ax_gyro)
    ax_gyro.set_title('IMU Gyroscope')
    ax_gyro.set_ylabel('rad/s')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    aruco_file = "aruco_log_20250319_113300.csv"
    imu_file = "tskin_log_20250319_113249.csv" 
    # aruco_file = "/home/banjov2/Tactigon-SDK/aruco_log_20250319_113300.csv"
    # imu_file = "/home/banjov2/Tactigon-SDK/tskin_log_20250319_113249.csv"
    compare_aruco_imu(aruco_file, imu_file)