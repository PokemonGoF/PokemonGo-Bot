from __future__ import unicode_literals
import time
from datetime import date

try:
    import lcd
    lcd = lcd.lcd()
    # Change this to your i2c address
    lcd.set_addr(0x23)
except Exception:
    lcd = False


logger_format = '[{day} {time}] {message}'


def log(message, color='white'):
    color2hex = {
        'red': '91m',
        'green': '92m',
        'yellow': '93m',
        'blue': '94m',
        'cyan': '96m'
    }

    today = date.today().strftime('%Y-%m-%d')
    now = time.strftime("%H:%M:%S")
    message = message.decode('utf-8')

    if color in color2hex:
        colored_message = u'\033[%s%s\033[0m' % (color2hex[color], message)
        formatted_message = logger_format.format(message=colored_message,
                                                 day=today,
                                                 time=now)
        print(formatted_message)
    else:
        formatted_message = logger_format.format(message=message,
                                                 day=today,
                                                 time=now)
        print(formatted_message)

    if lcd and message:
        lcd.message(message)
