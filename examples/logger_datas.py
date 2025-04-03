import time
import csv
from tactigon_gear import TSkin, TSkinConfig, Hand, OneFingerGesture

def main():
    TSKIN_MAC = "C0:83:35:34:28:38"
    tskin_cfg = TSkinConfig(TSKIN_MAC, Hand.RIGHT)
    tskin = TSkin(tskin_cfg)
    tskin.start()

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

        print(a, t, acc, gyro)

        timestamp = time.time()

        # Extract data, handling None cases
        roll = a.roll if a else ''
        pitch = a.pitch if a else ''
        yaw = a.yaw if a else ''

        touch_gesture = t.one_finger.name if t and t.one_finger else ''

        acc_x = acc.x if acc else ''
        acc_y = acc.y if acc else ''
        acc_z = acc.z if acc else ''

        gyro_x = gyro.x if gyro else ''
        gyro_y = gyro.y if gyro else ''
        gyro_z = gyro.z if gyro else ''

        writer.writerow([timestamp, roll, pitch, yaw, touch_gesture,
                         acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z])

        if t and t.one_finger == OneFingerGesture.TAP_AND_HOLD:
            i += 1
        else:
            i = 0

        if i > 5:
            break

        time.sleep(0.02) # 50Hz

    if csvfile:
        csvfile.close()
    tskin.terminate()

if __name__ == "__main__":
    main()