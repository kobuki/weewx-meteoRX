#!/usr/bin/env python3
"""Offline exercise of the meteoRX parser.  Requires weewx on the PYTHONPATH.

Builds CRC-valid Davis packets, wraps them in the receiver's 10-byte raw line
format, and runs them through Meteostick.parse_readings.  No hardware needed.

    PYTHONPATH=~/weewx-data/bin python3 test_parse.py
"""

import sys

from weewx.crc16 import crc16
from user.meteostick import Meteostick, MeteostickDriver

FAILURES = []


def check(label, cond, detail=''):
    if cond:
        print("  ok   %s %s" % (label, detail))
    else:
        print("  FAIL %s %s" % (label, detail))
        FAILURES.append(label)


def make_line(body6, channel, rssi=-65, ts_last=2562444, repeater=False):
    """body6: the 6 payload bytes; byte 0 carries the message type in its high
    nibble.  Returns a raw 10-byte-format 'I' line with a valid Davis CRC."""
    data = bytearray(body6)
    assert len(data) == 6
    data[0] = (data[0] & 0xF0) | ((channel - 1) & 0x7)
    if repeater:
        # wire layout: 6 data bytes, crc, then the repeater id.  the crc is
        # computed over data + repeater id, which is why the driver swaps
        # [6:8] with [8:10] before checking it.
        rpt_id = bytearray([0x51, 0x52])
        crc = crc16(data + rpt_id)
        full = data + bytearray([(crc >> 8) & 0xff, crc & 0xff]) + rpt_id
    else:
        crc = crc16(data)
        full = data + bytearray([(crc >> 8) & 0xff, crc & 0xff]) + bytearray([0xff, 0xff])
    fields = ['I', '100'] + ['%02X' % b for b in full] + ['0', str(rssi), str(ts_last)]
    return ' '.join(fields)


