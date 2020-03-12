import time
import sys

# pyserial
import serial
import serial.tools.list_ports as list_ports

# midi related
import mido

# Serial port parameters
SERIAL_SPEED = 9600
SERIAL_PORT = "/dev/cu.E-nstrument-ESP32SPP"
# Midi virtual port
MIDI_PORT = "IAC Driver Bus 1"

# global var to safely exit the loop when program is ctr+c by user
close_serial_connection = False
# this is used to print a helpful message when everything is going right, so you can start waving the e-instrument
successfully_receiving_accelerometer_data = False

# This new data format is used to simplify converting serial data to useful accelerometer data
# accelerometer_data = [ax,ay,az,t,gx,gy,gz]
accelerometer_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


# Open the midi port
midi_port = mido.open_output(MIDI_PORT)


# Helper function to ensure bluetooth serial port is valid
def check_if_valid_serial_port(port_name):
    myports = [tuple(p)[0] for p in list(list_ports.comports())]
    if port_name not in myports:
        print(f"{port_name} is not a valid serial port")
        print("Available serial ports:")
        for serial_port in myports:
            print(serial_port)
        return False
    else:
        print(f"{port_name} is a Valid serial port!")
        return True


# Function to parse serial data from bytes to accelerometer data and update the global variable
def parse_serial(data):
    global accelerometer_data
    # convert from bytes to a string
    strdata = str(data)
    try:
        # removes last 6 chars (\\r\\n') and then splits wherever their is a ';'  followed by removing first element of the list after split which is 'b'
        parsed_string_list = strdata[:-6].split(";")[1:]
        if len(parsed_string_list) == 7:
            # convert string list to float list
            accelerometer_data = [float(i) for i in parsed_string_list]
            # print this data
            # print(accelerometer_data)
            # Now play midi based on these values
            parse_accel_play_midi(accelerometer_data)
    except Exception as e:
        print(f"Exception while parsing serial ble data {e}")


# Function to play midi note given accelerometer data
# accelerometer_data = [ax,ay,az,t,gx,gy,gz]
def parse_accel_play_midi(accelerometer_data):
    # destructure list
    ax, ay, az, t, gx, gy, gz = accelerometer_data
    # Build a better algorithm to parse the data to produce midi notes since this currently only uses gx values
    if gx < -2:
        gx = gx / 1.1
        round_note = abs(round(gx))
        # Since midi notes are between 0 -127
        if round_note > 127:
            round_note = 127
        midinote = mido.Message("note_on", note=round_note, time=0.01)
        print(f"Playing: {midinote}")
        midi_port.send(midinote)


# Watch serial data
def serial_monitor():
    global close_serial_connection
    global successfully_receiving_accelerometer_data

    valid = check_if_valid_serial_port(SERIAL_PORT)
    if valid:
        # print details
        print(f"Trying to connect to serial port ... {SERIAL_PORT}")

        try:
            # Connect to the serial port
            ser = serial.Serial(SERIAL_PORT, SERIAL_SPEED, timeout=2)

        except Exception as e:
            print(f"Problem connecting to bluetooth serial port: {e}")
            sys.exit()

        # if connected
        if ser.is_open:

            print("Connected to serial port, waiting to receive messages: ")
            # while connected
            while not close_serial_connection:
                try:
                    data = ser.readline()
                    if data == [] or len(data) == 0:
                        print(f"Received: {data}")
                        print(
                            "Ble serial not receiving data! Please try to reboot your e-instrument or try to re-connect to it!"
                        )
                        close_serial_connection = True
                    else:
                        if not (successfully_receiving_accelerometer_data):
                            print("Receiving accelerometer data! You can start waving your e-instrument to produce midi notes!")
                            successfully_receiving_accelerometer_data = True

                        parse_serial(data)
                    time.sleep(0.01)
                # If user ctr+c, close the serial port to avoid multiple open ports in the future during program shutdown
                except KeyboardInterrupt:
                    ser.close()
                    close_serial_connection = True
                    sys.exit()


serial_monitor()
