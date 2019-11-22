# Copyright (c) 2017-2019, Emmanuel Blot <emmanuel.blot@free.fr>
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

from logging import getLogger
from re import match
from time import sleep, time as now
from typing import Iterable, Union
from pyftdi.i2c import I2cController, I2cPort


class SerialEepromError(Exception):
    """Base class for all Serial Flash errors"""


class SerialEepromTimeout(SerialEepromError):
    """Exception thrown when a flash command cannot be completed in a timely
       manner"""


class SerialEepromValueError(ValueError, SerialEepromError):
    """Exception thrown when a parameter is out of range"""


class SerialEeprom:
    """Interface of a generic SPI flash device"""

    def read(self, address, length):
        """Read a sequence of bytes from the specified address."""
        raise NotImplementedError()

    def write(self, address, data):
        """Write a sequence of bytes, starting at the specified address."""
        raise NotImplementedError()

    @property
    def capacity(self):
        """Get the flash device capacity in bytes"""
        raise NotImplementedError()


class SerialEepromManager:
    """I2c flash manager.
    """

    @staticmethod
    def get_from_controller(i2cctrl: I2cController,
                            name: str, address: int = 0x50) -> SerialEeprom:
        """Obtain an instance of the detected flash device, using an
           existing SpiController.

           :param i2cctrl: a PyFtdi configured I2cController instance
           :param name: I2C EEPROM type
           :param address: I2C slave address
           :return: a concrete :py:class:`SerialEeprom` instance
        """
        size = SerialEepromManager.get_eeprom_size(name, address)
        slave = i2cctrl.get_port(address)
        flash = I2c24AADevice(slave, size)
        return flash

    @staticmethod
    def get_flash_device(url: str, name: str, address: int = 0x50,
                         highspeed: bool = False) -> SerialEeprom:
        """Obtain an instance of the detected flash device.

           :param url: FTDI url
           :param name: I2C EEPROM type
           :param address: I2C slave address
           :param highspeed: whether to use a 400 KHz vs. 100 KHz clock
           :return: a concrete :py:class:`SerialEeprom` instance
        """
        size = SerialEepromManager.get_eeprom_size(name, address)
        ctrl = I2cController()
        ctrl.configure(url, frequency=highspeed and 400E3 or 100E3)
        slave = ctrl.get_port(address)
        flash = I2c24AADevice(slave, size)
        return flash

    @staticmethod
    def get_eeprom_size(name: str, address: int) -> int:
        mo = match(r'(?i)^24AA(?P<size>\d+)(?P<rev>[a-z]?)$', name)
        if not mo:
            raise SerialEepromValueError('Unsupported type: %s' % name)
        size = int(mo.group('size')) << (10-3)
        word_size = I2c24AADevice.get_word_size(size)
        # special case with 24AA32: 24AA32 is 'obsolete' and not supported
        if (size == (4 << 10)) and (mo.group('rev').upper() != 'A'):
            raise SerialEepromValueError('Unsupported type: %s' % name)
        if word_size == 1:
            test_addr = 0x50
        else:
            test_addr = address & 0xf8
        if test_addr != 0x50:
            raise SerialEepromValueError('Invalid device address: 0x%02x' %
                                         address)
        return size

class I2c24AADevice(SerialEeprom):
    """Generic flash device implementation.
    """

    WRITE_CYCLE_TIME_MAX = 0.005

    DEVICES = {
        128: (8, 1),
        256: (8, 1),
        # the following devices require shifting slave addresses:
        # not yet implemented
        # 512: (16, 1),
        # 1 << 10: (16, 1),
        # 2 << 10: (16, 1),
        4 << 10: (32, 2),
        8 << 10: (32, 2),
        16 << 10: (64, 2),
        32 << 10: (64, 2),
        64 << 10: (128, 2),
    }

    def __init__(self, slave: I2cPort, size: int):
        self.log = getLogger('pyftdi.i2c.eeprom')
        self._slave = slave
        try:
            self._cache_size, self._addr_width = self.DEVICES[size]
        except KeyError:
            raise SerialEepromValueError('Unsupported flash size: %d KiB' %
                                         size)
        self._size = size
        self._cache_mask = self._cache_size-1
        self._slave.configure_register(True, self._addr_width)

    @classmethod
    def get_word_size(cls, size: int) -> int:
        """Return the SerialEepromt word size.

           :return: word size in bytes.
        """
        try:
            return cls.DEVICES[size][1]
        except KeyError:
            raise SerialEepromValueError('Unsupported flash size: %d KiB' %
                                         size)

    @property
    def capacity(self) -> int:
        """Get the flash device capacity.

           :return: storage capacity in bytes.
        """
        return self._size

    def __len__(self):
        return self._size

    def read(self, address: int, size: int) -> bytes:
        """Read data from SerialEeprom

           :param address: address of the first byte read from the eeprom
           :param int: count of bytes to read
           :return: a byte buffer of read bytes
        """
        if address+size > len(self):
            raise SerialEepromValueError('Out of range')
        # although it should not be necessary, it seems that reading out
        # all bytes at once triggers errors - reason unknown
        # read out reliability is greatly improved with short read sequence
        # we use the same chunk management as with write request to
        # align as much read requests as possible on device pages
        self.log.info('Read @ 0x%04x', address)
        return self._slave.read_from(address, size)

    def write(self, address: int,
              data: Union[bytes, bytearray, Iterable[int]]) -> None:
        """Write data to SerialEeprom.

           :param int: address of the first byte to write in SerialEeprom
           :param data: data buffer to write
        """
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data)
        if address+len(data) > len(self):
            raise SerialEepromValueError('Out of range')
        size = len(data)
        # unaligned left hand side
        left = address & self._cache_mask
        csize = self._cache_size
        if left:
            length = csize - left
            self._do_write(address, data[:length])
            offset = length
            address += length
        else:
            offset = 0
        # aligned buffer
        while offset < size:
            wsize = min(csize, size-offset)
            self._do_write(address, data[offset:offset+wsize])
            address += wsize
            offset += wsize

    def _do_write(self, address, data):
        self.log.info('Write @ 0x%04x %s', address, data)
        self._slave.write_to(address, data)
        last = now() + self.WRITE_CYCLE_TIME_MAX*4
        while now() < last:
            sleep(self.WRITE_CYCLE_TIME_MAX*4)
            break
        else:
            raise SerialEepromTimeout('Device did not complete write cycle')
