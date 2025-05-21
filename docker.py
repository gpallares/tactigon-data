import asyncio
from bleak import BleakScanner
from termcolor import cprint
import time
import datetime
from os import path, getcwd
from tactigon_gear import TSkin, TSkinConfig, Hand, GestureConfig, OneFingerGesture
from tactigon_speech import TSkin_Speech, TSkinConfig, Hand, VoiceConfig, OneFingerGesture, TSpeechObject, TSpeech, HotWord
import socket  # Add this import

TARGET_DEVICE_NAME = "TSKIN50"
TSKIN: TSkin = None

# TCP client global
TCP_CLIENT = None

async def scan_devices(): 
    tskin_devices: dict = dict()
    index = 1

    cprint('Scanning started...\n', 'light_magenta')
    send_tcp_message('Scanning started...\n')

    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == TARGET_DEVICE_NAME:
            tskin_devices[index] = device.address
            index += 1
    
    return tskin_devices

def get_selected_tskin(devices: dict) -> str:

    while True:
        cprint('Select a TSKIN device.', 'light_cyan')
        send_tcp_message('Select a TSKIN device.')

        for k,v in devices.items():
            cprint(f' press {k} for {v}', 'blue')
            send_tcp_message(f' press {k} for {v}')
        
        print()
        selected_tskin = int(input('Select: '))

        if int(selected_tskin) not in devices.keys():
            cprint('Ops.. Invalid number for tskin!\n', 'light_yellow')
            send_tcp_message('Ops.. Invalid number for tskin!\n')
            continue

        cprint(f'You selected {devices[selected_tskin]} tskin\n', 'light_green')
        send_tcp_message(f'You selected {devices[selected_tskin]} tskin\n')

        return devices[selected_tskin]

def get_selected_hand():
    while True:
        selected_hand= input('Select the hand (r=RIGHT, l=LEFT): ').lower().strip() 

        if selected_hand not in ['r','l']:
            cprint('Ops.. Invalid value for hand!\n', 'light_yellow')
            send_tcp_message('Ops.. Invalid value for hand!\n')
            continue

        tskin_hand = Hand.RIGHT if selected_hand == 'r' else Hand.LEFT

        cprint(f"You selected {tskin_hand.value} hand\n", 'light_green')
        send_tcp_message(f"You selected {tskin_hand.value} hand\n")
        return tskin_hand

def configure_tskin(tskin_mac: str, tskin_hand: Hand) -> TSkin:
    model_folder = getcwd()

    TSKIN_NAME = "TSKIN"

    gesture_config = GestureConfig(
        path.join(model_folder, "model.pickle"), 
        path.join(model_folder, "encoder.pickle"),
        "demo",
        datetime.datetime.now(),
        ["up","down","push","pull","twist","circle","swipe_r","swipe_l"]
    )

    tskin_cfg = TSkinConfig(tskin_mac, tskin_hand, TSKIN_NAME, gesture_config)

    voice_cfg = VoiceConfig(
        path.join(model_folder, "models.tflite"), 
        path.join(model_folder, "tos.scorer"),

    )

    global TSKIN
    TSKIN = TSkin_Speech(tskin_cfg, voice_cfg)

    return

def send_tcp_message(msg):
    global TCP_CLIENT
    if TCP_CLIENT:
        try:
            TCP_CLIENT.sendall((str(msg) + '\n').encode())
        except Exception as e:
            pass  # Optionally print or log error

