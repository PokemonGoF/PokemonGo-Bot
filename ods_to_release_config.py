#v1.0 Witzbold script to configure release_config. 

from pyexcel_ods import get_data

data = get_data("release_config.ods")
catchlist = data['Sheet1']
configfile = open('release_config.json', 'w')


def initConfig():
    #writing standard stuff from example to config
    configfile.write(''+
    '{\n'+
    '    "any": {\n'+
    '        "release_under_cp": 0,\n'+
    '        "release_under_iv": 0,\n'+
    '        "cp_iv_logic": "or"\n'+
    '    },\n'+
    '\n'+
    '    "My Pokemon": {\n'+
    '        "release_under_cp": 0,\n'+
    '        "release_under_iv": 0,\n'+
    '        "cp_iv_logic": "or"\n'+
    '    },\n\n')

def finishConfig():
    configfile.write(''+
    '    "exceptions": {\n'
    '            "always_capture": [\n'+
    '                "Arcanine",\n'+
    '                "Lapras",\n'+
    '                "Dragonite",\n'+
    '                "Snorlax",\n'+
    '                "Blastoise",\n'+
    '                "Moltres",\n'+
    '                "Articuno",\n'+
    '                "Zapdos",\n'+
    '                "Mew",\n'+
    '                "Mewtwo"\n'+
    '            ]\n'+
    '        }\n'+
    '    }')

def appendConfig(Pokemon, cp):
    #appending config with pokemon and CP, IV is always 0
    configfile.write(''+
    '    "%s":{\n' % Pokemon+
    '        "release_under_cp": %i,\n' % cp+
    '        "release_under_iv": 0,\n' +
    '        "cp_iv_logic": "or"},\n\n' ) #needed since IV=0


def main():
    initConfig()

    for line in catchlist[2:]:
        appendConfig(line[1], int(line[2]))
        line[1]
        print int(line[2])

    finishConfig()


if __name__ == "__main__":
    main()
