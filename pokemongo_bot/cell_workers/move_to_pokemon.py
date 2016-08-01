import time
import requests
from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers.base_task import BaseTask
from utils import distance, format_dist, format_time

class MoveToPokemon(BaseTask):
    def should_run(self):
        return self.bot.config.pokemon_map_use and not self.bot.softban

    def work(self):
        if not self.should_run():
            return WorkerResult.SUCCESS

        nearest_pokemon = self.get_nearest_pokemon()

        if nearest_pokemon == None:
            return WorkerResult.SUCCESS

        lat = nearest_pokemon['latitude']
        lng = nearest_pokemon['longitude']
        pokemonName = nearest_pokemon['pokemon_name']
        unit = self.bot.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            lat,
            lng
        )

        max_travel_time = int(nearest_pokemon['disappear_time'] / 1000) - int(time.time()) - 15
        
        needed_speed = max((dist / max_travel_time), self.bot.config.pokemon_map_min_speed)
        
        secs_since_last_ran = max((int(time.time()) - self.bot.last_ran_mtp_timestamp), 0)
        
        if (needed_speed * 3600 / 1000) < (self.bot.config.pokemon_map_max_speed * 3600 / 1000):
            logger.log('Found {} in PokemonGo-Map. Moving @{} km/h , {} and {} left to get there'.format(pokemonName, (needed_speed * 3600 / 1000), format_dist(dist, unit), format_time(max_travel_time)))

            step_walker = StepWalker(
                self.bot,
                (needed_speed * secs_since_last_ran),
                lat,
                lng
            )
            
            self.bot.running_to_pokemon = True
            
            self.bot.last_ran_mtp_timestamp = int(time.time())

            if not step_walker.step():
                return WorkerResult.RUNNING
        else:
            self.bot.encounter_ids.append(nearest_pokemon['encounter_id'])
            return WorkerResult.SUCCESS 

        if dist > 2:
            logger.log('Taking one last step to reach {}'.format(pokemonName))
            step_walker = StepWalker(
                self.bot,
                (dist - 1),
                lat,
                lng
            )
        
        logger.log('Arrived at {}'.format(pokemonName))
        self.bot.encounter_ids.append(nearest_pokemon['encounter_id'])
        self.bot.running_to_pokemon = False
        
        return WorkerResult.SUCCESS

    def get_nearest_pokemon(self):
        try:
            if len(self.bot.config.pokemon_map_ids) > 0:
                encounters = [x for x in requests.get('http://' + self.bot.config.pokemon_map_host + ':' +
                                            str(self.bot.config.pokemon_map_port) + '/raw_data?ids=' +
                                            self.bot.config.pokemon_map_ids
                                            ).json()['pokemons']]
            else:
                encounters = [x for x in requests.get('http://' + self.bot.config.pokemon_map_host + ':' +
                                            str(self.bot.config.pokemon_map_port) + '/raw_data'
                                            ).json()['pokemons']]
        except requests.exceptions.RequestException as e:
            logger.log('The connection to the PokemonGo-Map server is failing. Probably you forgot to spin it up first')
            return None
        
        # Sort all encounters by distance from current position
        encounters.sort(key=lambda x: distance(
            self.bot.position[0],
            self.bot.position[1],
            x['latitude'],
            x['longitude']
        ))
        
        #remove all the pokemons already caught
        encounters = filter(lambda x: x["encounter_id"] not in self.bot.encounter_ids, encounters)
        
        if len(encounters) > 0:
            return encounters[0]
        else:
            return None