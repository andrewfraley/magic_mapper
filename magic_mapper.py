import os
import re
import time
import struct
import subprocess
import json
import fcntl

# We need the socket library for send_tcp_command(), but this isn't always installed in WebOS
try:
    import socket
    SOCKET_AVAILABLE = True
except ImportError:
    SOCKET_AVAILABLE = False

BLOCK_MOUSE = False  # Set to True to disable the mouse, note EXCLUSIVE_MODE must be True to work
EXCLUSIVE_MODE = True  # Prevent bound codes from being seen by WebOS, must be True for BLOCK_MOUSE

DEVICE_NAME = 'LGE M-RCU - Builtin [0]'   # the exact Name= shown in /proc/bus/input/devices
# DEVICE_NAME = 'LGE M-RCU - Builtin [1]'   # UNTESTED - Try this for IR remotes


OUTPUT_DEVICE = "/dev/input/event4"  # unbound codes get resent to this device in exclusive mode


BUTTONS = {
    398: "red",
    399: "green",
    400: "yellow",
    401: "blue",
    402: "ch_up",
    403: "ch_down",
    115: "vol_up",
    114: "vol_down",
    207: "play",
    119: "pause",
    128: "stop",
    167: "record",
    168: "rewind",
    208: "fastforward",
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
    1037: "netflix",
    1042: "disney",
    1043: "lg_channels",
    1086: "alexa",
    1117: "google",
    362: "guide",
    428: "voice",
    771: "channels",
    787: "channels_alt",  # seen on an LG IR remote
    994: "...",
    799: "...alt",  # seen on an LG IR remote, button with three dots surrounded by a rectangle
    1083: "search",
    217: "search_alt",  # seen on an LG IR remote
    174: "exit",  # seen on an LG IR remote, appears to exit apps
    829: "sap",
    1116: "tv",
    358: "info",
    773: "home",
    28: "ok"
}

MOUSE_WHEEL = {
     1: "wheel_up",
    -1: "wheel_down"
}

EVIOCGRAB = 1074021776  # Don't mess with this


def cycle_energy_mode(inputs):
    """cycle energy modes between min med max off"""
    modes = ["max", "med", "min", "off"]
    if inputs.get("reverse_order"):
        modes.reverse()
    current_mode = get_picture_settings()["settings"]["energySaving"]

    if current_mode in modes:
        next_mode = modes.index(current_mode) + 1
    else:  # It's probably in auto mode so just start at the first mode
        next_mode = 0

    if next_mode >= len(modes):
        next_mode = 0

    inputs["mode"] = modes[next_mode]
    set_energy_mode(inputs)


def toggle_eye_comfort(inputs):
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
    if inputs.get("notifications"):
        show_message("Reduce blue light mode: %s" % new_mode)


def screen_off(inputs):
    """Turns the screen off, but not the TV itself.
    Press any button but power and vol to turn it back on.
    """
    endpoint = "luna://com.webos.service.tvpower/power/turnOffScreen"
    payload = {}
    luna_send(endpoint, payload)


def set_energy_mode(inputs):
    """Sets the energy savings mode
    Inputs:
        - mode (string, default: none)
            - Valid values: min med max off auto screen_off
    Note screen_off may not work on some models, best to use the screen_off function instead
    """
    mode = inputs["mode"]
    endpoint = "luna://com.webos.settingsservice/setSystemSettings"
    payload = {"category": "picture", "settings": {"energySaving": mode}}
    luna_send(endpoint, payload)
    if inputs.get("notifications"):
        show_message("Energy mode: %s" % mode)


def increase_oled_light(inputs):
    """Increase the oled light value
    Inputs:
        increment (10) - the value to raise the light level on each press
        disable_energy_savings (True) - If energy savings is on, disable it
    """
    increment_oled_light(inputs, direction="up")


def reduce_oled_light(inputs):
    """Decrease the oled light value
    Inputs:
        increment (10) - the value to lower the light level on each press
        disable_energy_savings (True) - If energy savings is on, disable it
    """
    increment_oled_light(inputs, direction="down")


def set_oled_backlight(inputs):
    backlight = inputs["backlight"]
    endpoint = "luna://com.webos.settingsservice/setSystemSettings"
    payload = {"category": "picture", "settings": {"backlight": backlight}}
    luna_send(endpoint, payload)
    if inputs.get("notifications"):
        show_message("OLED Backlight: %s" % backlight)


def launch_app(inputs):
    """Launch an app by app_id
    Inputs: app_id  - Use list_apps.py to get the app_id
    """
    app_id = inputs["app_id"]
    endpoint = "luna://com.webos.service.applicationmanager/launch"
    payload = {"id": app_id}
    luna_send(endpoint, payload)