def select_program():
    programs = {
        1: 'gear',
        2: 'speech'
    }

    cprint('Select a program to execute.', 'light_cyan')
    send_tcp_message('Select a program to execute.')

    while True:
        for k,v in programs.items():
            cprint(f' press {k} for {v}', 'blue')
            send_tcp_message(f' press {k} for {v}')

        selected_program = int(input('\nSelect: '))

        if int(selected_program) not in programs.keys():
            cprint('Ops.. Invalid program!\n', 'light_yellow')
            send_tcp_message('Ops.. Invalid program!\n')
            continue
    
        return programs[selected_program]
    
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
    send_tcp_message("Tap to enable listening mode.")

    while True:
        if not TSKIN.connected:
            cprint("Reconnecting..", 'light_magenta')
            send_tcp_message("Reconnecting..")
            time.sleep(0.5)
            continue

        if i > 2:
            break

        if TSKIN.is_listening:
            cprint("Listening...", 'light_magenta')
            send_tcp_message("Listening...")
            time.sleep(0.5)
            continue

        touch = TSKIN.touch
        transcription = TSKIN.transcription

        if transcription:
            if transcription.timeout:
                if transcription.time == 0:
                    cprint("Silence timeout. No words found!", 'light_yellow')
                    send_tcp_message("Silence timeout. No words found!")
                else:
                    cprint("Voice timeout. Cannot process more than", 'light_yellow')
                    send_tcp_message("Voice timeout. Cannot process more than")
            else:
                print("Transcription found!")
                send_tcp_message("Transcription found!")

            cprint(transcription, 'green')
            send_tcp_message(transcription)

        if touch:
            if touch.one_finger == OneFingerGesture.TAP_AND_HOLD:
                i += 1
            elif touch.one_finger == OneFingerGesture.SINGLE_TAP:
                if TSKIN.listen(tspeech_obj):
                    cprint("Waiting for voice commands...", 'light_magenta')
                    send_tcp_message("Waiting for voice commands...")
                    cprint("Try to say:\n - Start application\n - Enter applcaition\n", 'blue')
                    send_tcp_message("Try to say:\n - Start application\n - Enter applcaition\n")
        else:
            i = 0

        time.sleep(0.02)

def gear():

    i = 0

    while True:
        if not TSKIN.connected:
            cprint("Reconnecting..", 'light_magenta')
            send_tcp_message("Reconnecting..")
            time.sleep(0.2)
            continue

        if i > 5:
            break

        t = TSKIN.touch
        a = TSKIN.angle
        g = TSKIN.gesture

        cprint(a, 'light_grey')
        send_tcp_message(a)

        if g or t:
            cprint(g if g else t, 'green')
            send_tcp_message(g if g else t)
            time.sleep(1)

        if t and t.one_finger == OneFingerGesture.TAP_AND_HOLD:
            i += 1
        else:
            i = 0

        time.sleep(0.02)

def connect_tskin():
    while not TSKIN.connected:
        cprint("Connecting..", 'light_magenta')
        send_tcp_message("Connecting..")
        time.sleep(0.5)
    
    cprint("Connected!", 'green')
    send_tcp_message("Connected!")

def disconnect_tskin():
    if TSKIN and TSKIN.connected:
        cprint("Disconnecting...", 'light_yellow')
        send_tcp_message("Disconnecting...")
        TSKIN.terminate()
        cprint("Disconnected!", 'red')
        send_tcp_message("Disconnected!")

def main():
    global TCP_CLIENT
    cprint('We are looking for your Tactigon Skin...', 'light_magenta')
    send_tcp_message('We are looking for your Tactigon Skin...')

    # Connect to TCP server
    try:
        TCP_CLIENT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCP_CLIENT.connect(('192.168.10.102', 8888))
        send_tcp_message('Connected to TCP server.')
    except Exception as e:
        print(f'Could not connect to TCP server: {e}')
        TCP_CLIENT = None

    while True:

        devices = asyncio.run(scan_devices())
        devices_count = len(devices)

        if devices_count == 0:
            cprint("We couldn't find any TSKIN devices! press enter to rescan..", 'light_yellow')
            send_tcp_message("We couldn't find any TSKIN devices! press enter to rescan..")
            input()
            continue
        else:
            mac_address = get_selected_tskin(devices)
            hand = get_selected_hand()
            program = select_program()

            configure_tskin(mac_address, hand)
            TSKIN.start()
            connect_tskin()

            globals()[program]()

        disconnect_tskin()
        if TCP_CLIENT:
            TCP_CLIENT.close()
        return

if __name__ == '__main__':
    try:
        main()
    except(KeyboardInterrupt):
        disconnect_tskin()