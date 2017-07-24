#!/usr/bin/env python3
# Copyright (c) 2017, Emmanuel Blot <emmanuel.blot@free.fr>
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

from i2cflash.serialeeprom import SerialEepromManager
from os import environ
from pyftdi import FtdiLogger
from pyftdi.misc import pretty_size
from sys import stdout
from time import time as now
import logging
import unittest


class SerialEepromTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # FTDI device should be defined to your actual setup
        cls.ftdi_url = environ.get('FTDI_DEVICE', 'ftdi://ftdi:232h/1')
        print('Using FTDI device %s' % cls.ftdi_url)

    def setUp(self):
        self.flash = SerialEepromManager.get_flash_device(self.ftdi_url,
                                                          '24AA32A', 0x50)

    def tearDown(self):
        del self.flash

    def test_flashdevice_1_read_bandwidth(self):
        """Read the whole device to get READ bandwith
        """
        delta = now()
        data = self.flash.read(0, len(self.flash))
        delta = now()-delta
        length = len(data)
        self._report_bw('Read', length, delta)

    def test_flashdevice_2_small_rw(self):
        """Short R/W test
        """
        baseaddr = 0x0034
        tpl = 'This is an I2C EEPROM test %d. '
        string = ''.join([tpl % count for count in range(20)])
        refstr = string.encode('ascii')
        delta = now()
        self.flash.write(baseaddr, refstr)
        delta = now()-delta
        data = self.flash.read(baseaddr, len(refstr))
        print(refstr)
        print(data)
        for n, (r, d) in enumerate(zip(refstr, data), start=1):
            if r != d:
                print('Mismatch @ %d/0x%x' % (n, n))
                break
        self.assertEqual(r, d, 'R/W mismatch')
        length = len(data)
        self._report_bw('Write', length, delta)
        data = self.flash.read(baseaddr+0x40, len(refstr)-0x40)
        print(data)

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


if __name__ == '__main__':
    FtdiLogger.log.addHandler(logging.StreamHandler(stdout))
    level = environ.get('FTDI_LOGLEVEL', 'info').upper()
    try:
        loglevel = getattr(logging, level)
    except AttributeError:
        raise ValueError('Invalid log level: %s', level)
    FtdiLogger.set_level(loglevel)
    unittest.main(defaultTest='suite')
