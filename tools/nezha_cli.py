#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
哪吒 AX3000 (RE-OS-03U) TTL 串口交互/刷机工具
用法:
  python nezha_cli.py send  "help"               # 发一条命令并抓回显(~4s)
  python nezha_cli.py send  "httpd"  --wait 10   # 发命令并等待更久
  python nezha_cli.py mon   30                   # 纯监控 30 秒
  python nezha_cli.py boot  httpd                # 重启后在 autoboot 处中断并执行命令
  python nezha_cli.py raw   "0x0a 0x0a"          # 发原始十六进制字节
接线: GND-GND, 白线(RXD)->板子TX, 绿线(TXD)->板子RX, 红线(VCC)不接. 115200 8N1
"""
import sys, os, time

try:
    import serial
    import serial.tools.list_ports as list_ports
except ImportError:
    print("缺少 pyserial, 请先 pip install pyserial")
    sys.exit(1)

BAUD = 115200
LOGDIR = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(LOGDIR, "nezha_cli.log")


def pick_port():
    cands = []
    for p in list_ports.comports():
        d = (p.description or "").lower()
        h = (p.hwid or "").lower()
        if "bluetooth" in d or "bth" in h:
            continue
        if "cp210" in d or "ch340" in d or "usb-serial" in d or "uart" in d or "silicon" in d:
            cands.append(p.device)
    if len(cands) == 1:
        return cands[0]
    if cands:
        print("多个候选串口: %s -> 用第一个 %s" % (cands, cands[0]))
        return cands[0]
    # 兜底: 列出所有口
    allp = [p.device for p in list_ports.comports()]
    if allp:
        print("未识别到 CP210x, 可用口: %s -> 用 %s" % (allp, allp[0]))
        return allp[0]
    return None


def open_port(port):
    return serial.Serial(port=port, baudrate=BAUD, bytesize=8,
                         parity='N', stopbits=1, timeout=0.2)


def pump(ser, seconds, logf, echo=True):
    t0 = time.time()
    while time.time() - t0 < seconds:
        data = ser.read(8192)
        if data:
            try:
                logf.write(data); logf.flush()
            except Exception:
                pass
            if echo:
                sys.stdout.write(data.decode("utf-8", "replace"))
                sys.stdout.flush()


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    act = sys.argv[1]
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    wait = 4.0
    if "--wait" in sys.argv:
        i = sys.argv.index("--wait")
        if i + 1 < len(sys.argv):
            try:
                wait = float(sys.argv[i + 1])
            except ValueError:
                pass

    port = pick_port()
    if not port:
        print("找不到串口, 请检查 CP2102 是否插好")
        return
    print("串口: %s @ %d 8N1\n" % (port, BAUD))
    try:
        ser = open_port(port)
    except Exception as e:
        print("打开串口失败: %s" % e)
        return

    logf = open(LOG, "ab")
    try:
        if act == "mon":
            secs = float(args[0]) if args and args[0].replace('.', '', 1).isdigit() else 30
            print("== 监控 %.0fs ==" % secs)
            pump(ser, secs, logf)
        elif act == "send":
            if not args:
                print("需要命令参数"); return
            cmd = args[0]
            print(">>> 发送: %r" % cmd)
            ser.write((cmd + "\r").encode()); ser.flush()
            pump(ser, wait, logf)
        elif act == "raw":
            if not args:
                print("需要十六进制参数"); return
            b = bytes(int(x, 16) for x in args[0].replace(",", " ").split())
            print(">>> 发送原始: %s" % b.hex())
            ser.write(b); ser.flush()
            pump(ser, wait, logf)
        else:
            print("未知命令: %s" % act)
    except KeyboardInterrupt:
        print("\n(中断)")
    finally:
        logf.close(); ser.close()
        print("\n== done, 日志追加到 %s ==" % LOG)


if __name__ == "__main__":
    main()
