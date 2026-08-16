#!/usr/bin/env python3
"""Simulate a meteoRX/VPTools receiver on a pty, for end-to-end driver testing.

Creates a pty, prints its slave path, then speaks the receiver protocol:
responds to the reset/config commands and streams CRC-valid raw packets.

    PYTHONPATH=~/weewx-data/bin python3 fakestick.py /tmp/ttyMETEO
"""

import os
import pty
import sys
import time

from weewx.crc16 import crc16

CHANNEL = 1


def make_line(body6, channel=CHANNEL, rssi=-65, ts_last=2562444):
    data = bytearray(body6)
    data[0] = (data[0] & 0xF0) | ((channel - 1) & 0x7)
    crc = crc16(data)
    full = data + bytearray([(crc >> 8) & 0xff, crc & 0xff]) + bytearray([0xff, 0xff])
    fields = ['I', '100'] + ['%02X' % b for b in full] + ['0', str(rssi), str(ts_last)]
    return ' '.join(fields) + '\r\n'


PACKETS = [
    'B 29530 338141 366 101094 60 37 45\r\n',
    make_line([0x50, 0x20, 0x30, 0xFF, 0x75, 0x00]),   # wind + rain rate
    make_line([0x80, 0x00, 0x00, 0x33, 0x8D, 0x00]),   # outside temp
    make_line([0xA0, 0x00, 0x00, 0xC9, 0x3D, 0x00]),   # outside humidity
    make_line([0xE0, 0x00, 0x00, 0x05, 0x05, 0x00]),   # rain counter
    make_line([0x60, 0x00, 0x00, 0xDB, 0x00, 0x43]),   # solar radiation
    make_line([0x40, 0x00, 0x00, 0x12, 0x45, 0x00]),   # uv
    b'\xff\xfe garbage \x80\r\n',                      # line noise
    'I 100 ZZ GARBAGE\r\n',                            # malformed
]


def main():
    link = sys.argv[1]
    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    if os.path.islink(link) or os.path.exists(link):
        os.unlink(link)
    os.symlink(slave_name, link)
    print("pty ready at %s -> %s" % (link, slave_name), flush=True)

    banner = ("# MeteoRX simulator\r\n# fake firmware 1.0\r\n?")
    started = False
    buf = b''
    i = 0
    while True:
        # drain any command bytes without blocking
        import select
        r, _, _ = select.select([master], [], [], 0.2)
        if r:
            chunk = os.read(master, 1024)
            buf += chunk
            while b'\r' in buf:
                cmd, buf = buf.split(b'\r', 1)
                cmd = cmd.decode('ascii', 'replace').strip()
                print("cmd: %r" % cmd, flush=True)
                if cmd == 'r':
                    # real hardware takes about a second to come back after a
                    # reset; the driver flushes its input before it starts
                    # looking for the '?' prompt, so answering instantly loses it
                    time.sleep(1.0)
                    os.write(master, banner.encode('ascii'))
                    started = True
                else:
                    os.write(master, ("# ack %s\r\n" % cmd).encode('ascii'))
        if started:
            pkt = PACKETS[i % len(PACKETS)]
            if isinstance(pkt, str):
                pkt = pkt.encode('ascii')
            os.write(master, pkt)
            i += 1
            time.sleep(0.05)


if __name__ == '__main__':
    main()
