# Magic Mapper

## Summary

Magic Mapper is a script that will let you remap unused buttons on the LG Magic Remote. The script itself runs on your rooted LG TV, detects button presses, and allows you to control anything available via the [luna-send api](https://www.webosose.org/docs/tools/commands/luna-send/). Note your TV must be rooted to use this.

## Currently Supported Functions

The script has support to do the the following (default config button):

-   Decrease the OLED light (red button)
-   Increase the OLED light (green button)
-   Set a specific OLED light value (not configured by default)
-   Cycle the energy savings modes (yellow button)
-   Set a specific energy savings mode
-   Turn the screen off (9 button - uses set_energy_mode)
-   Toggle the Eye Comfort Mode (also known as Reduce Blue Light) (blue button)
-   Launch an app (not configured by default)
-   Send IR commands to a device configured by the Device Connector (ie have a shortcut key to toggle power on for an optical connected soundbar)

## TV Models supported

-   LG C9 - Fully tested on FW 05.30.25
-   LG CX - Not tested, but should work.
-   LG C1 - Not tested, but should work.
-   LG C2 - Fully tested

## Installation / Setup

-   Root your TV using https://rootmy.tv/ and install the Home Brew app
    -   Note the above link is likely to fail on the newest firmware.
    -   Instead, follow this guide (C2 and probably C1 have issues, see next bullet): https://github.com/RootMyTV/RootMyTV.github.io/issues/85#issuecomment-1295058979
    -   The above instructions work fine for a C9, but a C2 requires additional steps for SSH to work, [outlined here](https://github.com/RootMyTV/RootMyTV.github.io/issues/85#issuecomment-1364765232):
-   Once your TV is rooted, run the following to download the Magic Mapper scripts (or just vi the files and copy and paste, or just use scp on the C9/CX, but the C2 doesn't support scp).
```
cd /home/root
wget https://raw.githubusercontent.com/andrewfraley/magic_mapper/main/magic_mapper.py
wget https://raw.githubusercontent.com/andrewfraley/magic_mapper/main/magic_mapper_config.json
cd /var/lib/webosbrew/init.d
wget https://raw.githubusercontent.com/andrewfraley/magic_mapper/main/start_magic_mapper
chmod +x /var/lib/webosbrew/init.d/start_magic_mapper
```
- Edit magic_mapper_config.json as needed
-   Lastly, reboot the TV (recommended to use the HomeBrew app to reboot to avoid crash detection issues, launch HomeBrew app, click cog, click reboot link on bottom left.)

## Configuring buttons

Buttons are configured via the magic_mapper_config.json file. magic_mapper_config.json contains a json formatted dictionary where each primary key is the name of the button to map (see the Button List below). Note that changes to magic_mapper_config.json require you to restart the script, so just reboot your TV or if testing over SSH, kill the magic_mapper.py process and run the script manually. To reboot your TV, it's recommended that you use the Home Brew app to do it to avoid Home Brew errors (the script won't start if Home Brew crash detection kicks in). To reboot with Home Brew, open the Home Brew app, click the cog icon, then click the reboot link on the bottom left.

```
"yellow": {  # The name of the button to remap, see the Button List below
  "function": "cycle_energy_mode",   # The matching function to execute in magic_mapper.py - see Function List below
  "inputs": {                        # The input dict to send to the function, different functions use different inputs, see the Function List below
    "reverse_order": false,
    "notifications": true
  }
}
```

## Overriding App Buttons

If you want to remap the app buttons, you must first uninstall the app you don't use (otherwise pressing the button will still launch that app, even with this script running). For example, if you wanted to replace the Amazon Prime button with Plex:

-   Uninstall the Prime app.
-   Get the Plex app id by copying the included list_apps.py script to the TV.
    - ```wget https://raw.githubusercontent.com/andrewfraley/magic_mapper/main/list_apps.py```
    - Run it with:
        -   (C9/CX): `python list_apps.py`
        -   (C1/C2+): `python3 list_apps.py`
    -   This will list the app names followed by their app ID such as `Plex : cdp-30`, cdp-30 is the app id for Plex.
-   Edit the magic_mapper_config.json file and add a new item like:

```
  "prime": {
    "function": "launch_app",
    "inputs": {
      "app_id": "cdp-30"
    }
  }
```

-   Now when you press the Prime button, Plex will launch instead.

## Function List

### cycle_energy_mode

-   Cycles through each energy savings mode (minimum, medium, maximum, off)
-   Inputs:
    -   **reverse_order** (boolean, default: false): Reverse the cycle order of the modes
    -   **notifications** (boolean, default: false): Show a toast notification on mode change (Note the warning about energy consumption cannot be disabled)
-   Example:
    ```
    "yellow": {
      "function": "cycle_energy_mode",
      "inputs": {
        "reverse_order": false,
        "notifications": true
      }
    }
    ```

### toggle_eye_comfort

-   Toggles the Eye Comfort Mode on and off, also known as Reduce Blue Light depending on menu.
-   Inputs:
    -   **notifications** (boolean, default: false): Show a toast notification on change
-   Example:
    ```
    "blue": {
      "function": "toggle_eye_comfort",
      "inputs": {
        "notifications": false
      }
    }
    ```

### reduce_oled_light / increase_oled_light

-   Increases / decreases the oled light setting
-   Inputs:
    -   **increment** (integer, default: 10): The amount to change the setting by
-   Example:
    ```
    "red": {
      "function": "reduce_oled_light",
      "inputs": {
        "increment": 10
      }
    }
    ```

### set_energy_mode

-   Set a specific energy savings mode
    - note "screen_off" activates the screen off setting which turns off the screen until you push a button other than the power button.
-   Inputs:
    -   **mode** (string, default: none, values: "off", "min", "med", "max", "auto", "screen_off")
    -   **notifications** (boolean, default: false): Show a toast notification on change
-   Example:
    ```
    "green": {
      "function": "set_energy_mode",
      "inputs": {
        "mode": "auto",
        "notifications": true
      }
    }
    ```

### set_oled_light

-   Set the OLED backlight to a specific value
-   Inputs:
    -   **backlight** (integer, default: none, values: 0-100): The backlight value to set
    -   **notifications** (boolean, default: false): Show a toast notification on change
-   Example:
    ```
    "3": {
      "function": "set_oled_backlight",
      "inputs": {
        "backlight": 50,
        "notifications": true
      }
    }
    ```

### launch_app

-   Launch an app (See the Overriding App Buttons section Above to use on an app button, example here is for normal buttons)
-   Inputs:
    -   **app_id** (string, default: none): The app id to launch. To get a list of all app IDs, copy the included list_apps.py script to the TV and run it (`python list_apps.py` on C9/CX, `python3 list_apps.py` on C1/C2+)
-   Example:
    ```
    "1": {
      "function": "launch_app",
      "inputs": {
        "app_id": "netflix"
      }
    }
    ```
### send_ir_command
- Send an IR command to a device configured by the TV's Device Connector
- Inputs:
    - tv_input (string, default: none): The input the device is on, ie "optical" or "hdmi3" (TODO: full list unknown)
    - keycode (string, default: none): The IR keycode to send "IR_KEY_VOLUP", "IR_KEY_POWER" (TODO: full list unknown)
    - device_type (string, default: none) ie "audio" (TODO: full list unknown)
- Example:
  ```
  "0": {
    "function": "send_ir_command",
    "inputs": {
      "tv_input": "optical",
      "keycode": "IR_KEY_POWER",
      "device_type": "audio"
    }
  },
  ```

## Button List

List of known buttons and their codes. Not all remote buttons are on this list, but the missing ones are likely buttons where the default behavior can't be disabled. If needed, you can modify magic_mapper.py to add other button codes. Just run magic_mapper.py manually and it will list all button codes it sees.

Note that long presses (longer than 1s) are ignored. I will eventually add support for different actions based on short vs long press.

```
 "red"
 "green"
 "yellow"
 "blue"
 "ch_up"
 "ch_down"
 "play"
 "pause"
 "1"
 "2"
 "3"
 "4"
 "5"
 "6"
 "7"
 "8"
 "9"
 "0"
 "prime"
 "netflix"
 "disney"
 "lg_channels"
 "alexa"
 "google"
```

## Help!

If you need assistance, please open an issue on Github here: https://github.com/andrewfraley/magic_mapper/issues

You can view all issues (closed and still open) here: https://github.com/andrewfraley/magic_mapper/issues?q=is%3Aissue

## Modifying the script

The script is currently setup to detect the button presses of the commonly unused buttons. Namely the 0-9 buttons and the color buttons. You can remap other buttons, but be aware this script does not prevent the actions a button normally takes. For example, you could override the channel +/- buttons, but some internal apps use these buttons. So if you press one, it will execute the default behavior in addition to the remapped behavior via this script.

The function names supplied in magic_mapper_config.json map to the function names in the script. If you wanted to have the yellow button do something unsupported by this script, create a new function in magic_mapper.py and then add the function to magic_mapper_config.json such as:

```
"yellow": {
  "function": "your_new_function_name"
  "inputs": {
    "variable_passed_to_function": "value_for_variable",
    "another_variable": "value_for_var"
  }
}
```

There are some various examples of the luna-send endpoints and payloads here (scroll down a bit): https://gist.github.com/Ircama/1f29c2d2def75da6604756a3c91a8ab4

For documentation on each endpoint, see the WebOS developer docs: https://www.webosose.org/docs/reference/ls2-api/ls2-api-index/

If you add new novel functionality that others might make use of, please submit a PR!

## Donations

If you love this project and want to donate to support it, donate your money somewhere else! If you don't have a charity in mind, food banks are always in dire need of your support, consider donating to your local regional food bank.
