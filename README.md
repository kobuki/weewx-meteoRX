## weewx-meteoRX

### About this Repository

This repository is a fork of [https://github.com/matthewwall/weewx-meteostick](https://github.com/matthewwall/weewx-meteostick) for use with custom receiver modules. It has been modified and fixed in numerous ways to better support these custom receivers. It strives to maintain compatibility with the Meteostick driver as much as possible and should be compatible with either the custom receiver or the one described in the [https://github.com/kobuki/VPTools](https://github.com/kobuki/VPTools) repo.

### Requirements

- weewx 5.0 or newer (tested against 5.5)
- Python 3.7 or newer, as required by weewx 5 (tested against 3.13 on
  Debian 13 "trixie")
- pyserial

Neither the driver nor weewx 5 depends on the `future` package, so this runs
on distributions such as Debian 13 that no longer ship `python3-future`.

For weewx 4.x, use driver version 2025020702 (commit `103b245`), the last
release that carried the weewx 3/4 compatibility shims.

### Installation

0) Install weewx, select Simulator as the weather station

https://weewx.com/docs/5.1/usersguide/installing/

1) Download the driver

```
wget -O weewx-meteoRX.zip https://github.com/kobuki/weewx-meteoRX/archive/master.zip
```

2) Install the driver

```
sudo weectl extension install weewx-meteoRX.zip
```

3) Select and configure the driver

```
sudo weectl station reconfigure
```

4) Restart weewx

```
sudo systemctl restart weewx
```

### Querying and configuring the receiver

The driver ships a configurator, reachable through `weectl device`:

```
sudo weectl device --info
sudo weectl device --show-options
sudo weectl device --set-bandwidth=0
```

### Running the driver standalone

For troubleshooting you can run the driver directly, without the weewx engine.
Point `PYTHONPATH` at the directory holding your `user` package (by default
`~/weewx-data/bin` for a pip install, `/etc/weewx/bin` for a package install):

```
PYTHONPATH=~/weewx-data/bin python3 ~/weewx-data/bin/user/meteostick.py --help
PYTHONPATH=~/weewx-data/bin python3 ~/weewx-data/bin/user/meteostick.py --port=/dev/ttyUSB0
```
