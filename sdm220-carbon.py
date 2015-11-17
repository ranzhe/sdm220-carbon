#!/usr/bin/env python

import sys
import os
import time
import getopt
import socket
import ConfigParser

import struct
import pymodbus.client.sync
import binascii

DELAY = 15

def print_help():
    print 'Usage: sdm220-carbon.py -c sdm220-carbon.ini'
    print 'If no config file provided with -c argument, i`ll try to open one at the script path'
    sys.exit(0)

def parse_config(configfile):
    options_dict = {}

    Config = ConfigParser.ConfigParser()

    try:
        Config.read(configfile)
    except:
        print "Unable to open configuration file: %s" %configfile
        sys.exit(1)

    options = Config.options('Settings')
    for option in options:
        options_dict[option] = Config.get('Settings', option)

    return options_dict


def read_float_reg(client, basereg, unit) :
    resp = client.read_input_registers(basereg,2, unit=unit)
    if resp == None :
        return None

    return struct.unpack('>f',struct.pack('>HH',*resp.registers))

def fmt_or_dummy(regfmt, val) :
    if val is None :
        return '.'*len(regfmt%(0))

    return regfmt%(val)


def get_meter_vals(regs, options):


    # if client is set to odd or even parity, set stopbits to 1
    # if client is set to 'none' parity, set stopbits to 2

    client = pymodbus.client.sync.ModbusSerialClient('rtu', port=options['port'], baudrate=int(options['baudrate']), parity=options['parity'],stopbits=int(options['stopbits']), timeout=0.125)

    values = []

    for reg in regs:
        regval = []
        regval.append(reg[0])
        regval.append(fmt_or_dummy(reg[2], read_float_reg(client, reg[1], unit=int(options['slave_id']))))

        values.append(regval)

    return values


def send_msg(message, options):
    print 'sending message to %s:%s:\n%s' % (options['carbon_server'], options['carbon_port'], message)
    sock = socket.socket()
    sock.connect((options['carbon_server'], int(options['carbon_port'])))
    sock.sendall(message)
    sock.close()


if __name__ == '__main__':
    regs = [
        # Symbol    Reg#  Format
        ( 'V',      0x00, '%6.2f' ), # Voltage [V]
        ( 'Curr',   0x06, '%6.2f' ), # Current [A]
        ( 'Pact', 0x0c, '%6.0f' ), # Active Power ("Wirkleistung") [W]
        ( 'Papp', 0x12, '%6.0f' ), # Apparent Power ("Scheinl.") [W]
        ( 'Prea', 0x18, '%6.0f' ), # Reactive Power ("Blindl.") [W]
        ( 'PF',     0x1e, '%6.3f' ), # Power Factor   [1]
        ( 'Phi',    0x24, '%6.1f' ), # cos(Phi)?      [1]
        ( 'Freq',   0x46, '%6.2f' )  # Line Frequency [Hz]
    ]

    argv = sys.argv[1:]

    configfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sdm220-carbon.ini')

    try:
        opts, args = getopt.getopt(argv, "hc:", ["configfile"])
    except:
        print_help()
        sys.exit(1)

    for opt,arg in opts:
        if opt in ('-h', '--help'):
            print_help()
        elif opt == '-c':
            configfile = arg

    options = parse_config(configfile)

    while True:
        lines = []
        timestamp = int(time.time())
        meter_vals = get_meter_vals(regs, options)

        for meter_val in meter_vals:
            line = str('%s.%s %s %d' % (options['carbon_metric_prefix'], meter_val[0], meter_val[1], timestamp))
            lines.append(line)

        message = '\n'.join(lines) + '\n'
        send_msg(message, options)
        time.sleep(DELAY)