def send_ir_command(inputs):
    """Send an IR command to a configured device
    This relies on you using the device connection manager to setup your IR device (ie a soundbar)
    Once setup you can use this function to have the remote send IR commands
    """
    tv_input = inputs["tv_input"]  # "OPTICAL", other inputs untested
    keycode = inputs["keycode"]  # "IR_KEY_VOLUP" "IR_KEY_POWER"
    device_type = inputs["device_type"]  # "audio"

    endpoint = "luna://com.webos.service.irdbmanager/sendIrCommand"
    payload = {
        "keyCode": keycode,
        "buttonState": "single",
        "connectedInput": tv_input,
        "deviceType": device_type,
    }
    luna_send(endpoint, payload)


def curl(inputs):
    """Execute the system curl binary with the provided inputs
    Note this script has to work on Python 2.7 and 3.x, and very
    few Python libraries are included in WebOS, so we'll just
    keep it simple and use the system curl binary vs urllib.
    """

    url = inputs.get("url")
    if not url:
        print("ERROR: curl function called but url not supplied")

    method = inputs.get("method", "GET").upper()

    command_string = "curl -vs -X %s" % method
    command = command_string.split()

    headers = inputs.get("headers")
    if headers:
        if type(headers) == list:
            for header in headers:
                command.append("-H")
                command.append(header)
        elif type(headers) != str:  # Python 2.7 on the C9 returns unicode instead of str
            headers = str(headers)
            command.append("-H")
            command.append(headers)

    data = inputs.get("data")
    if data:
        command.append("-d")
        command.append(data)

    command.append(url)
    print("Running curl command: %s" % " ".join(command))

    try:
        output = subprocess.check_output(command)
    except subprocess.CalledProcessError as error:
        print("WARNING: curl command failed")
        print(error)
        return

    return output


def press_button(inputs):
    """Simulate a button press on the remote
    This is useful to simulate the play and pause buttons for remotes that don't have these buttons
    Inputs: button_name (str)
    """
    button = inputs["button"]
    keycode = get_keycode(button)
    if not keycode:
        return
    print("Simulating keystroke with button '%s' (keycode %s)" % (button, keycode))
    send_keystroke(OUTPUT_DEVICE, keycode)


def send_cec_button(inputs):
    """This sends an HDMI-CEC button press to the current input device
    Consider this experimental, little is known about how this works (from my perspective as the developer)
    Inputs:
        code (integer, default: none) - The code to send.  Only code known at present is 18882561 which is "Home".
    """
    code = inputs["code"]
    if WEBOS_MAJOR_VERSION < 5:
        endpoint = "luna://com.webos.service.tv.keymanager/createKeyEvent"
        code_key = "code"
    else:
        endpoint = "luna://com.webos.service.eim/cec/sendKeyEvent"
        code_key = "key"

    payload = {code_key: code, "device": "remoteControl", "id": "magic_mapper", "type": "keyDown"}
    luna_send(endpoint, payload)
    payload["type"] = "keyUp"
    luna_send(endpoint, payload)


def set_dynamic_tone_mapping(inputs):
    """Set a specific value for Dynamic Tone Mapping
    Inputs:
        - value (string, default: none)
            - Valid values: "off", "on", "HGIG"
    """
    value = inputs["value"]

    # values are case sensitive
    if value.upper() == "HGIG":
        value = "HGIG"
    else:
        value = value.lower()

    endpoint = "luna://com.webos.settingsservice/setSystemSettings"
    payload = {"category": "picture", "settings": {"hdrDynamicToneMapping": value}}
    luna_send(endpoint, payload)

def disabled(inputs):
    print("Key was disabled")

def send_tcp_command(inputs):
    """Send a TCP command to a specified IP address and port.
    Inputs:
        ip (str): The IP address of the target device.
        port (int): The port number of the target device.
        command (str): The command string to send.
        timeout (float, optional): Socket timeout in seconds. Default is 5.
    """
    if not SOCKET_AVAILABLE:
        print("ERROR: socket library is not available, cannot use send_tcp_command()")
        return

    ip = inputs.get("ip")
    port = inputs.get("port")
    command = inputs.get("command")
    timeout = inputs.get("timeout", 5.0)

    if not ip or not port or command is None: # command can be an empty string
        print("ERROR: send_tcp_command called with missing ip, port, or command")
        return

    try:
        # Ensure command is a string and ends with a newline for many TCP services
        if not command.endswith("\r\n"):
            command += "\r\n"

        # Convert command to bytes
        command_bytes = command.encode('utf-8')

        print("Sending TCP command '%s' to %s:%s" % (command, ip, port))

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        sock.sendall(command_bytes)
        # Optionally, receive a response
        # response = sock.recv(1024)
        # print("Received response: %s" % response.decode('utf-8'))
        sock.close()
        print("TCP command sent successfully.")
    except socket.error as e:
        print("ERROR: Could not send TCP command to %s:%s - %s" % (ip, port, e))
    except Exception as e:
        print("ERROR: An unexpected error occurred in send_tcp_command: %s" % e)

