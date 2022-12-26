import time
import struct
import subprocess
import json

# import logging

SETTINGS = {
    "show_notifications": True,  # Will present "toast" notification dialogs on some settings changes like eye comfort and energy mode
    "backlight_increment": 10,  # For each button press, how much to raise or lower the brightness
    "input_device": "/dev/input/event3",  # You shouldn't need to change this unless newer hardware in the future moves the input device used for the remote
}

FUNCTION_MAP = {
    "yellow": "cycle_energy_mode",  # cycles the energy savings modes
    "blue": "toggle_eye_comfort",  # aka reduce blue light
    "red": "reduce_oled_light",
    "green": "increase_oled_light",
}

BUTTONS = {
    398: "red",
    399: "green",
    400: "yellow",
    401: "blue",
    402: "ch_up",
    403: "ch_down",
    207: "play",
    119: "pause",
    2: "1",
    3: "2",
    4: "3",
    5: "4",
    6: "5",
    7: "6",
    8: "7",
    9: "8",
    10: "9",
    11: "0",
    1038: "prime",
    1037: "netflix"
}


def main():
    """MAIN"""

    infile_path = SETTINGS["input_device"]
    FORMAT = "llHHI"
    EVENT_SIZE = struct.calcsize(FORMAT)

    in_file = open(infile_path, "rb")

    event = in_file.read(EVENT_SIZE)

    code_wait = None  # Are we waiting for button up
    code_wait_start = None
    while event:
        (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)

        if code in BUTTONS:

            print("button code: %s" % code)
            print("button value: %s" % value)
            print("code_wait: %s" % code_wait)
            print("code_wait_start: %s" % code_wait_start)

            if not code_wait and value == 1:  # Start waiting for button up
                print("%s button down" % BUTTONS[code])
                code_wait = code
                code_wait_start = time.time()
            elif code_wait == code and value == 0:

                # We need to ignore long presses
                now = time.time()
                button_hold_duration = now - code_wait_start
                print("button_hold_duration: %s" % button_hold_duration)

                code_wait = None
                code_wait_start = None

                if button_hold_duration < 1.0:
                    print("%s button up" % BUTTONS[code])
                    fire_event(code)
                else:
                    print("Ignoring long press of %s" % BUTTONS[code])

        event = in_file.read(EVENT_SIZE)

    in_file.close()


def fire_event(code):
    print("firing event for code: %s" % code)
    button_name = BUTTONS[code]
    print("button_name: %s" % button_name)

    if button_name not in FUNCTION_MAP:
        print("Button %s not in FUNCTION_MAP" % button_name)
        return

    func_name = FUNCTION_MAP[button_name]
    print("func_name: %s" % func_name)
    globals()[func_name]()


def luna_send(endpoint, payload):
    # Execute luna send and return the output

    command = ["/usr/bin/luna-send", "-n", "1"]
    command.append(endpoint)
    command.append(json.dumps(payload))
    print("running command: %s" % command)
    output = subprocess.check_output(command)
    return output


def cycle_energy_mode():
    # cycle energy modes between min med max off
    modes = ["max", "med", "min", "off"]
    current_mode = get_picture_settings()["settings"]["energySaving"]
    next_mode = modes.index(current_mode) + 1
    if next_mode >= len(modes):
        next_mode = 0
    set_energy_mode(modes[next_mode])


def toggle_eye_comfort():
    """Toggle the eye comfort mode aka reduce blue light"""
    current_mode = get_picture_settings()["settings"]["eyeComfortMode"]
    print("current eye comfort mode: current_mode %s" % current_mode)
    if current_mode == "off":
        new_mode = "on"
    else:
        new_mode = "off"
    endpoint = "luna://com.webos.settingsservice/setSystemSettings"
    payload = {"category": "picture", "settings": {"eyeComfortMode": new_mode}}
    luna_send(endpoint, payload)
    show_message("Reduce blue light mode: %s" % new_mode)


def set_energy_mode(mode):
    """Sets the energy savings mode"""
    endpoint = "luna://com.webos.settingsservice/setSystemSettings"
    payload = {"category": "picture", "settings": {"energySaving": mode}}
    luna_send(endpoint, payload)
    show_message("Energy mode: %s" % mode)


def increase_oled_light():
    increment_oled_light('up')


def reduce_oled_light():
    increment_oled_light('down')


def increment_oled_light(up_or_down):
    increment = int(SETTINGS['backlight_increment'])
    current_value = get_picture_settings()["settings"]["backlight"]

    if up_or_down == 'up':
        new_value = current_value + increment
        if new_value > 100:
            new_value = 100
    elif up_or_down == "down":
        new_value = current_value - increment
        if new_value < 0:
            new_value = 0

    endpoint = "luna://com.webos.settingsservice/setSystemSettings"
    payload = {"category": "picture", "settings": {"backlight": new_value}}
    luna_send(endpoint, payload)


def get_picture_settings():
    # Return the current settings
    endpoint = "luna://com.webos.settingsservice/getSystemSettings"
    payload = {"category": "picture"}
    output = luna_send(endpoint, payload)
    settings = json.loads(output)
    return settings


def show_message(message):
    """Shows a "toast" message"""

    if SETTINGS["show_notifications"]:
        endpoint = "luna://com.webos.notification/createToast"
        payload = {"message": message}
        luna_send(endpoint, payload)


if __name__ == "__main__":
    main()
