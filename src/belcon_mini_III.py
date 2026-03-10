#!/usr/bin/env python3

import time

from serial.tools import list_ports
from pymodbus.client.sync import ModbusSerialClient as ModbusClient


# --- Modbus Register Addresses ---
REG_STATUS          = 8    # R: Device status (16-bit flags)
REG_SET_MODE        = 9    # R/W: Operation mode
REG_FREQ_RAM        = 13   # R/W: Target frequency (RAM)
REG_FREQ_EEPROM     = 14   # W: Target frequency (EEPROM)
REG_ACTUAL_FREQ     = 200  # R: Realtime output frequency
REG_SET_FREQ        = 204  # R: Set frequency
REG_PARAM_BASE      = 1000 # R: Parameter base address (param N -> 1000+N)

# --- Operation Mode Values (REG_SET_MODE) ---
MODE_EXT     = 0
MODE_PU      = 1
MODE_EXT_JOG = 2
MODE_NET     = 4
MODE_PU_EXT  = 5
MODE_NET_SET = 6  # Written to activate NET mode

MODE_LABELS = {
    MODE_EXT:     "EXT",
    MODE_PU:      "PU",
    MODE_EXT_JOG: "EXT JOG",
    MODE_NET:     "NET",
    MODE_PU_EXT:  "PU+ EXT",
}

# --- Direction / Speed Control Values (REG_STATUS write) ---
DIR_NORMAL  = 2   # Normal rotation flag
DIR_REVERSE = 4   # Reverse rotation flag

SPEED_LOW    = 32
SPEED_MIDDLE = 16
SPEED_HIGH   = 8

SPEED_LABELS = {
    'low':    SPEED_LOW,
    'middle': SPEED_MIDDLE,
    'high':   SPEED_HIGH,
}

# --- Slave / Modbus Config ---
UNIT_ID   = 1
MAX_FREQ_HZ = 40000


