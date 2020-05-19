#!/usr/bin/python3

import serial
from datetime import datetime

import sys
import os
import termios
import fcntl
import tty

# Change the input mode so that we can check for keyboard input without
# pausing the program. (This also disables echoing of keystrokes to the
# console.)
class nonblocking_stdin:
    def __enter__(self):
        self.original_attr = termios.tcgetattr(sys.stdin)
        self.original_flow = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)

        tty.setcbreak(sys.stdin)
        fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, self.original_flow |
                os.O_NONBLOCK)

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(sys.stdin, termios.TCSANOW, self.original_attr)
        fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, self.original_flow)

def main():
    ser = serial.Serial('/dev/ttyACM0', 115200)

    commandline = ""
    valvetime_ms = 1000 # ms
    pressures_Pa = [0] * 20 # list of the most recent pressure measurements

    with nonblocking_stdin():
        while True:

            # fetch a line data from the Arduino and extract the individual
            # measurements (aborting if there are any problems parsing the
            # data)

            rawline = ser.readline()
            try:
                line = rawline.decode('utf-8').strip()
                if line == '':
                    continue
                vals = [0 if '' == val else int(val) for val in
                        line.split(',')]
                if len(vals) != 2:
                    continue
            except:
                continue

            pressure,temperature = vals

            # Convert pressure to standard units

            # constants from ABP datasheet and Honeywell technical note on SPI
            # communication with Honeywell digital output pressure sensors
            pressure_output_min = 0x0666
            pressure_output_max = 0x399A
            pressure_max = 60000
            pressure_min = 0
            pressure_Pa = (pressure - pressure_output_min) / (
                pressure_output_max - pressure_output_min) * (
                pressure_max - pressure_min) + pressure_min

            # add it to the list of recent pressures (replacing the oldest
            # value) and calculate the mean of recent pressure measurements
            pressures_Pa = pressures_Pa[1:] + [pressure_Pa]
            mean_pressure_Pa = sum(pressures_Pa)/len(pressures_Pa)

            # if a key has been pressed...
            keyboard_input = sys.stdin.read(1)
            if keyboard_input:
                # if a number key has been pressed, record the digit (up to a
                # max of 4 digits).
                if keyboard_input[0] >= '0' and keyboard_input[0] <= '9':
                    if len(commandline) < 4: # no need for more than 9999 ms
                        commandline += keyboard_input
                # if enter has been pressed, parse the digits (if present) as
                # the new valve open time (otherwise keep the current value),
                # and then send the valve-open time to the Arduino to actuate
                # the valve.
                elif keyboard_input[0] == '\n':
                    if len(commandline) > 0:
                        valvetime_ms = int(commandline)
                    ser.write(f'{valvetime_ms}\n'.encode())
                    commandline = ''
                    print('\r' + ' '*100, end='') # erase the line
                # If backspace was pressed, delete the most recent input
                elif keyboard_input[0] == '\x7F': # backspace
                    if len(commandline) > 0:
                        commandline = commandline[0:-1]
                    print('\r' + ' '*100, end='') # erase the line
                # If ctrl-D, x, or q is pressed, then quit.
                elif (keyboard_input[0] == '\x04' or keyboard_input[0] == 'q'
                        or keyboard_input == 'x'):
                    break # quit

            # print the most recent pressure and the command prompt so far
            print(#f'{datetime.utcnow().isoformat()}Z'+
                f'\rPressure: {mean_pressure_Pa:7.0f} Pa ' +
                f'Current Valve Open Time: {valvetime_ms:6} ms ' +
                f'New Valve Open Time: {commandline}',
                end=''
                )

        print('\nExiting...')

if __name__ == '__main__':
    main()
