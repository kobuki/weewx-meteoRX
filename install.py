# installer for the meteoRX / meteostick driver
# Copyright 2016 Matthew Wall
# Distributed under the terms of the GNU Public License (GPLv3)

import weewx

from weecfg.extension import ExtensionInstaller

REQUIRED_WEEWX = "5.0"

weewx.require_weewx_version("meteostick", REQUIRED_WEEWX)


def loader():
    return MeteostickInstaller()


class MeteostickInstaller(ExtensionInstaller):
    def __init__(self):
        super(MeteostickInstaller, self).__init__(
            version="2026081601",
            name='meteostick',
            description='Collect data from meteostick via serial port',
            author="Matthew Wall",
            author_email="mwall@users.sourceforge.net",
            files=[('bin/user', ['bin/user/meteostick.py', 'bin/user/windcal.dat'])]
            )
