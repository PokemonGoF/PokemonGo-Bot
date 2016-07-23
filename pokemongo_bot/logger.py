import time
try:
    import lcd
    lcd = lcd.lcd()
    # Change this to your i2c address
    lcd.set_addr(0x23)
except:
    lcd = False

def log(string, color = 'white'):
    colorHex = {
        'green': '92m',
        'yellow': '93m',
        'red': '91m'
    }
    if color not in colorHex:
        print('[' + time.strftime("%Y-%m-%d %H:%M:%S") + '] '+ string)
    else:
        print(u'\033['+ colorHex[color] + time.strftime("%Y-%m-%d %H:%M:%S") + ' ' + string.decode('utf-8') + '\033[0m')
    if lcd:
        if(string):
            lcd.message(string)
