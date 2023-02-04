import os
import fcntl
import struct

EVIOCGRAB = 1074021776

input_format = "llHHI"
event_size = struct.calcsize(input_format)

# Device file path
device_file = '/dev/input/event3'

# Codes to filter out
filter_codes = [1037]

# Open the device file in exclusive mode
input_device = open(device_file, 'rb')

# Acquire exclusive control of the device
fcntl.ioctl(input_device, EVIOCGRAB, 1)

# open the output device
uinput_file = os.open("/dev/input/event4", os.O_WRONLY)


while True:
    # Read input from the device
    event = input_device.read(event_size)
    (tv_sec, tv_usec, type, code, value) = struct.unpack(input_format, event)

    # Check if the code should be filtered
    if code not in filter_codes:
        print('Unfiltered: %s' % code)
        os.write(uinput_file, event)
    else:
        print('Filtered: %s' % code)
