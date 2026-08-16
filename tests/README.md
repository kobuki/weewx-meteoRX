# Test helpers

These need weewx (5.0+) on the `PYTHONPATH`, plus the driver importable as
`user.meteostick`.  For a pip install of weewx that means
`PYTHONPATH=~/weewx-data/bin`; for a package install, `/etc/weewx/bin`.

## test_parse.py

Offline exercise of the packet parser.  Builds CRC-valid Davis packets, wraps
them in the receiver's 10-byte raw line format, and runs them through
`Meteostick.parse_readings`.  Covers wind, rain rate, rain counter,
temperature, humidity, solar, UV, leaf/soil, repeater packets, the `B`
receiver line, rain-counter wraparound, and a pile of malformed input.  No
hardware required.

```
PYTHONPATH=~/weewx-data/bin python3 tests/test_parse.py
```

Exits non-zero if anything fails.

## fakestick.py

Simulates a receiver on a pty so weewxd can be run end to end without
hardware.  It answers the reset and configuration commands, then streams
CRC-valid packets (with some line noise and malformed lines mixed in, to
check that the driver survives them).

```
PYTHONPATH=~/weewx-data/bin python3 tests/fakestick.py /tmp/ttyMETEO &
# then set port = /tmp/ttyMETEO in [Meteostick] and start weewxd
```
