## weewx-meteoRX

### About this Repository

This repository is a fork of [https://github.com/matthewwall/weewx-meteostick](https://github.com/matthewwall/weewx-meteostick) for use with custom receiver modules. It has been modified and fixed in numerous ways to better support these custom receivers. It strives to maintain compatibility with the Meteostick driver as much as possible and should be compatible with either the custom receiver or the one in the [https://github.com/kobuki/VPTools](https://github.com/kobuki/VPTools) repo.  

Read data from a meteostick via serial connection.


### Installation

0) Install weewx, select Simulator as the weather station

http://weewx.com/docs/usersguide.htm

1) Download the driver

wget -O weewx-meteoRX.zip https://github.com/kobuki/weewx-meteoRX/archive/master.zip

2) Install the driver

sudo wee_extension --install weewx-meteoRX.zip

3) Configure the driver

sudo wee_config --reconfigure

4) Start weewx

sudo /etc/init.d/weewx start
