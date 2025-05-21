import asyncio
from bleak import BleakScanner
from termcolor import cprint
import time
import datetime
from os import path, getcwd
import tactigon_gear
from tactigon_gear import TSkin, TSkinConfig, Hand, GestureConfig, OneFingerGesture
from tactigon_speech import TSkin_Speech, TSkinConfig as TSpeechTSkinConfig, Hand as TSpeechHand, VoiceConfig, OneFingerGesture as TSpeechOneFingerGesture, TSpeechObject, TSpeech, HotWord # Aliased to avoid name clash if necessary, though TSkinConfig and Hand are the same.
import socket

TARGET_DEVICE_NAME = "TSKIN50"
TSKIN: TSkin = None 


DOCKER_SENDER_HOST = 'host.docker.internal'  # For Docker Desktop. For Linux without Docker Desktop, use your host's actual IP address.
DOCKER_SENDER_PORT = 8888
DOCKER_SOCKET: socket.socket = None

# --- Docker Sender Functions ---
def connect_docker_sender():
    global DOCKER_SOCKET
    if DOCKER_SOCKET is not None:
        cprint("Docker sender socket already connected or connection attempt was made.", 'yellow')
        return

    cprint(f"Attempting to connect to Docker sender at {DOCKER_SENDER_HOST}:{DOCKER_SENDER_PORT}...", 'cyan')
    try:
        DOCKER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        DOCKER_SOCKET.settimeout(5) # Add a timeout for connection
        DOCKER_SOCKET.connect((DOCKER_SENDER_HOST, DOCKER_SENDER_PORT))
        cprint("Successfully connected to Docker sender.", 'green')
    except socket.error as e:
        cprint(f"Failed to connect to Docker sender: {e}", 'red')
        DOCKER_SOCKET = None # Ensure it's None if connection failed

def disconnect_docker_sender():
    global DOCKER_SOCKET
    if DOCKER_SOCKET:
        cprint("Disconnecting from Docker sender...", 'light_yellow')
        try:
            DOCKER_SOCKET.shutdown(socket.SHUT_RDWR) # Graceful shutdown
            DOCKER_SOCKET.close()
        except socket.error as e:
            cprint(f"Error closing Docker socket: {e}", 'red')
        finally:
            DOCKER_SOCKET = None
            cprint("Disconnected from Docker sender.", 'red')

def send_to_docker(message: str):
    global DOCKER_SOCKET
    if DOCKER_SOCKET:
        try:
            # cprint(f"Sending to Docker: {message.strip()}", 'magenta') # Optional: for debugging
            DOCKER_SOCKET.sendall(message.encode())
        except socket.error as e:
            cprint(f"Error sending data to Docker sender: {e}. Attempting to reconnect...", 'red')
            disconnect_docker_sender() # Close faulty socket
            # Optionally, you could try to reconnect immediately, or handle it more gracefully
            # connect_docker_sender() # Be careful with rapid reconnections
    else:
        # cprint("Docker sender not connected. Cannot send message.", 'yellow') # Can be noisy
        pass


async def scan_devices(): 
    tskin_devices: dict = dict()
    index = 1

    cprint('Scanning started...\n', 'light_magenta')

    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == TARGET_DEVICE_NAME:
            tskin_devices[index] = device.address
            index += 1
    
    return tskin_devices

def get_selected_tskin(devices: dict) -> str:
    while True:
        cprint('Select a TSKIN device.', 'light_cyan')
        for k,v in devices.items():
            cprint(f' press {k} for {v}', 'blue')
        print()
        try:
            selected_tskin_key = int(input('Select: '))
            if selected_tskin_key not in devices.keys():
                cprint('Oops.. Invalid number for tskin!\n', 'light_yellow')
                continue
            cprint(f'You selected {devices[selected_tskin_key]} tskin\n', 'light_green')
            return devices[selected_tskin_key]
        except ValueError:
            cprint('Oops.. Please enter a valid number!\n', 'light_yellow')


def get_selected_hand():
    while True:
        selected_hand= input('Select the hand (r=RIGHT, l=LEFT): ').lower().strip()
        if selected_hand not in ['r','l']:
            cprint('Ops.. Invalid value for hand!\n', 'light_yellow')
            continue
        tskin_hand = Hand.RIGHT if selected_hand == 'r' else Hand.LEFT
        cprint(f"You selected {tskin_hand.value} hand\n", 'light_green')
        return tskin_hand

