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


def make_line(body6, channel=CHANNEL, rssi=-65, ts_last=2562444, fei=-1):
    data = bytearray(body6)
    data[0] = (data[0] & 0xF0) | ((channel - 1) & 0x7)
    crc = crc16(data)
    full = data + bytearray([(crc >> 8) & 0xff, crc & 0xff]) + bytearray([0xff, 0xff])
    fields = ['I', '100'] + ['%02X' % b for b in full] + ['0', str(rssi), str(ts_last), str(fei)]
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
    """FAKE_MODE selects the receiver behaviour:
    wxreceiver  - like WxReceiver: '# OK resetting', banner, state shown by '?' (default)
    doubleboot  - as above, plus a banner from an earlier boot (a DTR reset when the
                  port was opened over a network bridge) arriving just before it
    drop:<cmd>  - as wxreceiver, but the first <cmd> (e.g. t3) is lost
    legacy      - old fake: banner only, '# ack' replies, '?' without settings
    """
    import select
    link = sys.argv[1]
    mode = os.environ.get('FAKE_MODE', 'wxreceiver')
    drop = mode.split(':', 1)[1] if mode.startswith('drop:') else None
    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    if os.path.islink(link) or os.path.exists(link):
        os.unlink(link)
    os.symlink(slave_name, link)
    print("pty ready at %s -> %s, mode %s" % (link, slave_name, mode), flush=True)

    def send(text):
        os.write(master, text.encode('ascii'))

    defaults = {'t': '1', 'o': '0', 'm': '1', 'x': '190', 'r': '0', 'a': '12'}
    state = dict(defaults)
    running = False
    boots = 0
    buf = b''
    i = 0
    while True:
        # drain any command bytes without blocking
        r, _, _ = select.select([master], [], [], 0.2)
        if r:
            chunk = os.read(master, 1024)
            buf += chunk
            while b'\r' in buf:
                cmd, buf = buf.split(b'\r', 1)
                cmd = cmd.decode('ascii', 'replace').strip()
                print("cmd: %r" % cmd, flush=True)
                if drop is not None and cmd == drop:
                    drop = None
                    print("dropped %r" % cmd, flush=True)
                    continue
                if mode == 'legacy':
                    if cmd == 'r':
                        # real hardware takes about a second to come back after a reset
                        time.sleep(1.0)
                        send("# MeteoRX simulator\r\n# fake firmware 1.0\r\n?")
                        running = True
                    elif cmd.startswith('a'):
                        send("# OK afc %s\r\n" % cmd[1:])
                    else:
                        send("# ack %s\r\n" % cmd)
                    continue
                if cmd == 'r':
                    if mode == 'doubleboot' and boots == 0:
                        send("# WxReceiver fake ready to accept commands\r\n?\r\n")
                        print("banner (earlier boot)", flush=True)
                        time.sleep(0.1)
                    boots += 1
                    send("# OK resetting\r\n")
                    running = False
                    state = dict(defaults)
                    time.sleep(1.0)
                    send("# WxReceiver fake ready to accept commands\r\n?\r\n")
                    print("banner (after reset)", flush=True)
                elif cmd == '?':
                    send("# OK t%s f1 o%s m%s x%s r%s a%s %s\r\n" % (
                        state['t'], state['o'], state['m'], state['x'], state['r'], state['a'],
                        'running' if running else 'stopped'))
                elif cmd[:1] in state and len(cmd) > 1:
                    state[cmd[0]] = cmd[1:]
                    if cmd[0] == 'm':
                        running = True
                    send("# OK %s\r\n" % cmd)
                elif cmd == 'f1':
                    send("# OK filter on\r\n")
                else:
                    send("# ERR bad command\r\n")
        if running:
            pkt = PACKETS[i % len(PACKETS)]
            if isinstance(pkt, str):
                pkt = pkt.encode('ascii')
            os.write(master, pkt)
            i += 1
            time.sleep(0.05)


if __name__ == '__main__':
    main()