###################################
# Private Functions
# The fuctions below here should not be called by magic_mapper_config.json
####################################


def get_button_map():
    """Read the json config file"""
    config_path = os.path.join(os.path.dirname(__file__), "magic_mapper_config.json")
    with open(config_path) as config_file:
        button_map = json.load(config_file)
    return button_map


def fire_event_one(action):
    """Execute the function configured for the button"""
    func_name = action["function"]
    print("func_name: %s" % func_name)
    inputs = action.get("inputs", {})
    globals()[func_name](inputs)

def fire_events(actions):
    """Execute the function(s) configured for the button"""
    for action in actions:
        fire_event_one(action)


def luna_send(endpoint, payload):
    # Execute luna send and return the output

    command = ["/usr/bin/luna-send", "-n", "1"]
    command.append(endpoint)
    command.append(json.dumps(payload))
    print("running command: %s" % command)
    output = subprocess.check_output(command)
    return output


def increment_oled_light(inputs, direction):
    """Increment the oled backlight up or down"""
    increment = inputs.get("increment", 10)

    current_settings = get_picture_settings()["settings"]

    disable_energy_savings = str_to_bool(inputs.get("disable_energy_savings", True))
    if disable_energy_savings:
        if current_settings["energySaving"] != "off":
            set_energy_mode({"mode": "off"})

    current_value = int(current_settings["backlight"])

    if direction == "up":
        new_value = current_value + increment
        if new_value > 100:
            new_value = 100
    elif direction == "down":
        new_value = current_value - increment
        if new_value < 0:
            new_value = 0

    inputs["backlight"] = new_value
    set_oled_backlight(inputs)


def get_picture_settings():
    # Return the current settings
    endpoint = "luna://com.webos.settingsservice/getSystemSettings"
    payload = {"category": "picture"}
    output = luna_send(endpoint, payload)
    settings = json.loads(output)
    return settings


def show_message(message):
    """Shows a "toast" message"""
    endpoint = "luna://com.webos.notification/createToast"
    payload = {"message": message}
    luna_send(endpoint, payload)


def get_keycode(button):
    """Returns the keycode associated with the button name"""
    keys = [k for k, v in BUTTONS.items() if v == button]
    if keys:
        return keys[0]

    print('ERROR: Button "%s" not found!' % button)
    return None


def send_keystroke(device, keycode):
    """Send a keystroke to the input device
        We use this to simulate button presses like play/pause since those require special handling
        Use the press_button function for magic_mapper_config.json
    };
    """
    send_input_event(device, keycode, 1, 1)
    send_input_event(device, 0, 0, 0)
    send_input_event(device, keycode, 0, 1)
    send_input_event(device, 0, 0, 0)


def send_input_event(device, keycode, value, event_type):
    """Low level function to write to the input device file
    Don't call this from magic_mapper_config.json
    """
    input_format = "llHHI"

    out_file = os.open(device, os.O_RDWR)
    now = time.time()
    tv_sec = int(now)
    tv_usec = int((now - tv_sec) * 1000000)

    data = [tv_sec, tv_usec, event_type, keycode, value]
    # print("writing: %s" % data)

    event = struct.pack(input_format, *data)
    os.write(out_file, event)
    os.close(out_file)


def str_to_bool(string):
    """Convert string to bool"""
    if string.lower() in ["yes", "true"]:
        return True
    return False


def get_webos_version():
    """Return webos version"""
    with open("/etc/starfish-release") as f:
        release = f.read()

    version = release.split()[2]
    major_version = version.split(".")[0]
    return int(major_version)


