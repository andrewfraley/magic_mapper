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

## Modifying the script

The script is currently setup to detect the button presses of the commonly unused buttons.  Namely the 0-9 buttons and the color buttons.  You can remap other buttons, but be aware this script does not prevent the actions a button normally takes.  For example, you could override the channel +/- buttons, but some internal apps use these buttons.  So if you press one, it will execute the default behavior in addition to the remapped behavior via this script.

To change a button, edit the FUNCTION_MAP dict and replace your button and function name.  The function names map to functions in the script.  If you wanted to have the yellow button do something different, create a new function and then edit FUNCTION_MAP such as:

```
"yellow": "your_new_function",
```

If you add new novel functionality that others might make use of, please submit a PR!

There are some various examples of the luna-send endpoints and payloads here (scroll down a bit):  https://gist.github.com/Ircama/1f29c2d2def75da6604756a3c91a8ab4

For documentation on each endpoint, see the WebOS developer docs: https://www.webosose.org/docs/reference/ls2-api/ls2-api-index/
