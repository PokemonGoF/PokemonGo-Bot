class StatisticsKeeper(object):
    """
    Object to keep runtime stats while PokemonGo-bot is running.
    """

    def __init__(self, distance_unit="km"):

        ## Walking Stags ##
        # noinspection SpellCheckingInspection
        self.visited_pokestops = 0
        self.distance_walked = 0
        self.distance_units = distance_unit

        ### Pokemon Caught Stats ##
        self.pokemon_encountered = 0
        self.pokemon_caught = 0
        # This is a dictionary of form,
        # pokemon_name : number_caught
        self.pokemon_caught = {
        }


    def increment_caught_pokemon(self, pokemon_type):
        """
        Tally a caught pokemon.
        Args:
            pokemon_type: Name of pokemon caught.

        Returns: None
        """
        if not self.pokemon_caught.has_key(pokemon_type):
            self.pokemon_caught[pokemon_type] = 0

        self.pokemon_caught[pokemon_type] += 1

    def __str__(self):
        """
        ToString method used for displaying final summary upon program exit.
        Returns: string
        """
        # noinspection SpellCheckingInspection
        return ("Pokestops visited: {pokestops}\n" + \
                "Distance walked: {distance} {distance_units}\n" + \
                "Pokemon caught: {pokemon}" \
                ).format(pokestops=self.visited_pokestops,
                         distance=round(self.distance_walked, 2),
                         distance_units=self.distance_units,
                         pokemon=self.pokemon_caught)
