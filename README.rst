pyi2cflash
==========

.. image:: https://github.com/eblot/pyi2cflash/workflows/Python%20package/badge.svg
   :alt: Python package build status

I2C eeprom device drivers (pure Python)

I2C flash devices, also known as *DataFlash* are commonly found in embedded
products, to store firmware, microcode or configuration parameters.

PyI2CFlash_ comes with several pure Python drivers for those flash devices, that
demonstrate use of I2C devices with PyFtdi_. It could also be useful to dump
flash contents or recover from a bricked devices.

.. _PyI2CFlash : https://github.com/eblot/pyi2cflash
.. _Python: http://python.org/
.. _PyFtdi : https://github.com/eblot/pyftdi

Supported I2C flash devices
---------------------------

============== ========== ========== ========== ========== ========== ========== ========== ========== ========== ==========
Vendor          Microchip  Microchip  Microchip  Microchip  Microchip  Microchip  Microchip  Microchip  Microchip  Microchip
-------------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------
EEPROM           24AA01_    24AA02_    24AA04_    24AA08_    24AA16_   24AA32A_    24AA64_   24AA128_   24AA256_   24AA512_
============== ========== ========== ========== ========== ========== ========== ========== ========== ========== ==========
Status              ?          ?         No         No         No         Ok          ?          ?          ?         ?
-------------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------
Size               128        256        512        1Ki        2Ki        4Ki        8Ki       16Ki       32Ki       64Ki
============== ========== ========== ========== ========== ========== ========== ========== ========== ========== ==========

Notes about performances
........................

* *Read* operation is synchronous with I2C bus clock: it therefore only depends
  on the achievable frequency on the I2C bus, which is bound to the highest
  supported frequency of the flash device.
* *Write* operation depends mostly on the flash device performance, whose upper
  limit comes mostly from the maximum write packet size of the device, as the
  device needs to be polled for completion after each packet: the shorter the
  packet, the higher traffic on the I2C and associated overhead.

.. _24AA01: http://ww1.microchip.com/downloads/en/DeviceDoc/21711c.pdf
.. _24AA02: http://ww1.microchip.com/downloads/en/DeviceDoc/21709c.pdf
.. _24AA04: http://ww1.microchip.com/downloads/en/DeviceDoc/21124E.pdf
.. _24AA08: http://ww1.microchip.com/downloads/en/DeviceDoc/21710c.pdf
.. _24AA16: http://ww1.microchip.com/downloads/en/DeviceDoc/21703d.pdf
.. _24AA32A: http://ww1.microchip.com/downloads/en/DeviceDoc/21713M.pdf
.. _24AA64: http://ww1.microchip.com/downloads/en/DeviceDoc/21189f.pdf
.. _24AA128: http://ww1.microchip.com/downloads/en/DeviceDoc/21191M.pdf
.. _24AA256: http://ww1.microchip.com/downloads/en/DeviceDoc/21203M.pdf
.. _24AA512: http://ww1.microchip.com/downloads/en/DeviceDoc/21754M.pdf

Notes about 24AA32
..................

This device is declared obsolete by the manufacturer and is not supported.

Only 24AA32A revision is supported.

Supported I2C flash commands
----------------------------

Read
  Read byte sequences of any size, starting at any location from the I2C
  flash device

Write
  Write arbitrary byte sequences of any size, starting at any location to the
  I2C flash device

Dependencies
------------

* Python_ 3.5 or above is required.
* PyFtdi_ 0.42 or above is required.
