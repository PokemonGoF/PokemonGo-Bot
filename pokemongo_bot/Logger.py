

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
