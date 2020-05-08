#!/usr/bin/env python3

# Copyright (c) 2017-2020, Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import unittest
from os import environ
from random import randint, seed
from sys import stdout, stderr
from time import time as now
from pyftdi import FtdiLogger
from pyftdi.ftdi import Ftdi
from pyftdi.i2c import I2cController
from pyftdi.misc import pretty_size
from pyftdi.usbtools import UsbTools
from i2cflash.serialeeprom import SerialEepromManager

#pylint: disable-msg=missing-docstring


class SerialEepromTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # FTDI device should be defined to your actual setup
        cls.ftdi_url = environ.get('FTDI_DEVICE', 'ftdi://ftdi:232h/1')
        seed()
        print('Using FTDI device %s' % cls.ftdi_url)

    def setUp(self):
        self.flash = None

    def tearDown(self):
        del self.flash

    def test_flashdevice_1_read_bandwidth(self):
        """Read the whole device to get READ bandwith
        """
        self.flash = SerialEepromManager.get_flash_device(self.ftdi_url,
                                                          '24AA32A', 0x50,
                                                          highspeed=True)
        delta = now()
        data = self.flash.read(0, len(self.flash))
        delta = now()-delta
        length = len(data)
        self._report_bw('Read', length, delta)

    def test_flashdevice_2_small_rw(self):
        """Short R/W test
        """
        self.flash = SerialEepromManager.get_flash_device(self.ftdi_url,
                                                          '24AA32A', 0x50)
        baseaddr = 0x0034
        # use a pseudo-random number to ensure to consecutive run work, in
        # the event where the write would silently fail and the read would
        # read back the data stored from a previous session. The length of
        # the string is also important to be sure to generate unaligned
        # accesses.
        tpl = 'This is %02x I2C EEPROM test %%d. ' % randint(0x00, 0xff)
        string = ''.join([tpl % count for count in range(20)])
        refstr = string.encode('ascii')
        delta = now()
        self.flash.write(baseaddr, refstr)
        delta = now()-delta
        data = self.flash.read(baseaddr, len(refstr))
        for n, (r, d) in enumerate(zip(refstr, data), start=1):
            if r != d:
                print('Mismatch %s/%s @ 0x%x on %d bytes' %
                      (r, d, n, len(refstr)), file=stderr)
                break
        self.assertEqual(r, d, 'R/W mismatch')
        length = len(data)
        self._report_bw('Write', length, delta)
        data = self.flash.read(baseaddr+0x40, len(refstr)-0x40)

    def test_usb_device(self):
        """Demo instanciation from an existing UsbDevice.
        """
        candidate = Ftdi.get_identifiers(self.ftdi_url)
        usbdev = UsbTools.get_device(candidate[0])
        i2c = I2cController()
        i2c.configure(usbdev, interface=candidate[1], frequency=100e3)
        eeprom = SerialEepromManager.get_from_controller(i2c, '24AA32A', 0x50)

    def test_i2c_controller(self):
        """Demo instanciation with an I2cController.
        """
        i2c = I2cController()
        i2c.configure(self.ftdi_url, frequency=100e3)
        eeprom = SerialEepromManager.get_from_controller(i2c, '24AA32A', 0x50)

    @classmethod
    def _report_bw(cls, action, length, time_):
        if time_ < 1.0:
            print("%s %s in %d ms @ %s/s" % (action, pretty_size(length),
                  int(1000*time_), pretty_size(length/time_)))
        else:
            print("%s %s in %d seconds @ %s/s" % (action, pretty_size(length),
                  int(time_), pretty_size(length/time_)))


def suite():
    return unittest.makeSuite(SerialEepromTestCase, 'test')


def main():
    FtdiLogger.log.addHandler(logging.StreamHandler(stdout))
    level = environ.get('FTDI_LOGLEVEL', 'info').upper()
    try:
        loglevel = getattr(logging, level)
    except AttributeError:
        raise ValueError('Invalid log level: %s', level)
    FtdiLogger.set_level(loglevel)
    unittest.main(defaultTest='suite')


if __name__ == '__main__':
    main()