def input_loop(button_map):
    # Read from the input device
    # https://stackoverflow.com/a/16682549/866057
    input_format = "llHHi"
    event_size = struct.calcsize(input_format)
    buttons_waiting = {}

    input_device_path = resolve_input_device_by_name(DEVICE_NAME)
    print("Opening input device: %s" % input_device_path)
    input_device = open(input_device_path, "rb")

    if EXCLUSIVE_MODE:
        print("EXCLUSIVE_MODE is enabled, taking over input device")
        fcntl.ioctl(input_device, EVIOCGRAB, 1)
        output_device = os.open(OUTPUT_DEVICE, os.O_WRONLY)
    else:
        print("EXCLUSIVE_MODE is disabled, will not override default button behavior")
        output_device = None

    first_loop = 2
    while True:

        if first_loop == 1:
            print("First loop complete, Magic Mapper is running")
            first_loop = 0
        elif first_loop == 2:
            print("Input loop started, waiting for button presses")
            first_loop = 1


        event = input_device.read(event_size)
        (tv_sec, tv_usec, event_type, code, value) = struct.unpack(input_format, event)

        now = time.time()
        key = None
        if event_type == 1:
            key = BUTTONS.get(code)
        elif event_type == 2:
            code = value # up/down
            key = MOUSE_WHEEL.get(code)
            value = 0
            buttons_waiting[code] = now
        actions = button_map.get(key)
        if actions == "disabled":
            print("Button %s is disabled" % key)
            continue
        current_app = None
        if actions:
            if type(actions) is not list:
                actions = [actions]
            endpoint = "luna://com.webos.applicationManager/getForegroundAppInfo"
            current_app = luna_send(endpoint, {})
            current_app = json.loads(current_app).get('appId')
            filtered_actions = []
            found_match = False
            for action in actions:
                appId = action.get('appId')
                if appId is None:
                    filtered_actions += [action]
                if appId == current_app:
                    filtered_actions += [action]
                    found_match = True
                if appId == '!' and not found_match:
                    filtered_actions += [action]
            actions = filtered_actions

        if not actions:
            # If in exclusive mode, we need to send the input event back so it can be read by others
            if EXCLUSIVE_MODE and not (BLOCK_MOUSE and code == 1198):
                os.write(output_device, event)
            if key and value == 1:
                print("Button %s not configured in magic_mapper_config.json" % key)
            elif value == 1:
                print("Button code %s ignored" % code)
            continue

        # Button Down
        if value == 1:
            print("%s button down" % key)
            if code in buttons_waiting and now - buttons_waiting[code] < 1.0:
                print("WARNING: Got code %s DOWN while waiting for UP" % code)
            buttons_waiting[code] = now

        # Button Up
        if value == 0:
            if code not in buttons_waiting:
                print("WARNING: Got code %s UP with no DOWN" % code)
            elif now - buttons_waiting[code] > 1.0:
                print("Ignoring long press of %s" % key)
            else:
                print("%s button up" % key)
                print("firing event(s) for code: %s button: %s" % (code, key))
                fire_events(actions)
            if code in buttons_waiting:
                del buttons_waiting[code]


def resolve_input_device_by_name(device_name):
    """
    Find the input device path by looking for the device_name in /proc/bus/input/devices
    """
    print("Resolving input device path for device named '%s'" % device_name)
    try:
        with open("/proc/bus/input/devices", "r") as f:
            data = f.read()
    except Exception as e:
        print("ERROR: cannot read /proc/bus/input/devices: %s" % e)
        return None

    # Split on blank lines; each block describes one device
    blocks = re.split(r"\n\s*\n", data.strip())
    for block in blocks:
        # Look for N: Name="..."
        m_name = re.search(r'^N:\s+Name="([^"]+)"', block, flags=re.M)
        if not m_name:
            continue
        if m_name.group(1) != device_name:
            continue

        # Found our device; look for H: Handlers=...
        m_handlers = re.search(r'^H:\s+Handlers=([^\n]+)', block, flags=re.M)
        if not m_handlers:
            continue

        handlers = m_handlers.group(1).split()
        # pick the first 'eventX'
        for h in handlers:
            if h.startswith("event") and h[5:].isdigit():
                event_path = "/dev/input/" + h
                print("Resolved '%s' to %s" % (device_name, event_path))
                return event_path

    print("WARNING: device named '%s' not found in /proc/bus/input/devices" % device_name)
    return None


def main():
    """MAIN"""
    print("Starting Magic Mapper")
    time.sleep(2) # Ensure everything is running before we start
    button_map = get_button_map()

    global WEBOS_MAJOR_VERSION
    WEBOS_MAJOR_VERSION = get_webos_version()
    print("WEBOS_MAJOR_VERSION: %s" % WEBOS_MAJOR_VERSION)

    print("BLOCK_MOUSE is %s" % BLOCK_MOUSE)

    input_loop(button_map=button_map)


if __name__ == "__main__":
    main()
