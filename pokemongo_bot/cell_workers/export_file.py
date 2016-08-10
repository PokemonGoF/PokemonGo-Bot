import os
import io
import csv

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.base_dir import _base_dir

def csv_export(payload):
    out = io.BytesIO()
    writer = csv.writer(out)
    writer.writerow(['username', payload['username']])
    writer.writerow(['stardust', payload['stardust']])
    writer.writerow(['pokecoin', payload['pokecoin']])
    writer.writerow(['team', payload['team']])
    writer.writerow([])
    writer.writerow(['items'])
    for item, count in payload['inventory'].iteritems():
        writer.writerow([item, count])
    writer.writerow([])
    writer.writerow(['pokemons'])
    pokekeys = list(payload['pokemon_keys'])
    writer.writerow(pokekeys)
    for pokemon in payload['pokemons']:
        temp = []
        for key in pokekeys:
            temp.append(pokemon.get(key, ''));
        writer.writerow(temp)

    return out.getvalue()

class ExportFile(BaseTask):
    """
        Exports files with useful infos.

        Events: file_exported
    """
    SUPPORTED_TASK_API_VERSION = 1

    exporters = {
        'csv_export': csv_export
    }

    def initialize(self):
        self.export_extension = self.config.get('file_type', 'csv')

        self.turn = -1

        self.data = {};
        self.payload = {}
        self.text = ''
        self.pokemon_keys = set()

        if self.config.get('relative_path', False):
            self.file_path = os.path.join(_base_dir, self.config['relative_path'])
        elif self.config.get('absolute_path', False):
            self.file_path = self.config['absolute_path']
        else:
            self.file_path = os.path.join(_base_dir, 'export.{}'.format(self.export_extension))

    def work(self):
        self.turn += 1
        if self.turn % 25 != 0:
            return

        def mapper(pokemon):
            for k, v in pokemon.iteritems():
                self.pokemon_keys.add(k)
            return pokemon

        self._gatherData()

        self.payload = {
            'pokemons': map(mapper, self.data['pokemons']),
            'pokemon_keys': self.pokemon_keys,
            'stardust': self.data['stardust'],
            'pokecoin': self.data['pokecoin'],
            'username': self.data['username'],
            'team': self.data['team'],
            'inventory': dict(zip(map(lambda x: self.bot.item_list[str(x['item_id'])], self.data['items']), map(lambda x: x.get('count', 0), self.data['items'])))
        }

        self._export();
        self._write();
        self.emit_event(
            'file_exported',
            formatted='{} file exported to {}'.format(self.export_extension, self.file_path)
        )

    def _gatherData(self):
        inventory_response = self.bot.api.get_inventory()['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        self.data = {
            'pokemons': map(lambda x: x['inventory_item_data']['pokemon_data'], filter(lambda x: x['inventory_item_data'].get('pokemon_data', False), inventory_response)),
            'items': map(lambda x: x['inventory_item_data']['item'], filter(lambda x: x['inventory_item_data'].get('item', False), inventory_response)),
            'stardust': self.bot._player['currencies'][1].get('amount', 0),
            'pokecoin': self.bot._player['currencies'][0].get('amount', 0),
            'username': self.bot._player['username'],
            'team': self.bot._player['team']
        }

    def _export(self):
        self.text = self.exporters['{}_export'.format(self.export_extension)](self.payload)

    def _write(self):
        f = open(self.file_path, 'w+')
        f.write(self.text)
        f.truncate()
        f.close()
