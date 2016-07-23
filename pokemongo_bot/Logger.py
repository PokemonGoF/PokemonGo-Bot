try:
    import lcd
    lcd = lcd.lcd()
    # Change this to your i2c address
    lcd.set_addr(0x23)
except:
    lcd = False

def log(string, color = 'white'):
    colorHex = ''
    if(color == 'green'):
        colorHex = '92m'
    if(color == 'yellow'):
        colorHex = '93m'
    if(colorHex == 'red'):
        colorHex = '91m'
    if colorHex == '':
        print(string)
    else:
        print(u'\033['+ colorHex + string.decode('utf-8') + '\033[0m')
    if lcd:
        if(string):
            lcd.message(string)
