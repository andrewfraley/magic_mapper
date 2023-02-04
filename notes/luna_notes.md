# Luna Notes

Helpful luna-send one liners

### Get information about valid values for settings
https://www.webosose.org/docs/reference/ls2-api/com-webos-service-settings/#getsystemsettingvalues

```luna-send -n 1 luna://com.webos.service.settings/getSystemSettingValues '{"category":"picture", "key":"brightness"}' -f```

### Get info about available functions per endpoint
``` ls-monitor -i  com.webos.service.irdbmanager ```

### Monitor the luna bus for activity
``` ls-monitor ```

### Send IR power on command
```
luna-send -n 1 luna://com.webos.service.irdbmanager/sendIrCommand -f '{"keyCode":"IR_KEY_POWER","buttonState
":"single","connectedInput":"OPTICAL","deviceType":"audio"}'
```

### How I found the IR commands
- ls-monitor to debug the bus
- noted com.webos.service.irdbmanager calls
- Filter ls-monitor ```ls-monitor -f com.webos.service.irdbmanager```
- Note calls with payloads

```
26316.097 TX  call      710             com.webos.audio (cuJ2GiHl)      com.webos.service.irdbmanager (ABMetG7S) (null) //sendIrCommand  {"keyCode":"IR_KEY_VOLUP","buttonState":"single","connectedInput":"OPTICAL","deviceType":"audio"}
```

- Test payload
```
luna-send -n 1 luna://com.webos.service.irdbmanager/sendIrCommand -f '{"keyCode":"IR_KEY_VOLUP","buttonState
":"single","connectedInput":"OPTICAL","deviceType":"audio"}'
```

### Get possible IR code values
```
luna-send -n 1 luna://com.webos.service.irdbmanager/getKeyList -f '{"deviceType":"audio"}' | grep IR
```
