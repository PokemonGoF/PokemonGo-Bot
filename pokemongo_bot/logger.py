from __future__ import unicode_literals
import time

try:
    import lcd
    lcd = lcd.lcd()
    # Change this to your i2c address
    lcd.set_addr(0x23)
except Exception:
    lcd = False


def log(string, color='none'):
    color_hex = {
        'red': '91m',
        'green': '92m',
        'yellow': '93m',
        'blue': '94m',
        'purple': '95m',
        'cyan': '96m',
        'white': '97m'
    }
    if color not in color_hex:
        print('[{time}] {string}'.format(
            time=time.strftime("%H:%M:%S"),
            string=string.decode('utf-8')
        ))
    else:
        print(
            '[{time}] \033[{color} {string} \033[0m'.format(
                time=time.strftime("%H:%M:%S"),
                color=color_hex[color],
                string=string.decode('utf-8')
            )
        )
    if lcd:
        if string:
            lcd.message(string)
