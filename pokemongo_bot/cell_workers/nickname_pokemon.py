from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.inventory import pokemons, Pokemon, Attack


DEFAULT_IGNORE_FAVORITES = False
DEFAULT_GOOD_ATTACK_THRESHOLD = 0.7
DEFAULT_TEMPLATE = '{name}'

MAXIMUM_NICKNAME_LENGTH = 12


class NicknamePokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    """
    Nickname user pokemons according to the specified template


    PARAMETERS:

    dont_nickname_favorite (default: False)
        Prevents renaming of favorited pokemons

    good_attack_threshold (default: 0.7)
        Threshold for perfection of the attack in it's type (0.0-1.0)
         after which attack will be treated as good.
        Used for {fast_attack_char}, {charged_attack_char}, {attack_code}
         templates

    nickname_template (default: '{name}')
        Template for nickname generation.
        Empty template or any resulting in the simple pokemon name
         (e.g. '', '{name}', ...) will revert all pokemon to their original
         names (as if they had no nickname).

        Niantic imposes a 12-character limit on all pokemon nicknames, so
         any new nickname will be truncated to 12 characters if over that limit.
        Thus, it is up to the user to exercise judgment on what template will
         best suit their need with this constraint in mind.

        You can use full force of the Python [Format String syntax](https://docs.python.org/2.7/library/string.html#formatstrings)
        For example, using `{name:.8s}` causes the Pokemon name to never take up
         more than 8 characters in the nickname. This would help guarantee that
         a template like `{name:.8s}_{iv_pct}` never goes over the 12-character
         limit.


    **NOTE:** If you experience frequent `Pokemon not found` error messages,
     this is because the inventory cache has not been updated after a pokemon
     was released. This can be remedied by placing the `NicknamePokemon` task
     above the `TransferPokemon` task in your `config.json` file.


    EXAMPLE CONFIG:
    {
      "type": "NicknamePokemon",
      "config": {
        "enabled": true,
        "dont_nickname_favorite": false,
        "good_attack_threshold": 0.7,
        "nickname_template": "{iv_pct}_{iv_ads}"
      }
    }


    SUPPORTED PATTERN KEYS:

    {name}  Pokemon name      (e.g. Articuno)
    {id}    Pokemon ID/Number (1-151)
    {cp}    Combat Points     (10-4145)

    # Individial Values
    {iv_attack}  Individial Attack (0-15) of the current specific pokemon
    {iv_defense} Individial Defense (0-15) of the current specific pokemon
    {iv_stamina} Individial Stamina (0-15) of the current specific pokemon
    {iv_ads}     Joined IV values (e.g. 4/12/9)
    {iv_sum}     Sum of the Individial Values (0-45)
    {iv_pct}     IV perfection (in 000-100 format - 3 chars)
    {iv_pct2}    IV perfection (in 00-99 format - 2 chars)
                    So 99 is best (it's a 100% perfection)
    {iv_pct1}    IV perfection (in 0-9 format - 1 char)

    # Basic Values of the pokemon (identical for all of one kind)
    {base_attack}   Basic Attack (40-284) of the current pokemon kind
    {base_defense}  Basic Defense (54-242) of the current pokemon kind
    {base_stamina}  Basic Stamina (20-500) of the current pokemon kind
    {base_ads}      Joined Basic Values (e.g. 125/93/314)

    # Final Values of the pokemon (Base Values + Individial Values)
    {attack}        Basic Attack + Individial Attack
    {defense}       Basic Defense + Individial Defense
    {stamina}       Basic Stamina + Individial Stamina
    {sum_ads}       Joined Final Values (e.g. 129/97/321)

    # IV CP perfection - it's a kind of IV perfection percent
    #  but calculated using weight of each IV in its contribution
    #  to CP of the best evolution of current pokemon.
    # So it tends to be more accurate than simple IV perfection.
    {ivcp_pct}      IV CP perfection (in 000-100 format - 3 chars)
    {ivcp_pct2}     IV CP perfection (in 00-99 format - 2 chars)
                        So 99 is best (it's a 100% perfection)
    {ivcp_pct1}     IV CP perfection (in 0-9 format - 1 char)

    # Character codes for fast/charged attack types.
    # If attack is good character is uppecased, otherwise lowercased.
    # Use 'good_attack_threshold' option for customization
    #
    # It's an effective way to represent type with one character.
    #   If first char of the type name is unique - use it,
    #    in other case suitable substitute used
    #
    # Type codes:
    #   Bug: 'B'
    #   Dark: 'K'
    #   Dragon: 'D'
    #   Electric: 'E'
    #   Fairy: 'Y'
    #   Fighting: 'T'
    #   Fire: 'F'
    #   Flying: 'L'
    #   Ghost: 'H'
    #   Grass: 'A'
    #   Ground: 'G'
    #   Ice: 'I'
    #   Normal: 'N'
    #   Poison: 'P'
    #   Psychic: 'C'
    #   Rock: 'R'
    #   Steel: 'S'
    #   Water: 'W'
    #
    {fast_attack_char}      One character code for fast attack type
                                (e.g. 'F' for good Fire or 's' for bad
                                Steel attack)
    {charged_attack_char}   One character code for charged attack type
                                (e.g. 'n' for bad Normal or 'I' for good
                                Ice attack)
    {attack_code}           Joined 2 character code for both attacks
                                (e.g. 'Lh' for pokemon with good Flying
                                and weak Ghost attacks)

    # Moveset perfection percents for attack and for defense
    #  Calculated for current pokemon only, not between all pokemons
    #  So perfect moveset can be weak if pokemon is weak (e.g. Caterpie)
    {attack_pct}   Moveset perfection for attack (in 000-100 format - 3 chars)
    {defense_pct}  Moveset perfection for defense (in 000-100 format - 3 chars)
    {attack_pct2}  Moveset perfection for attack (in 00-99 format - 2 chars)
    {defense_pct2} Moveset perfection for defense (in 00-99 format - 2 chars)
    {attack_pct1}  Moveset perfection for attack (in 0-9 format - 1 char)
    {defense_pct1} Moveset perfection for defense (in 0-9 format - 1 char)

    # Special case: pokemon object.
    # You can access any available pokemon info via it.
    # Examples:
    #   '{pokemon.ivcp:.2%}'             ->  '47.00%'
    #   '{pokemon.fast_attack}'          ->  'Wing Attack'
    #   '{pokemon.fast_attack.type}'     ->  'Flying'
    #   '{pokemon.fast_attack.dps:.2f}'  ->  '10.91'
    #   '{pokemon.fast_attack.dps:.0f}'  ->  '11'
    #   '{pokemon.charged_attack}'       ->  'Ominous Wind'
    {pokemon}   Pokemon instance (see inventory.py for class sources)


    EXAMPLES:

    1. "nickname_template": "{ivcp_pct}_{iv_pct}_{iv_ads}"

    Golbat with IV (attack: 9, defense: 4 and stamina: 8) will result in:
     '48_46_9/4/8'

    2. "nickname_template": "{attack_code}{attack_pct1}{defense_pct1}{ivcp_pct1}{name}"

    Same Golbat (with attacks Wing Attack & Ominous Wind) will have nickname:
     'Lh474Golbat'

    See /tests/nickname_test.py for more examples.
    """

    # noinspection PyAttributeOutsideInit
    def initialize(self):
        self.ignore_favorites = self.config.get(
            'dont_nickname_favorite', DEFAULT_IGNORE_FAVORITES)
        self.good_attack_threshold = self.config.get(
            'good_attack_threshold', DEFAULT_GOOD_ATTACK_THRESHOLD)
        self.template = self.config.get(
            'nickname_template', DEFAULT_TEMPLATE)

    def work(self):
        """
        Iterate over all user pokemons and nickname if needed
        """
        for pokemon in pokemons().all():  # type: Pokemon
            if not pokemon.is_favorite or not self.ignore_favorites:
                self._nickname_pokemon(pokemon)

    def _nickname_pokemon(self, pokemon):
        # type: (Pokemon) -> None
        """
        Nicknaming process
        """

        # We need id of the specific pokemon unstance to be able to rename it
        instance_id = pokemon.id
        if not instance_id:
            self.emit_event(
                'api_error',
                formatted='Failed to get pokemon name, will not rename.'
            )
            return

        # Generate new nickname
        old_nickname = pokemon.nickname
        try:
            new_nickname = self._generate_new_nickname(pokemon, self.template)
        except KeyError as bad_key:
            self.emit_event(
                'config_error',
                formatted="Unable to nickname {} due to bad template ({})"
                          .format(old_nickname, bad_key)
            )
            return

        # Skip if pokemon is already well named
        if pokemon.nickname_raw == new_nickname:
            return

        # Send request
        response = self.bot.api.nickname_pokemon(
            pokemon_id=instance_id, nickname=new_nickname)
        sleep(1.2)  # wait a bit after request

        # Check result
        try:
            result = reduce(dict.__getitem__, ["responses", "NICKNAME_POKEMON"],
                            response)['result']
        except KeyError:
            self.emit_event(
                'api_error',
                formatted='Attempt to nickname received bad response from server.'
            )
            return

        # Nickname unset
        if result == 0:
            self.emit_event(
                'unset_pokemon_nickname',
                formatted="Pokemon {old_name} nickname unset.",
                data={'old_name': old_nickname}
            )
            pokemon.update_nickname(new_nickname)
        elif result == 1:
            self.emit_event(
                'rename_pokemon',
                formatted="Pokemon {old_name} renamed to {current_name}",
                data={'old_name': old_nickname, 'current_name': new_nickname}
            )
            pokemon.update_nickname(new_nickname)
        elif result == 2:
            self.emit_event(
                'pokemon_nickname_invalid',
                formatted="Nickname {nickname} is invalid",
                data={'nickname': new_nickname}
            )
        else:
            self.emit_event(
                'api_error',
                formatted='Attempt to nickname received unexpected result'
                          ' from server ({}).'.format(result)
            )

    def _generate_new_nickname(self, pokemon, template):
        # type: (Pokemon, string) -> string
        """
        New nickname generation
        """

        # Filter template
        template = template.lower().strip()

        # Individial Values of the current specific pokemon (different for each)
        iv_attack = pokemon.iv_attack
        iv_defense = pokemon.iv_defense
        iv_stamina = pokemon.iv_stamina
        iv_list = [iv_attack, iv_defense, iv_stamina]
        iv_sum = sum(iv_list)
        iv_pct = iv_sum / 45.0

        # Basic Values of the pokemon (identical for all of one kind)
        base_attack = pokemon.static.base_attack
        base_defense = pokemon.static.base_defense
        base_stamina = pokemon.static.base_stamina

        # Final Values of the pokemon
        attack = base_attack + iv_attack
        defense = base_defense + iv_defense
        stamina = base_stamina + iv_stamina

        # One character codes for fast/charged attack types
        # If attack is good then character is uppecased, otherwise lowercased
        fast_attack_char = self.attack_char(pokemon.fast_attack)
        charged_attack_char = self.attack_char(pokemon.charged_attack)
        # 2 characters code for both attacks of the pokemon
        attack_code = fast_attack_char + charged_attack_char

        moveset = pokemon.moveset

        #
        # Generate new nickname
        #
        new_name = template.format(
            # Pokemon
            pokemon=pokemon,
            # Pokemon name
            name=pokemon.name,
            # Pokemon ID/Number
            id=int(pokemon.pokemon_id),
            # Combat Points
            cp=int(pokemon.cp),

            # Individial Values of the current specific pokemon
            iv_attack=iv_attack,
            iv_defense=iv_defense,
            iv_stamina=iv_stamina,
            # Joined IV values like: 4/12/9
            iv_ads='/'.join(map(str, iv_list)),
            # Sum of the Individial Values
            iv_sum=iv_sum,
            # IV perfection (in 000-100 format - 3 chars)
            iv_pct="{:03.0f}".format(iv_pct * 100),
            # IV perfection (in 00-99 format - 2 chars)
            #  99 is best (it's a 100% perfection)
            iv_pct2="{:02.0f}".format(iv_pct * 99),
            # IV perfection (in 0-9 format - 1 char)
            #  9 is best (it's a 100% perfection)
            iv_pct1=int(round(iv_pct * 9)),

            # Basic Values of the pokemon (identical for all of one kind)
            base_attack=base_attack,
            base_defense=base_defense,
            base_stamina=base_stamina,
            # Joined Base Values like: 125/93/314
            base_ads='/'.join(map(str, [base_attack, base_defense, base_stamina])),

            # Final Values of the pokemon (Base Values + Individial Values)
            attack=attack,
            defense=defense,
            stamina=stamina,
            # Joined Final Values like: 129/97/321
            sum_ads='/'.join(map(str, [attack, defense, stamina])),

            # IV CP perfection (in 000-100 format - 3 chars)
            # It's a kind of IV perfection percent but calculated
            #  using weight of each IV in its contribution to CP of the best
            #  evolution of current pokemon
            # So it tends to be more accurate than simple IV perfection
            ivcp_pct="{:03.0f}".format(pokemon.ivcp * 100),
            # IV CP perfection (in 00-99 format - 2 chars)
            ivcp_pct2="{:02.0f}".format(pokemon.ivcp * 99),
            # IV CP perfection (in 0-9 format - 1 char)
            ivcp_pct1=int(round(pokemon.ivcp * 9)),

            # One character code for fast attack type
            # If attack is good character is uppecased, otherwise lowercased
            fast_attack_char=fast_attack_char,
            # One character code for charged attack type
            charged_attack_char=charged_attack_char,
            # 2 characters code for both attacks of the pokemon
            attack_code=attack_code,

            # Moveset perfection for attack and for defense (in 000-100 format)
            #  Calculated for current pokemon only, not between all pokemons
            #  So perfect moveset can be weak if pokemon is weak (e.g. Caterpie)
            attack_pct="{:03.0f}".format(moveset.attack_perfection * 100),
            defense_pct="{:03.0f}".format(moveset.defense_perfection * 100),

            # Moveset perfection (in 00-99 format - 2 chars)
            attack_pct2="{:02.0f}".format(moveset.attack_perfection * 99),
            defense_pct2="{:02.0f}".format(moveset.defense_perfection * 99),

            # Moveset perfection (in 0-9 format - 1 char)
            attack_pct1=int(round(moveset.attack_perfection * 9)),
            defense_pct1=int(round(moveset.defense_perfection * 9)),
        )

        # Use empty result for unsetting nickname
        # So original pokemon name will be shown to user
        if new_name == pokemon.name:
            new_name = ''

        # 12 is a max allowed length for the nickname
        return new_name[:MAXIMUM_NICKNAME_LENGTH]

    def attack_char(self, attack):
        # type: (Attack) -> string
        """
        One character code for attack type
        If attack is good then character is uppecased, otherwise lowercased

        Type codes:

        Bug: 'B'
        Dark: 'K'
        Dragon: 'D'
        Electric: 'E'
        Fairy: 'Y'
        Fighting: 'T'
        Fire: 'F'
        Flying: 'L'
        Ghost: 'H'
        Grass: 'A'
        Ground: 'G'
        Ice: 'I'
        Normal: 'N'
        Poison: 'P'
        Psychic: 'C'
        Rock: 'R'
        Steel: 'S'
        Water: 'W'

        it's an effective way to represent type with one character
        if first char is unique - use it, in other case suitable substitute used
        """
        char = attack.type.as_one_char.upper()
        if attack.rate_in_type < self.good_attack_threshold:
            char = char.lower()
        return char
