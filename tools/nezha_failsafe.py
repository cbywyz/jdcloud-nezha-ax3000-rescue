#!/usr/bin/env python3
# -*- coding: ascii -*-
# Auto-catch failsafe prompt during kernel boot, press f, drop into shell
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import serial

PORT = 'COM5'
BAUD = 115200
TIMEOUT = int(sys.argv[1]) if len(sys.argv) > 1 else 120

ser = serial.Serial(PORT, BAUD, timeout=1)
print('watching failsafe prompt on %s for %ds' % (PORT, TIMEOUT))
ser.reset_input_buffer()

buf = b''
start = time.time()
triggered = False
while time.time() - start < TIMEOUT:
    chunk = ser.read(256)
    if chunk:
        buf += chunk
        try:
            text = buf.decode('utf-8', errors='replace')
        except Exception:
            text = ''
        # failsafe prompt line appears like:
        # "Press the [f] key and hit [enter] to enter failsafe mode"
        if not triggered and 'failsafe' in text:
            triggered = True
            print('[*] failsafe prompt detected! sending f...')
            time.sleep(0.3)
            ser.write(b'f\n')
            time.sleep(0.5)
            ser.write(b'\n')
            time.sleep(1.0)
            ser.write(b'\n')
        if triggered and ('root@' in text or '/#' in text):
            print('[*] shell reached!')
            break

if triggered:
    # dump recent output
    tail = buf[-4000:]
    print('---- tail ----')
    print(tail.decode('utf-8', errors='replace'))
else:
    print('[-] failsafe never triggered, tail:')
    print(buf[-1500:].decode('utf-8', errors='replace'))
ser.close()
