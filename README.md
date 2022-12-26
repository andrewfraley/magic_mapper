# Magic Mapper

## Summary
Magic Mapper is a script that will let you remap unused buttons on the LG Magic Remote.  The script itself runs on your rooted LG TV, detects button presses, and allows you to control anything available via the [luna-send api](https://www.webosose.org/docs/tools/commands/luna-send/).

## Examples
The script has examples that by default allow the following:
- Red button: decrease the OLED light
- Green button: increase the OLED light
- Yellow button: Cycle the energy savings modes
- Blue: Toggle the Eye Comfort Mode (also known as Reduce Blue Light)

## TV Models supported
- LG C9 - Fully tested
- LG CX - Not tested, but should work.  Likely needs the C9 startup script.
- LG CX - Not tested, but should work.  Likely needs the C2 startup script.
- LG C2 - Fully tested

## Installation / Setup

- Root your TV using https://rootmy.tv/
  - Note the above link is likely to fail on the newest firmware.
  - Instead, follow this guide (C2 has issues, see next bullet): https://github.com/RootMyTV/RootMyTV.github.io/issues/85#issuecomment-1295058979
  - The above instructions work fine for a C9, but a C2 requires additional steps for SSH to work, [outlined here](https://github.com/RootMyTV/RootMyTV.github.io/issues/85#issuecomment-1364765232):
- Once your TV is rooted, copy the scripts over (or just vi the files and copy and paste).
  - start_mapper should be placed at /var/lib/webosbrew/init.d/start_magic_mapper
  - magic_mapper.py should be placed at /home/root/magic_mapper.py
```
scp start_magic_mapper-c2 root@yourtvIP:/var/lib/webosbrew/init.d/start_magic_mapper
scp magic_mapper.py:/home/root/
```

## Configuring buttons

Buttons are configured via the magic_mapper_config.json file.  magic_mapper_config.json contains a json formatted dictionary where each primary key is the name of the button to map (see the Button List below).

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

If you want to remap the app buttons, you must first uninstall the app you don't use (otherwise pressing the button will still launch that app, even with this script running).  For example, if you wanted to replace the Amazon Prime button with Plex:

- Uninstall the Prime app.
- Get the Plex app id.  Copy the included list_apps.py script to the TV and run it with:
  - (C9/CX): ```python list_apps.py```
  - (C1/C2+): ```python3 list_apps.py```
  - This will list the app names followed by their app ID such as ```Plex : cdp-30```, cdp-30 is the app id for Plex.
- Edit the magic_mapper_config.json file and add a new item like:
```
  "prime": {
    "function": "launch_app",
    "inputs": {
      "app_id": "cdp-30"
    }
  }
```
- Now when you press the Prime button, Plex will launch instead.

## Function List

### cycle_energy_mode

- Cycles through each energy savings mode (minimum, medium, maximum, off)
- Inputs:
  - **reverse_order** (boolean, default: false): Reverse the cycle order of the modes
  - **notifications** (boolean, default: false): Show a toast notification on mode change (Note the warning about energy consumption cannot be disabled)
- Example:
    ```
    "yellow": {
      "function": "cycle_energy_mode",
      "inputs": {
        "reverse_order": false,
        "notifications": true
      }
    },
    ```

### toggle_eye_comfort

- Toggles the Eye Comfort Mode on and off, also known as Reduce Blue Light depending on menu.
- Inputs:
  - **notifications** (boolean, default: false): Show a toast notification on change
- Example:
  ```
  "blue": {
    "function": "toggle_eye_comfort",
    "inputs": {
      "notifications": false
    }
  },
  ```

### reduce_oled_light / increase_oled_light
- Increases / decreases the oled light setting
- Inputs:
  - **backlight_increment** (integer, default: 10): The amount to change the setting by
- Example:
  ```
  "red": {
    "function": "reduce_oled_light",
    "inputs": {
      "backlight_increment": 10
    }
  },
  ```

### launch_app
- Launch an app (See the Overriding App Buttons section Above to use on an app button, example here is for normal buttons)
- Inputs:
  - **app_id** (string, default: none): The app id to launch.  To get a list of all app IDs, copy the included list_apps.py script to the TV and run it (```python list_apps.py``` on C9/CX, ```python3 list_apps.py``` on C1/C2+)
- Example:
  ```
  "red": {
    "function": "launch_app",
    "inputs": {
      "app_id": "netflix"
    }
  }
  ```

## Button List

List of known buttons and their codes.  Not all remote buttons are on this list, but the missing ones are likely buttons where the default behavior can't be disabled.  If needed, you can modify magic_mapper.py to add other button codes.  Just run magic_mapper.py manually and it will list all button codes it sees.

```
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
```

## Modifying the script

The script is currently setup to detect the button presses of the commonly unused buttons.  Namely the 0-9 buttons and the color buttons.  You can remap other buttons, but be aware this script does not prevent the actions a button normally takes.  For example, you could override the channel +/- buttons, but some internal apps use these buttons.  So if you press one, it will execute the default behavior in addition to the remapped behavior via this script.

The function names supplied in magic_mapper_config.json map to the function names in the script.  If you wanted to have the yellow button do something unsupported by this script, create a new function in magic_mapper.py and then add the function to magic_mapper_config.json such as:

```
"yellow": {
  "function": "your_new_function_name"
  "inputs": {
    "variable_passed_to_function": "value_for_variable",
    "another_variable": "value_for_var"
  }
}
```

If you add new novel functionality that others might make use of, please submit a PR!

There are some various examples of the luna-send endpoints and payloads here (scroll down a bit):  https://gist.github.com/Ircama/1f29c2d2def75da6604756a3c91a8ab4

For documentation on each endpoint, see the WebOS developer docs: https://www.webosose.org/docs/reference/ls2-api/ls2-api-index/


SETTINGS = {
    "show_notifications": True,  # Will present "toast" notification dialogs on some settings changes like eye comfort and energy mode
    "backlight_increment": 10,  # For each button press, how much to raise or lower the brightness
    "input_device": ,  # You shouldn't need to change this unless newer hardware in the future moves the input device used for the remote
}

FUNCTION_MAP = {
    "yellow": "cycle_energy_mode",  # cycles the energy savings modes
    "blue": "toggle_eye_comfort",  # aka reduce blue light
    "red": "reduce_oled_light",
    "green": "increase_oled_light",
}