def configure_tskin(tskin_mac: str, tskin_hand: Hand) -> None: # Returns None, sets global TSKIN
    model_folder = getcwd()
    TSKIN_NAME = "TSKIN_App" # Give it a unique name if needed

    gesture_config = GestureConfig(
        path.join(model_folder, "model.pickle"),
        path.join(model_folder, "encoder.pickle"),
        "demo",
        datetime.datetime.now(),
        ["up","down","push","pull","twist","circle","swipe_r","swipe_l"]
    )

    # Using TSpeechTSkinConfig and TSpeechHand for clarity, assuming they are compatible/same as tactigon_gear ones
    tskin_cfg = TSpeechTSkinConfig(tskin_mac, tskin_hand, TSKIN_NAME, gesture_config=gesture_config)

    voice_cfg = VoiceConfig(
        path.join(model_folder, "models.tflite"),
        path.join(model_folder, "tos.scorer"),
    )

    global TSKIN
    TSKIN = TSkin_Speech(tskin_cfg, voice_cfg)
    return

def select_program():
    programs = {
        1: 'gear',
        2: 'speech'
    }
    cprint('Select a program to execute.', 'light_cyan')
    while True:
        for k,v in programs.items():
            cprint(f' press {k} for {v}', 'blue')
        try:
            selected_program_key = int(input('\nSelect: '))
            if int(selected_program_key) not in programs.keys():
                cprint('Ops.. Invalid program!\n', 'light_yellow')
                continue
            return programs[selected_program_key]
        except ValueError:
            cprint('Ops.. Please enter a valid number!\n', 'light_yellow')

def speech():
    tspeech_obj = TSpeechObject(
        [
            TSpeech(
                [HotWord("start"), HotWord("enter")],
                TSpeechObject(
                    [
                        TSpeech(
                            [HotWord("application")]
                        )
                    ]
                )
            )
        ]
    )
    i = 0
    cprint("Tap to enable listening mode.", "light_cyan")
    send_to_docker("Speech program started. Tap to enable listening.\n")

    while True:
        if not TSKIN.connected:
            cprint("Reconnecting TSKIN..", 'light_magenta')
            time.sleep(0.5)
            continue

        if i > 2: # Exit condition for demo
            send_to_docker("Speech program tap-and-hold exit condition met.\n")
            break

        if TSKIN.is_listening:
            cprint("TSKIN Listening...", 'light_magenta')
            # send_to_docker("TSKIN is listening for voice commands.\n") # Can be very noisy
            time.sleep(0.5)
            continue

        touch = TSKIN.touch
        transcription = TSKIN.transcription

        if transcription:
            if transcription.timeout:
                if transcription.time == 0:
                    msg = "Silence timeout. No words found!"
                    cprint(msg, 'light_yellow')
                    send_to_docker(f"Speech: {msg}\n")
                else:
                    msg = f"Voice timeout. Processed up to {transcription.time}s." # Clarified message
                    cprint(msg, 'light_yellow')
                    send_to_docker(f"Speech: {msg}\n")
            else:
                msg = "Transcription found!"
                print(msg)
                send_to_docker(f"Speech: {msg} Content: {transcription}\n")

            cprint(transcription, 'green')

        if touch:
            touch_info = f"Speech Touch: {touch.one_finger.name if touch.one_finger else 'multi-finger'}\n" # More descriptive
            cprint(touch_info.strip(), 'blue')
            send_to_docker(touch_info)

            if touch.one_finger == TSpeechOneFingerGesture.TAP_AND_HOLD:
                i += 1
            elif touch.one_finger == TSpeechOneFingerGesture.SINGLE_TAP:
                if TSKIN.listen(tspeech_obj):
                    msg = "Waiting for voice commands...\nTry to say:\n - Start application\n - Enter application"
                    cprint(msg, 'light_magenta')
                    send_to_docker("TSKIN now listening for specific voice commands.\n")
                else:
                    cprint("Failed to start listening mode.", 'yellow')
                    send_to_docker("TSKIN failed to start listening mode.\n")
        else:
            i = 0
        time.sleep(0.02)
    send_to_docker("Speech program ended.\n")