def main():
    stick = Meteostick(port='/dev/null', iss_channel=1, anemometer_channel=2,
                       leaf_soil_channel=3, temp_hum_1_channel=4,
                       solar_channel=-1, uv_channel=-1)
    rpt = 0.2

    print("wind + rain-rate (msg type 5), iss channel 1")
    line = make_line([0x50, 0x20, 0x30, 0xFF, 0x75, 0x00], channel=1)
    d = stick.parse_readings(line, rpt)
    check('channel', d.get('channel') == 1, d.get('channel'))
    check('wind_speed present', 'wind_speed' in d, d.get('wind_speed'))
    check('wind_dir present', 'wind_dir' in d, d.get('wind_dir'))
    check('rain_rate present', 'rain_rate' in d, d.get('rain_rate'))
    check('rf_signal', d.get('rf_signal') == -65, d.get('rf_signal'))

    print("outside temperature (msg type 8), digital sensor")
    line = make_line([0x80, 0x00, 0x00, 0x33, 0x8D, 0x00], channel=1)
    d = stick.parse_readings(line, rpt)
    check('temperature present', 'temperature' in d, d.get('temperature'))
    check('temperature sane', 'temperature' in d and -60 < d['temperature'] < 70,
          d.get('temperature'))

    print("outside humidity (msg type A)")
    line = make_line([0xA0, 0x00, 0x00, 0xC9, 0x3D, 0x00], channel=1)
    d = stick.parse_readings(line, rpt)
    check('humidity present', 'humidity' in d, d.get('humidity'))
    check('humidity sane', 'humidity' in d and 0 <= d['humidity'] <= 100,
          d.get('humidity'))

    print("rain counter (msg type E)")
    line = make_line([0xE0, 0x00, 0x00, 0x05, 0x05, 0x00], channel=1)
    d = stick.parse_readings(line, rpt)
    check('rain_count', d.get('rain_count') == 5, d.get('rain_count'))

    print("solar radiation (msg type 6)")
    line = make_line([0x60, 0x00, 0x00, 0xDB, 0x00, 0x43], channel=1)
    d = stick.parse_readings(line, rpt)
    check('solar_radiation present', 'solar_radiation' in d, d.get('solar_radiation'))

    print("uv (msg type 4)")
    line = make_line([0x40, 0x00, 0x00, 0x12, 0x45, 0x00], channel=1)
    d = stick.parse_readings(line, rpt)
    check('uv present', 'uv' in d, d.get('uv'))

    print("leaf/soil station (msg type F, soil moisture) on channel 3")
    line = make_line([0xF2, 0x09, 0x1A, 0x55, 0xC0, 0x00], channel=3)
    d = stick.parse_readings(line, rpt)
    check('soil_temp_1', 'soil_temp_1' in d, d.get('soil_temp_1'))
    check('soil_moisture_1', 'soil_moisture_1' in d, d.get('soil_moisture_1'))

    print("repeater packet (crc bytes swapped out to positions 8/9)")
    line = make_line([0xE0, 0x00, 0x00, 0x07, 0x05, 0x00], channel=1, repeater=True)
    d = stick.parse_readings(line, rpt)
    check('rain_count via repeater', d.get('rain_count') == 7, d.get('rain_count'))

    print("receiver 'B' line, with and without inside humidity")
    d = stick.parse_readings('B 29530 338141 366 101094 60 37', rpt)
    check('temp_in', abs(d.get('temp_in', 0) - 36.6) < 0.01, d.get('temp_in'))
    check('pressure', abs(d.get('pressure', 0) - 1010.94) < 0.01, d.get('pressure'))
    d = stick.parse_readings('B 29530 338141 366 101094 60 37 45', rpt)
    check('humidity_in', d.get('humidity_in') == 45.0, d.get('humidity_in'))

    print("extra temp/hum station on channel 4, with debug parsing on")
    import user.meteostick as ms
    ms.DEBUG_PARSE = 3
    ms.DEBUG_SERIAL = 3
    ms.DEBUG_RAIN = 1
    try:
        line = make_line([0xA0, 0x00, 0x00, 0xC9, 0x3D, 0x00], channel=4)
        d = stick.parse_readings(line, rpt)
        check('humid_1 present', 'humid_1' in d, d.get('humid_1'))
        check('no outHumidity for th1', 'humidity' not in d, d)
        line = make_line([0x80, 0x00, 0x00, 0x33, 0x8D, 0x00], channel=4)
        d = stick.parse_readings(line, rpt)
        check('temp_1 present', 'temp_1' in d, d.get('temp_1'))
        # every message type, with debug on, must not blow up
        for mtype in range(0, 16):
            line = make_line([mtype << 4, 0x10, 0x20, 0x30, 0x40, 0x00], channel=1)
            try:
                stick.parse_readings(line, rpt)
                check('msg type 0x%X with debug on' % mtype, True)
            except Exception as e:
                check('msg type 0x%X with debug on' % mtype, False,
                      '%s: %s' % (type(e).__name__, e))
    finally:
        ms.DEBUG_PARSE = ms.DEBUG_SERIAL = ms.DEBUG_RAIN = 0

    print("malformed input must not raise")
    for bad in ['I 100 ZZ', 'I', 'X 1 2 3', '# hello', '',
                'I 100 FF FF FF FF FF FF FF FF FF FF 0 -65 100',
                'I 100 1FF 00 00 00 00 00 00 00 FF FF 0 -65 100']:
        try:
            stick.parse_readings(bad, rpt)
            check('survived %r' % bad, True)
        except Exception as e:
            check('survived %r' % bad, False, '%s: %s' % (type(e).__name__, e))

    print("bad crc is rejected without a crash")
    line = make_line([0xE0, 0x00, 0x00, 0x05, 0x05, 0x00], channel=1)
    fields = line.split(' ')
    fields[9] = '%02X' % ((int(fields[9], 16) ^ 0xFF) & 0xFF)
    d = stick.parse_readings(' '.join(fields), rpt)
    check('crc failure yields no data', 'rain_count' not in d, d)

    print("non-ascii noise is rejected")
    d = stick.parse_readings('I 100 ��', rpt)
    check('noise rejected', d == {} or 'channel' not in d, d)

    print("_data_to_packet / rain delta and wraparound")
    drv = MeteostickDriver.__new__(MeteostickDriver)
    drv.sensor_map = dict(MeteostickDriver.DEFAULT_SENSOR_MAP)
    drv.rain_per_tip = rpt
    drv.last_rain_count = None
    p = drv._data_to_packet({'rain_count': 10, 'temperature': 20.0})
    check('first packet rain is 0', p['rain'] == 0.0, p['rain'])
    p = drv._data_to_packet({'rain_count': 12, 'temperature': 20.0})
    check('rain delta', abs(p['rain'] - 0.4) < 1e-9, p['rain'])
    p = drv._data_to_packet({'rain_count': 2, 'temperature': 20.0})
    check('wraparound', abs(p['rain'] - (118 * rpt)) < 1e-9, p['rain'])
    check('usUnits set', 'usUnits' in p and 'dateTime' in p)

    print("_fmt handles str and bytes")
    check('_fmt bytes', __import__('user.meteostick', fromlist=['_fmt'])._fmt(b'\x00\xff') == '00 ff')
    check('_fmt str', __import__('user.meteostick', fromlist=['_fmt'])._fmt('AB') == '41 42')

    print()
    if FAILURES:
        print("%d FAILURES: %s" % (len(FAILURES), FAILURES))
        return 1
    print("all checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
