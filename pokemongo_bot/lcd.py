# -*- coding: utf-8 -*-
"""
Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
Made available under GNU GENERAL PUBLIC LICENSE
# Modified Python I2C library for Raspberry Pi
# as found on http://www.recantha.co.uk/blog/?p=4849
# Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
# added bits and pieces from various sources
# By DenisFromHR (Denis Pleic)
# 2015-02-10, ver 0.1
"""
import os
from itertools import islice
from time import *

# This import is NOT available on Mac OS X, check for ARM OS before loading
if (os.name()).lower() == 'arm':
    import smbus


class i2c_device:
    def __init__(self, addr, port=1):
        self.addr = addr
        self.bus = smbus.SMBus(port)

    # Write a single command
    def write_cmd(self, cmd):
        self.bus.write_byte(self.addr, cmd)
        sleep(0.0001)

    # Write a command and argument
    def write_cmd_arg(self, cmd, data):
        self.bus.write_byte_data(self.addr, cmd, data)
        sleep(0.0001)

    # Write a block of data
    def write_block_data(self, cmd, data):
        self.bus.write_block_data(self.addr, cmd, data)
        sleep(0.0001)

    # Read a single byte
    def read(self):
        return self.bus.read_byte(self.addr)

    # Read
    def read_data(self, cmd):
        return self.bus.read_byte_data(self.addr, cmd)

    # Read a block of data
    def read_block_data(self, cmd):
        return self.bus.read_block_data(self.addr, cmd)


# LCD Address
# ADDRESS = 0x27
LCD_WIDTH = 20
LCD_HEIGHT = 2
LCD_CHARS = [0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70, 0x78]  # Address position for custom chars
# Use char generator here: https://omerk.github.io/lcdchargen/ or http://www.quinapalus.com/hd44780udg.html
# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit


class lcd:
    # initializes objects and lcd
    # def __init__(self, adress):

    def set_addr(self, adress):
        self.lcd_device = i2c_device(adress)

        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x02)

        self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS |
                       LCD_4BITMODE)
        self.displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_BLINKOFF)
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)

    def show_cursor(self, show):
        """Show or hide the cursor.  Cursor is shown if show is True."""
        if show:
            self.displaycontrol |= LCD_CURSORON
        else:
            self.displaycontrol &= ~LCD_CURSORON
        self.lcd_write(LCD_DISPLAYCONTROL | self.displaycontrol)

    def blink(self, blink):
        """Turn on or off cursor blinking.  Set blink to True to enable blinking."""
        if blink:
            self.displaycontrol |= LCD_BLINKON
        else:
            self.displaycontrol &= ~LCD_BLINKON
        self.lcd_write(LCD_DISPLAYCONTROL | self.displaycontrol)

    # clocks EN to latch command
    def lcd_strobe(self, data):
        self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
        sleep(.0005)
        self.lcd_device.write_cmd(((data & ~En) | LCD_BACKLIGHT))
        sleep(.0001)

    def lcd_write_four_bits(self, data):
        self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
        self.lcd_strobe(data)

    # write a command to lcd
    def lcd_write(self, cmd, mode=0):
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # write a character to lcd (or character rom) 0x09: backlight | RS=DR<
    # works!
    def lcd_write_char(self, charvalue, mode=1):
        self.lcd_write_four_bits(mode | (charvalue & 0xF0))
        self.lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))

    def message(self, message, style=1, speed=1):
        """Send a message to the display, use \n for new line"""
        # style=1 Left justified
        # style=2 Centred
        # style=3 Right justified
        # style=4 typing

        self.clear()
        words = iter(message.split())
        lines, current = [], next(words)
        for word in words:
            if len(current) + 1 + len(word) > LCD_WIDTH:
                lines.append(current)
                current = word
            else:
                current += " " + word
        lines.append(current)

        for (idx, line) in enumerate(lines):
            if idx == 0:
                self.lcd_write(0x80)
            if idx == 1:
                self.lcd_write(0xC0)
            if idx == 2:
                self.lcd_write(0x94)
            if idx == 3:
                self.lcd_write(0xD4)

            for char in line:
                self.lcd_write(ord(char), Rs)

    def type_string(self, message, line, speed=0.3, style=1, blink=True):
        """Type like a type machine"""
        # style=1 Left justified
        # style=2 Centred
        # style=3 Right justified

        if line == 1:
            self.lcd_write(0x80)
        if line == 2:
            self.lcd_write(0xC0)
        if line == 3:
            self.lcd_write(0x94)
        if line == 4:
            self.lcd_write(0xD4)
        if style == 0x01:
            message = message.ljust(LCD_WIDTH, '')
        elif style == 0x02:
            message = message.center(LCD_WIDTH, '')
        elif style == 3:
            message = message.rjust(LCD_WIDTH, '')

        for i in range(len(message)):
            self.lcd_write(ord(message[i]), Rs)
            sleep(speed)

    def split_every(self, n, iterable):
        i = iter(iterable)
        piece = list(islice(i, n))
        while piece:
            yield piece
            piece = list(islice(i, n))

    def filler(self, str1, str2):
        len1 = len(str1)
        len2 = len(str2)
        left = LCD_WIDTH - len1 - len2
        fill = ' ' * left
        return str1 + fill + str2

    # put string function
    def write_line(self, string, line, style=1):
        if line == 1:
            self.lcd_write(0x80)
        if line == 2:
            self.lcd_write(0xC0)
        if line == 3:
            self.lcd_write(0x94)
        if line == 4:
            self.lcd_write(0xD4)

        if style == 0x01:
            string = string.ljust(LCD_WIDTH, ' ')
        elif style == 0x02:
            string = string.center(LCD_WIDTH, ' ')
        elif style == 3:
            string = string.rjust(LCD_WIDTH, ' ')

        for char in string:
            self.lcd_write(ord(char), Rs)

    # clear lcd and set to home
    def clear(self):
        self.lcd_clear()

    def lcd_clear(self):
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_RETURNHOME)

    # define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)
    def backlight(self, state):  # for state, 1 = on, 0 = off
        if state == 1:
            self.lcd_device.write_cmd(LCD_BACKLIGHT)
        elif state == 0:
            self.lcd_device.write_cmd(LCD_NOBACKLIGHT)

    # add custom characters (0 - 7)
    def createChar(self, charPos, charDef):
        self.lcd_write(LCD_CHARS[charPos], 0)
        for line in charDef:
            self.lcd_write(line, 1)

    def lcd_display_string_pos(self, string, line, pos):
        if line == 1:
            pos_new = pos
        elif line == 2:
            pos_new = 0x40 + pos
        elif line == 3:
            pos_new = 0x14 + pos
        elif line == 4:
            pos_new = 0x54 + pos

        self.lcd_write(0x80 + pos_new)

        for char in string:
            self.lcd_write(ord(char), Rs)
