import time
import sys
try:
    import lcd
    lcd = lcd.lcd()
    # Change this to your i2c address
    lcd.set_addr(0x23)
except Exception:
    lcd = False

def log(string, color = 'white'):
	# Write bot output also in a log file
	try:
		logs_file = open('logs/' + time.strftime("%Y%m%d") + '.txt', 'a')
		logs_file.write('[' + time.strftime("%H:%M:%S") + '] ' + string + '\n')
		logs_file.close()
	except:
		print "Unknown error while writing logs file!"
    
	colorHex = {
        'red': '91m',
        'green': '92m',
        'yellow': '93m',
        'blue': '94m',
        'cyan': '96m'
    }
	if color not in colorHex:
		print('[' + time.strftime("%H:%M:%S") + '] '+ string)
	else:
		print('[' + time.strftime("%H:%M:%S") + '] ' + u'\033['+ colorHex[color] + string.decode('utf-8') + '\033[0m')
	if lcd:
		if(string):
			lcd.message(string)
