import time

try:
    import lcd
    lcd = lcd.lcd()
    # Change this to your i2c address
    lcd.set_addr(0x23)
except Exception:
    lcd = False


def log(string, color='white'):
    try:
        string = string.decode('utf8')
    except UnicodeEncodeError:
        pass
    
    color_hex = {
        'red': '91m',
        'green': '92m',
        'yellow': '93m',
        'blue': '94m',
        'cyan': '96m'
    }
    if color not in color_hex:
        print('[' + time.strftime("%H:%M:%S") + '] ' + string)
    else:
        print('[' + time.strftime("%H:%M:%S") + '] ' + '\033[' + color_hex[color] + string + '\033[0m')
    if lcd:
        if string:
            lcd.message(string)