def gear():
    i = 0
    send_to_docker("Gear program started.\n")
    while True:
        if not TSKIN.connected:
            cprint("Reconnecting TSKIN..", 'light_magenta')
            time.sleep(0.2)
            continue

        if i > 5: # Exit condition for demo
            send_to_docker("Gear program tap-and-hold exit condition met.\n")
            break

        t = TSKIN.touch
        a = TSKIN.angle # Angle data
        g = TSKIN.gesture

        # Periodically send angle data if you want a continuous stream
        # For example, every 0.5 seconds if angle data is available
        # current_time = time.time()
        # if hasattr(gear, 'last_angle_send_time') and current_time - gear.last_angle_send_time > 0.5 and a:
        #     send_to_docker(f"Angle: {a}\n")
        #     gear.last_angle_send_time = current_time
        # elif not hasattr(gear, 'last_angle_send_time'):
        #     gear.last_angle_send_time = current_time

        cprint(f"Angle: {a}", 'light_grey') # Keep printing locally

        if g:
            cprint(f"Gesture: {g}", 'green')
            send_to_docker(f"Gesture: {g.name}\n") # Send gesture name
            # time.sleep(1) # This sleep might interrupt other logic or Docker sending. Consider removing if not essential.
        elif t: # Use elif to avoid sending touch if a gesture (which might involve touch) was already sent
            cprint(f"Touch: {t}", 'green')
            send_to_docker(f"Touch: {t.one_finger.name if t.one_finger else 'multi-finger'}\n") # Send touch type
            # time.sleep(1) # Same consideration as above

        if t and t.one_finger == OneFingerGesture.TAP_AND_HOLD:
            i += 1
        else:
            i = 0
        time.sleep(0.02)
    send_to_docker("Gear program ended.\n")


def connect_tskin():
    if not TSKIN:
        cprint("TSKIN not configured. Cannot connect.", 'red')
        return False
    while not TSKIN.connected:
        cprint("Connecting to TSKIN..", 'light_magenta')
        time.sleep(0.5) # Allow some time for connection attempt
        if not TSKIN.is_alive() and not TSKIN.connected: # Check if thread died before connecting
            cprint("TSKIN thread is not alive and not connected. Restarting TSKIN.", 'yellow')
            TSKIN.start() # Try to restart it
            time.sleep(1) # Give it time to start
    cprint("TSKIN Connected!", 'green')
    send_to_docker("TSKIN Connected.\n")
    return True

def cleanup_connections():
    global TSKIN # Ensure we're using the global TSKIN
    cprint("Initiating cleanup...", 'light_cyan')
    if TSKIN: # Check if TSKIN was initialized
        if TSKIN.connected:
            cprint("Disconnecting TSKIN...", 'light_yellow')
            TSKIN.terminate()
            # Wait for TSKIN to actually terminate
            # join_timeout = 5 # seconds
            # TSKIN.join(timeout=join_timeout)
            # if TSKIN.is_alive():
            #     cprint(f"TSKIN did not terminate within {join_timeout}s.", 'red')
            # else:
            cprint("TSKIN Disconnected!", 'red')
            send_to_docker("TSKIN Disconnected.\n") # Send before Docker disconnect
        elif TSKIN.is_alive(): # If not connected but thread is alive
            cprint("TSKIN thread is alive but not connected. Terminating...", 'light_yellow')
            TSKIN.terminate()
            cprint("TSKIN thread terminated.", 'red')
    else:
        cprint("TSKIN was not initialized. No TSKIN cleanup needed.", 'light_grey')

    disconnect_docker_sender() # Disconnect Docker sender last
    cprint("Cleanup complete.", 'light_cyan')


def main():
    cprint('We are looking for your Tactigon Skin...', 'light_magenta')

    devices = asyncio.run(scan_devices())
    if not devices:
        cprint("We couldn't find any TSKIN devices! Exiting.", 'light_yellow')
        return

    mac_address = get_selected_tskin(devices)
    hand = get_selected_hand()
    program_name = select_program() # Renamed to program_name

    configure_tskin(mac_address, hand)

    if TSKIN is None:
        cprint("TSKIN configuration failed. Exiting.", "red")
        return

    TSKIN.start() # Start TSKIN processing thread

    # Connect to Docker Sender first, so it's ready if TSKIN connection is quick
    connect_docker_sender()

    if not connect_tskin(): # connect_tskin now returns status
        cprint("Failed to connect to TSKIN. Exiting.", "red")
        cleanup_connections()
        return

    # Run the selected program
    if program_name in globals() and callable(globals()[program_name]):
        globals()[program_name]()
    else:
        cprint(f"Program '{program_name}' not found!", 'red')

    cleanup_connections()
    cprint("Application finished.", 'light_blue')


if __name__ == '__main__':
    print(f"Tactigon Gear Version: {tactigon_gear.__version__}")
    try:
        main()
    except KeyboardInterrupt:
        cprint("\nKeyboardInterrupt received. Exiting gracefully...", 'orange')
    except Exception as e:
        cprint(f"An unhandled exception occurred: {e}", 'red')
        import traceback
        traceback.print_exc()
    finally:
        cleanup_connections() # Ensure cleanup happens even on unexpected exit