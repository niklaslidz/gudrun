#!/usr/bin/env python
from __future__ import print_function
from subprocess import check_output


def all_device_paths():
    devices = [
        l.split('#')
        for l in check_output(
            'rosrun gudrun_sensors list_usb_devices.sh'.split()
        ).split('\n')
        if len(l.strip()) > 0
    ]
    full_devices_map = {}
    for row in devices:
        path, serial_id = row
        sid = serial_id.strip()
        if sid not in full_devices_map:
            full_devices_map[sid] = []
        full_devices_map[sid].append(path.strip()) 

    return full_devices_map

def preferred_device_paths():

    full_devices_map = all_device_paths()

    def priority(path):
        """Choose the *best* path.

        Some devices (like a virgin unflashed Pro Micro) have multiple paths
        associated with them, and the last to be listed is not necessarily
        the one they'll respond to when flashing.
        """
        out = 0
        good = 'USB', 'ACM'
        bad = 'input', 'mouse', 'event', '/dev/sd'
        for g in good:
            if g in path:
                out -= 1
        for b in bad:
            if b in path:
                out += 1
        return out
        
    devices_map = {
        sid: sorted(paths, key=priority)[0]
        for (sid, paths) in full_devices_map.items()
    }

    friendly_names = dict(
        ultrasound_uno='1a86_USB2.0-Serial',
        encoder_mega='Arduino__www.arduino.cc__0042_7543933363535110C102',
        encoder_micro='Arduino_LLC_Arduino_Leonardo', # I can see this becoming a problem if I want to use more than one of these chips.
        servo_maestro='Pololu_Corporation_Pololu_Micro_Maestro_6-Servo_Controller_00203742',
    )
    for k, v in friendly_names.items():
        if v in devices_map:
            devices_map[k] = devices_map[v]

    return devices_map


def device_path(device_id):
    return preferred_device_paths().get(device_id, 'device_not_found')


def main():
    from sys import argv

    if len(argv) < 2:
        full_devices_map = all_device_paths()
        from pprint import pprint
        pprint(full_devices_map)

    else:
        print(device_path(argv[1]))


if __name__ == '__main__':
    main()
