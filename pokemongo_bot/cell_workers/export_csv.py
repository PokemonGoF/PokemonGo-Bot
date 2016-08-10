import copy
import os
import io
import csv

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.base_dir import _base_dir

def csv_export(data):
    out = io.BytesIO()
    writer = csv.writer(out)
    writer.writerow(['username', data['username']])
    writer.writerow(['stardust', data['stardust']])
    writer.writerow(['pokecoin', data['pokecoin']])
    writer.writerow(['team', data['team']])
    writer.writerow([])
    writer.writerow(['items'])
    for item, count in data['inventory'].iteritems():
        writer.writerow([item, count])
    writer.writerow([])
    writer.writerow(['pokemons'])
    pokekeys = list(data['pokemon_keys'])
    writer.writerow(pokekeys)
    for pokemon in data['pokemons']:
        temp = []
        for key in pokekeys:
            temp.append(pokemon.get(key, ''));
        writer.writerow(temp)

    return out.getvalue()

class ExportCsv(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    export_extension = 0
    file_path = 0

    data = 0
    text = ''
    exporters = {
        'csv_export': csv_export
    }

    pokemon_keys = set()

    def initialize(self):
        self.export_extension = self.config.get('file_type', 'csv')

        if self.config.get('relative_path', False):
            self.file_path = os.path.join(_base_dir, self.config['relative_path'])
        elif self.config.get('absolute_path', False):
            self.file_path = self.config['absolute_path']
        else:
            self.file_path = os.path.join(_base_dir, 'export.{}'.format(self.export_extension))

    def work(self):
        def mapper(pokemon):
            pokemon = copy.deepcopy(pokemon)
            if pokemon.get('Fast Attack(s)', False): pokemon['Fast Attack(s)'] = ' / '.join(pokemon['Fast Attack(s)'])
            if pokemon.get('Special Attack(s)', False): pokemon['Special Attack(s)'] = ' / '.join(pokemon['Special Attack(s)'])
            if pokemon.get('Weaknesses', False): pokemon['Weaknesses'] = ' / '.join(pokemon['Weaknesses'])
            if pokemon.get('Type I', False): pokemon['Type I'] = ' / '.join(pokemon['Type I'])
            if pokemon.get('Type II', False): pokemon['Type II'] = ' / '.join(pokemon['Type II'])
            pokemon.pop('Next Evolution Requirements', None)
            if pokemon.get('Previous evolution(s)', False): pokemon['Previous evolution(s)'] = ' / '.join(map(lambda v: v['Name'], pokemon['Previous evolution(s)']))
            if pokemon.get('Next evolution(s)', False): pokemon['Next evolution(s)'] = ' / '.join(map(lambda v: v['Name'], pokemon['Next evolution(s)']))

            for k, v in pokemon.iteritems():
                self.pokemon_keys.add(k)
            return pokemon

        self.data = {
            'pokemons': map(mapper, self.bot.pokemon_list),
            'pokemon_keys': self.pokemon_keys,
            'stardust': self.bot._player['currencies'][1].get('amount', 0),
            'pokecoin': self.bot._player['currencies'][0].get('amount', 0),
            'username': self.bot._player['username'],
            'team': self.bot._player['team'],
            'inventory': dict(zip(map(lambda x: self.bot.item_list[str(x['item_id'])], self.bot.inventory), map(lambda x: x['count'], self.bot.inventory)))
        }

        self._export();

    def _export(self):
        self.text = self.exporters['{}_export'.format(self.export_extension)](self.data)
        self._write();

    def _write(self):
        f = open(self.file_path, 'w+')
        f.write(self.text)
        f.truncate()
        f.close()