class DMH():

    def __init__(self, usbport):
        if usbport is None:
            usbport = self.select_port()
        self.client = ModbusClient(
            method="rtu",
            port=usbport,
            stopbits=1,
            bytesize=8,
            parity='E',
            baudrate=19200,
            timeout=3,
            strict=False)
        self._max_freq_hz = MAX_FREQ_HZ
        self.open_connection()

    def open_connection(self):
        """Opens the connection with a conveyor."""
        self.client.connect()

    def close_connection(self):
        """Closes the connection with the conveyor."""
        self.client.close()

    def select_port(self):
        """Selects a port interactively if multiple ports are available."""
        ports = list_ports.comports()
        devices = [info.device for info in ports]

        if len(devices) == 0:
            print("Error: no devices found")
            return None
        elif len(devices) == 1:
            print("%s is the only port found." % devices[0])
            return devices[0]
        else:
            for i, dev in enumerate(devices):
                print("input %3d: open %s" % (i, dev))
            print("input number of target port >> ", end="")
            num = int(input())
            return devices[num]

    def get_status(self):
        """Reads current device status.
        This status field indicates the status of the conveyor and its motion.
        It is composed of 16 flags, described in the table below.
        Bit      Name                  Description
        0 (LSB): RUN                   1 when the inverter is in operation.
        1:       normal                1 when it is driven by normal rotation.
        2:       reverse               1 when it is driven by reverse rotation.
        3:       SU (reach freq)       1 when it reached target frequency.
        4:       OL (overload)         1 when it detects overload.
        5:       reserved              Not used. Always 0.
        6:       FU (detect freq)      1 when it detects frequency of Pr.42/43.
        7:       ABC (abnormal)        1 when it detects abnormal state.
        8:       reserved              Not used. Always 0.
        9:       SO (safety monitor)   1 when the safety stop is in operation.
        10 - 14: reserved              Not used. Always 0.
        15:      Abnormal occurrence   1 when an abnormal state is detected.
        """
        result = self.client.read_holding_registers(
            address=REG_STATUS, count=1, unit=UNIT_ID)
        status = format(result.registers[0], '016b')
        status_list = [0] * 16
        if int(status[-1]):
            print("RUN (in operation).")
            status_list[0] = 1
        if int(status[-2]):
            print("Normal rotation.")
            status_list[1] = 1
        if int(status[-3]):
            print("Reverse rotation.")
            status_list[2] = 1
        if int(status[-4]):
            print("Reached target frequency.")
            status_list[3] = 1
        if int(status[-5]):
            print("Overload was detected.")
            status_list[4] = 1
        if int(status[-7]):
            print("Overed frequency threshold (Pr. 42/43).")
            status_list[6] = 1
        if int(status[-8]):
            print("Abnormal state was detected.")
            status_list[7] = 1
        if int(status[-10]):
            print("Safety stop is in operation.")
            status_list[9] = 1
        if int(status[0]):
            print("Abnormal occurrence.")
            status_list[15] = 1

        return status_list

    def get_set_mode(self):
        """Reads current device set mode.
        0: EXT
        1: PU
        2: EXT JOG
        4: NET
        5: PU+ EXT
        """
        result = self.client.read_holding_registers(
            address=REG_SET_MODE, count=1, unit=UNIT_ID)
        mode_label = result.registers[0]
        mode_str = MODE_LABELS.get(int(mode_label), "UNKNOWN(%d)" % mode_label)
        print("Current set mode: " + mode_str)

        return mode_label

    def get_set_parameters(self, pnum):
        """Reads parameters set on the inverter controller.
        Register address = REG_PARAM_BASE + pnum.
        Note: pnum is 0-indexed offset from REG_PARAM_BASE, not the Pr. number.
        """
        result = self.client.read_holding_registers(
            address=REG_PARAM_BASE + pnum, count=1, unit=UNIT_ID)
        return result.registers[0]

    def stop(self):
        """Stops operations."""
        self.client.write_registers(
            address=REG_STATUS, values=[0], unit=UNIT_ID)

    def move(self, direction='normal', speed='low'):
        """Executes normal/reverse rotations with target speed.

        Args:
            direction: 'normal' or 'reverse'
            speed: 'low', 'middle', 'high', or an integer frequency in Hz/100
        """
        if direction == 'normal':
            set_value = DIR_NORMAL
        elif direction == 'reverse':
            set_value = DIR_REVERSE
        else:
            print("Select one from normal or reverse for direction.")
            return

        if speed in SPEED_LABELS:
            speed_val = SPEED_LABELS[speed]
        else:
            speed_val = 0
            try:
                self.set_frequency_on_RAM(
                    min(self._max_freq_hz, int(speed)))
            except ValueError:
                print("Select low/middle/high or input frequency.")
                return

        self.client.write_registers(
            address=REG_STATUS, values=[set_value + speed_val], unit=UNIT_ID)

    def set_net_mode(self):
        """Sets inverter operation mode as NET mode."""
        self.client.write_registers(
            address=REG_SET_MODE, values=[MODE_NET_SET], unit=UNIT_ID)

    def get_actual_frequency(self):
        """Gets realtime output frequency [Hz/100]."""
        result = self.client.read_holding_registers(
            address=REG_ACTUAL_FREQ, count=1, unit=UNIT_ID)
        return result.registers[0]

    def get_set_frequency(self):
        """Gets set frequency [Hz/100]."""
        result = self.client.read_holding_registers(
            address=REG_SET_FREQ, count=1, unit=UNIT_ID)
        return result.registers[0]

    def get_frequency_from_RAM(self):
        """Gets target frequency from RAM [Hz/100]."""
        result = self.client.read_holding_registers(
            address=REG_FREQ_RAM, count=1, unit=UNIT_ID)
        return result.registers[0]

    def set_frequency_on_RAM(self, freq):
        """Sets target frequency on RAM [Hz/100]."""
        self.client.write_registers(
            address=REG_FREQ_RAM, values=[freq], unit=UNIT_ID)

    def set_frequency_on_EEPROM(self, freq):
        """Sets target frequency on EEPROM [Hz/100].

        Note: Writes to EEPROM are persistent but have limited write cycles.
        Prefer set_frequency_on_RAM() for frequent updates.
        """
        self.client.write_registers(
            address=REG_FREQ_EEPROM, values=[freq], unit=UNIT_ID)

    def sleep_with_displaying_freq(self, sleep_sec):
        """Sleeps for sleep_sec seconds while displaying current frequency."""
        start = time.time()
        while True:
            time.sleep(0.1)
            print("Frequency: %s / %s [Hz/100]" % (
                self.get_actual_frequency(),
                self.get_set_frequency()))
            if (time.time() - start) > sleep_sec:
                break
