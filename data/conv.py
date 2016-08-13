def toJson(arg):
    if '[]' == arg:
        return []
    elif 'True' == arg:
        return 'true'
    elif 'False' == arg:
        return 'false'
    elif ''

for line in open('confpart.dat'):
    line = line.strip()
    if 'long_flag' == line[:9]:
        val = line.split('=')[1].strip()
        if len(val) and val[-1] == ',':
            val = val[:-1]
        print val
    if 'short_flag' == line[:10]:
        val = line.split('=')[1].strip()
        if len(val) and val[-1] == ',':
            val = val[:-1]
        print val
    elif 'help' == line[:4]:
        val = line.split('=')[1].strip()
        if len(val) and val[-1] == ',':
            val = val[:-1]
        print val
    elif 'type' == line[:4]:
        val = line.split('=')[1].strip()
        if len(val) and val[-1] == ',':
            val = val[:-1]
        print val
    elif 'default' == line[:7]:
        val = line.split('=')[1].strip()
        if len(val) and val[-1] == ',':
            val = val[:-1]
        print val
        print ''

