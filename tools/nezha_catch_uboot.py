#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
哪吒救砖 - 自动抓 autoboot 并中断进入 U-Boot
用法: python nezha_catch_uboot.py <等待秒数>
      期间断电重插, 检测到 "Hit any key" 立即发空格
"""
import sys, os, time
import serial, serial.tools.list_ports as list_ports

BAUD = 115200
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nezha_cli.log")


def pick_port():
    for p in list_ports.comports():
        d = (p.description or "").lower()
        if "cp210" in d or "ch340" in d or "usb-serial" in d or "silicon" in d:
            return p.device
    for p in list_ports.comports():
        if "bluetooth" not in (p.description or "").lower():
            return p.device
    return None


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 60
    port = pick_port()
    if not port:
        print("找不到串口"); return
    ser = serial.Serial(port=port, baudrate=BAUD, bytesize=8, parity='N',
                        stopbits=1, timeout=0.1)
    logf = open(LOG, "ab")
    t0 = time.time()
    buf = b""
    caught = False
    print("== 等待 autoboot (%.0fs) == 请断电重插" % secs)
    while time.time() - t0 < secs:
        data = ser.read(8192)
        if not data:
            continue
        buf += data
        logf.write(data); logf.flush()
        txt = data.decode("utf-8", "replace")
        sys.stdout.write(txt); sys.stdout.flush()
        low = buf[-4000:].lower()
        if not caught and (b"hit any key" in low or b"stop autoboot" in low):
            time.sleep(0.05)
            for _ in range(6):
                ser.write(b" "); ser.flush()
                time.sleep(0.06)
            caught = True
            print("\n\n>>>>>> 已发送空格中断 <<<<<<\n")
    # 再敲回车确认提示符
    if caught:
        time.sleep(0.5)
        ser.write(b"\r"); ser.flush()
        time.sleep(1.0)
        ser.read(8192)
    logf.close(); ser.close()
    print("\n== done ==")
    return caught


if __name__ == "__main__":
    main()
