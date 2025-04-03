import time
import csv
from collections import deque
from tactigon_gear import TSkin, TSkinConfig, Hand, OneFingerGesture
import matplotlib.pyplot as plt

# Configure gesture mapping for numerical representation
gesture_mapping = {
    '': 0,
    'TAP': 1,
    'DOUBLE_TAP': 2,
    'SWIPE_UP': 3,
    'SWIPE_DOWN': 4,
    'SWIPE_LEFT': 5,
    'SWIPE_RIGHT': 6,
    'TAP_AND_HOLD': 7
}

def main():
    TSKIN_MAC = "C0:83:35:34:28:38"
    tskin_cfg = TSkinConfig(TSKIN_MAC, Hand.RIGHT)
    tskin = TSkin(tskin_cfg)
    tskin.start()

    # Initialize plotting
    plt.ion()
    fig, axs = plt.subplots(4, 1, figsize=(10, 8))
    fig.suptitle('TSkin Sensor Data Live Visualization')
    
    # Configure subplots
    ax_angle, ax_acc, ax_gyro, ax_touch = axs
    
    ax_angle.set_ylabel('Angle (deg)')
    line_roll, = ax_angle.plot([], [], label='Roll')
    line_pitch, = ax_angle.plot([], [], label='Pitch')
    line_yaw, = ax_angle.plot([], [], label='Yaw')
    ax_angle.legend()
    
    ax_acc.set_ylabel('Acceleration (m/s²)')
    line_acc_x, = ax_acc.plot([], [], label='X')
    line_acc_y, = ax_acc.plot([], [], label='Y')
    line_acc_z, = ax_acc.plot([], [], label='Z')
    ax_acc.legend()
    
    ax_gyro.set_ylabel('Gyro (rad/s)')
    line_gyro_x, = ax_gyro.plot([], [], label='X')
    line_gyro_y, = ax_gyro.plot([], [], label='Y')
    line_gyro_z, = ax_gyro.plot([], [], label='Z')
    ax_gyro.legend()
    
    ax_touch.set_ylabel('Gesture')
    line_touch, = ax_touch.plot([], [], 'ro-', markersize=5)
    ax_touch.set_ylim(-0.5, 7.5)
    ax_touch.set_yticks(list(gesture_mapping.values()))
    ax_touch.set_yticklabels(list(gesture_mapping.keys()))
    
    plt.tight_layout()

    # Data buffers for plotting
    max_length = 100
    buffers = {
        'roll': deque(maxlen=max_length),
        'pitch': deque(maxlen=max_length),
        'yaw': deque(maxlen=max_length),
        'acc_x': deque(maxlen=max_length),
        'acc_y': deque(maxlen=max_length),
        'acc_z': deque(maxlen=max_length),
        'gyro_x': deque(maxlen=max_length),
        'gyro_y': deque(maxlen=max_length),
        'gyro_z': deque(maxlen=max_length),
        'touch': deque(maxlen=max_length)
    }

    i = 0
    csvfile = None
    writer = None
    file_initialized = False

    while True:
        if not tskin.connected:
            print("Connecting...")
            time.sleep(0.5)
            continue

        if not file_initialized:
            filename = f"tskin_log_{time.strftime('%Y%m%d_%H%M%S')}.csv"
            csvfile = open(filename, 'w', newline='')
            writer = csv.writer(csvfile)
            writer.writerow(['timestamp', 'roll', 'pitch', 'yaw', 'touch_gesture',
                             'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z'])
            file_initialized = True

        a = tskin.angle
        t = tskin.touch
        acc = tskin.acceleration
        gyro = tskin.gyro

        # Logging data (keep original empty strings for missing values)
        timestamp = time.time()
        roll_log = a.roll if a else ''
        pitch_log = a.pitch if a else ''
        yaw_log = a.yaw if a else ''
        touch_gesture_log = t.one_finger.name if t and t.one_finger else ''
        acc_x_log = acc.x if acc else ''
        acc_y_log = acc.y if acc else ''
        acc_z_log = acc.z if acc else ''
        gyro_x_log = gyro.x if gyro else ''
        gyro_y_log = gyro.y if gyro else ''
        gyro_z_log = gyro.z if gyro else ''

        # Convert to plot values (0 for missing data)
        roll_plot = a.roll if a else 0.0
        pitch_plot = a.pitch if a else 0.0
        yaw_plot = a.yaw if a else 0.0
        touch_plot = gesture_mapping.get(touch_gesture_log, 0)
        acc_x_plot = acc.x if acc else 0.0
        acc_y_plot = acc.y if acc else 0.0
        acc_z_plot = acc.z if acc else 0.0
        gyro_x_plot = gyro.x if gyro else 0.0
        gyro_y_plot = gyro.y if gyro else 0.0
        gyro_z_plot = gyro.z if gyro else 0.0

        # Update plot buffers
        buffers['roll'].append(roll_plot)
        buffers['pitch'].append(pitch_plot)
        buffers['yaw'].append(yaw_plot)
        buffers['acc_x'].append(acc_x_plot)
        buffers['acc_y'].append(acc_y_plot)
        buffers['acc_z'].append(acc_z_plot)
        buffers['gyro_x'].append(gyro_x_plot)
        buffers['gyro_y'].append(gyro_y_plot)
        buffers['gyro_z'].append(gyro_z_plot)
        buffers['touch'].append(touch_plot)

        # Update plots
        x_data = range(len(buffers['roll']))
        
        line_roll.set_data(x_data, buffers['roll'])
        line_pitch.set_data(x_data, buffers['pitch'])
        line_yaw.set_data(x_data, buffers['yaw'])
        ax_angle.relim()
        ax_angle.autoscale_view()
        
        line_acc_x.set_data(x_data, buffers['acc_x'])
        line_acc_y.set_data(x_data, buffers['acc_y'])
        line_acc_z.set_data(x_data, buffers['acc_z'])
        ax_acc.relim()
        ax_acc.autoscale_view()
        
        line_gyro_x.set_data(x_data, buffers['gyro_x'])
        line_gyro_y.set_data(x_data, buffers['gyro_y'])
        line_gyro_z.set_data(x_data, buffers['gyro_z'])
        ax_gyro.relim()
        ax_gyro.autoscale_view()
        
        line_touch.set_data(x_data, buffers['touch'])
        ax_touch.relim()
        ax_touch.autoscale_view()

        # Redraw the plot
        fig.canvas.draw()
        fig.canvas.flush_events()

        # Write to CSV
        writer.writerow([timestamp, roll_log, pitch_log, yaw_log, touch_gesture_log,
                         acc_x_log, acc_y_log, acc_z_log, gyro_x_log, gyro_y_log, gyro_z_log])

        # Check for exit condition
        if t and t.one_finger == OneFingerGesture.TAP_AND_HOLD:
            i += 1
        else:
            i = 0

        if i > 5:
            break

        plt.pause(0.01)  # Maintain 50Hz update rate

    # Cleanup
    if csvfile:
        csvfile.close()
    tskin.terminate()
    plt.close(fig)

if __name__ == "__main__":
    main()