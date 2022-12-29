import struct
import os
import time


def send_keystroke(device, keycode):
    """ Send a keystroke to the input device
        We use this to simulate button presses like play/pause since those require special handling
        Don't try to call this from magic_mapper_config.json


    struct input_event {
        struct timeval time;
        unsigned short type;
        unsigned short code;
        unsigned int value;
    };
    """
    send_event(device, keycode, 1, 1)
    send_event(device, 0, 0, 0)
    send_event(device, keycode, 0, 1)
    send_event(device, 0, 0, 0)


def send_event(device, keycode, value, event_type):
    input_format = "llHHI"

    out_file = os.open(device, os.O_RDWR)
    now = time.time()
    tv_sec = int(now)
    tv_usec = int((now - tv_sec) * 1000000)

    data = [tv_sec, tv_usec, event_type, keycode, value]
    print("writing: %s" % data)

    event = struct.pack(input_format, *data)
    os.write(out_file, event)
    os.close(out_file)


if __name__ == "__main__":
    send_keystroke(device="/dev/input/event3", keycode=2)


# https://www.linuxquestions.org/questions/programming-9/injecting-key-strokes-to-simulate-a-keyboard-4175471334/
