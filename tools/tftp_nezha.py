#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
哪吒救砖 · TFTP 服务器 (一键运行)
用法: python tftp_nezha.py [绑定的网卡IP, 默认192.168.10.100]
作用: 把固件文件通过 TFTP 提供给 U-Boot (板子来拉)
文件查找顺序: 本脚本目录 -> 上级目录 -> 上级目录/firmware
"""
import socket, os, struct, threading, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
BIND_IP = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TFTP_BIND_IP", "192.168.10.100")
PORT = 69

# 在这些目录里找固件文件 (本目录、上级、上级/firmware)
SEARCH_DIRS = [BASE, os.path.dirname(BASE), os.path.join(os.path.dirname(BASE), "firmware")]
WANTED = [
    "kwrt-factory.bin", "gpt.bin", "uboot.bin",
    "kernel.bin", "root.bin",
    "nwrt-qsdk.bin", "nwrt-generic.bin",
]


def find_files():
    found = {}
    for name in WANTED:
        for d in SEARCH_DIRS:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                found[name] = p
                break
    return found


FILES = find_files()


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def serve_file(fname, peer, blob):
    """用一个新的随机端口把 blob 发给 peer (标准 TFTP 行为)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((BIND_IP, 0))
    s.settimeout(3)
    try:
        total = len(blob)
        blks = (total + 511) // 512
        log("RRQ %s  %d bytes (%d blocks) -> %s" % (fname, total, blks, peer[0]))
        pos = 0
        blk = 1
        while pos < total or (total == 0 and blk == 1):
            chunk = blob[pos:pos + 512]
            pkt = struct.pack(">HH", 3, blk & 0xFFFF) + chunk
            ok = False
            for _ in range(6):
                s.sendto(pkt, peer)
                try:
                    resp, _a = s.recvfrom(2048)
                    op = struct.unpack(">H", resp[:2])[0]
                    if op == 4 and struct.unpack(">H", resp[2:4])[0] == (blk & 0xFFFF):
                        ok = True
                        break
                except socket.timeout:
                    continue
            if not ok:
                log("!! block %d 超时, 放弃" % blk)
                return
            pos += len(chunk)
            blk += 1
            if blk % 2000 == 0:
                log("   ...已发 %d/%d KB" % (pos // 1024, total // 1024))
        # 若刚好 512 整数倍, 补一个空块
        if total % 512 == 0 and total > 0:
            pkt = struct.pack(">HH", 3, blk & 0xFFFF) + b""
            for _ in range(3):
                s.sendto(pkt, peer)
                try:
                    s.recvfrom(2048)
                    break
                except socket.timeout:
                    continue
        log("DONE %s 发送完毕 (%d bytes)" % (fname, total))
    except Exception as e:
        log("ERR send %s: %s" % (fname, e))
    finally:
        s.close()


def main():
    # 预检文件
    for f, p in FILES.items():
        if not os.path.isfile(p):
            log("警告: 缺少 %s (%s)" % (f, p))

    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        srv.bind((BIND_IP, PORT))
    except OSError as e:
        log("绑定 %s:%d 失败: %s" % (BIND_IP, PORT, e))
        log("检查: 1) 以太网口是否设成 192.168.10.100  2) 是否有别的 TFTP 占 69 端口")
        input("按回车退出...")
        return
    log("TFTP 服务器就绪, 监听 %s:%d" % (BIND_IP, PORT))
    log("可提供文件: %s" % ", ".join(FILES.keys()))
    log("等待板子(192.168.10.10)来拉文件... Ctrl+C 停止")
    while True:
        try:
            data, peer = srv.recvfrom(2048)
        except KeyboardInterrupt:
            log("停止")
            break
        if len(data) < 4:
            continue
        op = struct.unpack(">H", data[:2])[0]
        if op == 1:  # RRQ
            fname = data[2:].split(b"\x00")[0].decode("utf-8", "replace")
            path = FILES.get(fname)
            if path and os.path.isfile(path):
                with open(path, "rb") as f:
                    blob = f.read()
                threading.Thread(target=serve_file, args=(fname, peer, blob), daemon=True).start()
            else:
                log("未找到文件: %s (from %s)" % (fname, peer[0]))
                # 回 ERROR
                err = struct.pack(">HH", 5, 1) + b"File not found\x00"
                srv.sendto(err, peer)
        else:
            log("忽略 opcode=%d from %s" % (op, peer[0]))


if __name__ == "__main__":
    main()
