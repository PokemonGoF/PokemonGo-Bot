import time

try:
    import lcd
    lcd = lcd.lcd()
    # Change this to your i2c address
    lcd.set_addr(0x23)
except Exception:
    lcd = False


def log(string, color='white'):
    decoded_string = string.decode('utf-8')
    color_hex = {
        'red': '91m',
        'green': '92m',
        'yellow': '93m',
        'blue': '94m',
        'cyan': '96m'
    }
    if color not in color_hex:
        print('[' + time.strftime("%H:%M:%S") + '] ' + decoded_string)
    else:
        print('[' + time.strftime("%H:%M:%S") + '] ' + u'\033[' + color_hex[color] + decoded_string + '\033[0m')
    if lcd:
        if decoded_string:
            lcd.message(decoded_string)
