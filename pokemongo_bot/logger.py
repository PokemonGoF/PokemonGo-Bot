import time
from datetime import date

try:
    import lcd
    lcd = lcd.lcd()
    # Change this to your i2c address
    lcd.set_addr(0x23)
except Exception:
    lcd = False

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
    log_format = '[%s %s] %s'

    if color not in color2hex:
        print(log_format % (today, now, message))
    else:
        colored_message = u'\033[' + color2hex[color] + message.decode('utf-8') + '\033[0m'
        print(log_format % (today, now, colored_message))
    if lcd:
        if message:
            lcd.message(message)
