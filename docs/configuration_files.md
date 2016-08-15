## Usage (up-to-date)
  1. copy `config.json.example` to `config.json`.
  2. Edit `config.json` and replace `auth_service`, `username`, `password`, `location` and `gmapkey` with your parameters (other keys are optional, check `Advance Configuration` below)
  3. Simply launch the script with : `./run.sh` or `./pokecli.py` or `python pokecli.py -cf ./configs/config.json` if you want to specify a config file

## Advanced Configuration
|      Parameter     | Default |                                                                                         Description                                                                                         |
|------------------|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tasks`            | []     | The behaviors you want the bot to do. Read [how to configure tasks](#configuring-tasks).
| `max_steps`        | 5       | The steps around your initial location (DEFAULT 5 mean 25 cells around your location) that will be explored
| `forts.avoid_circles`             | False     | Set whether the bot should avoid circles |
| `forts.max_circle_size`             | 10     | How many forts to keep in ignore list |
| `walk`             | 4.16    | Set the distance (in meters) covered by a step when moving.|
| `action_wait_min`   | 1       | Set the minimum time setting for anti-ban time randomizer
| `action_wait_max`   | 4       | Set the maximum time setting for anti-ban time randomizer
| `debug`            | false   | Let the default value here except if you are developer                                                                                                                                      |
| `test`             | false   | Let the default value here except if you are developer                                                                                                                                      |                                                                                       |
| `location_cache`   | true    | Bot will start at last known location if you do not have location set in the config                                                                                                         |
| `distance_unit`    | km      | Set the unit to display distance in (km for kilometers, mi for miles, ft for feet)                                                                                                          |
| `evolve_cp_min`           | 300   |                   Min. CP for evolve_all function

## Configuring Tasks
The behaviors of the bot are configured via the `tasks` key in the `config.json`. This enables you to list what you want the bot to do and change the priority of those tasks by reordering them in the list. This list of tasks is run repeatedly and in order. For more information on why we are moving config to this format, check out the [original proposal](https://github.com/PokemonGoF/PokemonGo-Bot/issues/142).

### Task Options:
* CatchLuredPokemon
* CatchVisiblePokemon
* EvolvePokemon
  * `evolve_all`: Default `NONE` | Set to `"all"` to evolve Pokémon if possible when the bot starts. Can also be set to individual Pokémon as well as multiple separated by a comma. e.g "Pidgey,Rattata,Weedle,Zubat"
  * `evolve_speed`: Default `20`
  * `use_lucky_egg`: Default: `False`
* FollowPath
  * `path_mode`: Default `loop` | Set the mode for the path navigator (loop or linear).
  * `path_file`: Default `NONE` | Set the file containing the waypoints for the path navigator.
* FollowSpiral
* HandleSoftBan
* IncubateEggs
  * `longer_eggs_first`: Default `True`
* MoveToFort
* [MoveToMapPokemon](#sniping-movetolocation)
* NicknamePokemon
  * `nickname_template`: Default `""` | See the [Pokemon Nicknaming](#pokemon-nicknaming) section for more details
  * `dont_nickname_favorite`: Default `false` | Prevents renaming of favorited pokemons
  * `good_attack_threshold`: Default `0.7` | Threshold for perfection of the attack in it's type *(0.0-1.0)* after which attack will be treated as good.<br>Used for `{fast_attack_char}`, `{charged_attack_char}`, `{attack_code}`  templates
* RecycleItems

  > **NOTE:** It's highly recommended to put this task before MoveToFort and SpinFort tasks. This way you'll most likely be able to loot.
  * `min_empty_space`: Default `6` | Minimum empty space to keep in inventory. Once the inventory has less empty space than that amount, the recycling process is triggered. Set it to the inventory size to trigger it at every tick.
  * `item_filter`: Pass a list of unwanted [items (using their JSON codes or names)](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Item-ID's) to recycle.
  * `max_balls_keep`: Default `None` | Maximum amount of balls to keep in inventory
  * `max_potions_keep`: Default `None` | Maximum amount of potions to keep in inventory
  * `max_berries_keep`: Default `None` | Maximum amount of berries to keep in inventory
  * `max_revives_keep`: Default `None` | Maximum amount of revives to keep in inventory
* SpinFort
* TransferPokemon

### Example configuration:
The following configuration tells the bot to transfer all the Pokemon that match the transfer configuration rules, then recycle the items that match its configuration, then catch the pokemon that it can, so on, so forth. Note the last two tasks, MoveToFort and FollowSpiral. When a task is still in progress, it won't run the next things in the list. So it will move towards the fort, on each step running through the list of tasks again. Only when it arrives at the fort and there are no other stops available for it to move towards will it continue to the next step and follow the spiral.

```
{
  // ...
  "tasks": [
    {
      "type": "TransferPokemon"
    },
    {
      "type": "RecycleItems"
    },
    {
      "type": "CatchVisiblePokemon"
    },
    {
      "type": "CatchLuredPokemon"
    },
    {
      "type": "SpinFort"
    },
    {
      "type": "MoveToFort"
    },
    {
      "type": "FollowSpiral"
    }
  ]
  // ...
}
```

### Specifying configuration for tasks
If you want to configure a given task, you can pass values like this:

```
{
  // ...
  "tasks": [
    {
      "type": "IncubateEggs",
      "config": {
        "longer_eggs_first": true
      }
    }
  ]
  // ...
}
```

### An example task configuration if you only wanted to collect items from forts:
```
{
  // ...
  "tasks": [
    {
      "type": "RecycleItems"
    },
    {
      "type": "SpinFortWorker"
    },
    {
      "type": "MoveToFortWorker"
    }
  ],
  // ...
}
```

## Catch Configuration
Default configuration will capture all Pokémon.

```"any": {"catch_above_cp": 0, "catch_above_iv": 0, "logic": "or"}```

You can override the global configuration with Pokémon-specific options, such as:

```"Pidgey": {"catch_above_cp": 0, "catch_above_iv": 0.8", "logic": "and"}``` to only capture Pidgey with a good roll.

Additionally, you can specify always_capture and never_capture flags.

For example: ```"Pidgey": {"never_capture": true}``` will stop catching Pidgey entirely.

## Release Configuration

### Common configuration

Default configuration will not release any Pokémon.

```"release": {"any": {"release_below_cp": 0, "release_below_iv": 0, "logic": "or"}}```

You can override the global configuration with Pokémon-specific options, such as:

```"release": {"Pidgey": {"release_below_cp": 0, "release_below_iv": 0.8, "logic": "or"}}``` to only release Pidgey with bad rolls.

Additionally, you can specify always_release and never_release flags. For example:

```"release": {"Pidgey": {"always_release": true}}``` will release all Pidgey caught.

### Keep the strongest pokemon configuration (dev branch)

You can set ```"release": {"Pidgey": {"keep_best_cp": 1}}``` or ```"release": {"any": {"keep_best_iv": 1}}```.

In that case after each capture bot will check that do you have a new Pokémon or not.

If you don't have it, it will keep it (no matter was it strong or weak Pokémon).

If you already have it, it will keep a stronger version and will transfer the a weaker one.

```"release": {"any": {"keep_best_cp": 2}}```, ```"release": {"any": {"keep_best_cp": 10}}``` - can be any number.

## Evolve All Configuration

By setting the `evolve_all` attribute in config.json, you can instruct the bot to automatically
evolve specified Pokémon on startup. This is especially useful for batch-evolving after popping up
a lucky egg (currently this needs to be done manually).

The evolve all mechanism evolves only higher IV/CP Pokémon. It works by sorting the high CP Pokémon (default: 300 CP or higher)
based on their IV values. After evolving all high CP Pokémon, the mechanism will move on to evolving lower CP Pokémon
only based on their CP (if it can).
It will also automatically transfer the evolved Pokémon based on the release configuration.

Examples on how to use (set in config.json):

1. "evolve_all": "all"
  Will evolve ALL Pokémon.

2. "evolve_all": "Pidgey,Weedle"
  Will only evolve Pidgey and Weedle.

3. Not setting evolve_all or having any other string would not evolve any Pokémon on startup.

If you wish to change the default threshold of 300 CP, simply add the following to the config file:

```
"evolve_cp_min":  <number>
```

## Path Navigator Configuration

Setting the `navigator.type` setting to `path` allows you to specify waypoints which the bot will follow. The waypoints can be loaded from a GPX or JSON file. By default the bot will walk along all specified waypoints and then move directly to the first waypoint again. When setting `navigator.path_mode` to `linear`, the bot will turn around at the last waypoint and along the given waypoints in reverse order.

An example for a JSON file can be found in `configs/path.example.json`. GPX files can be exported from many online tools, such as gpsies.com.The bot loads the first segment of the first track.

## Pokemon Nicknaming

A `nickname_template` can be specified for the `NicknamePokemon` task to allow a nickname template to be applied to all pokemon in the user's inventory. For example, a user wanting all their pokemon to have their IV values as their nickname could use a template `{iv_ads}`, which will cause their pokemon to be named something like `13/7/12` (depending on the pokemon's actual IVs).

The `NicknamePokemon` task will rename all pokemon in inventory on startup to match the given template and will rename any newly caught/hatched/evolved pokemon as the bot runs. _It may take one or two "ticks" after catching/hatching/evolving a pokemon for it to be renamed. This is intended behavior._

> **NOTE:** If you experience frequent `Pokemon not found` error messages, this is because the inventory cache has not been updated after a pokemon was released. This can be remedied by placing the `NicknamePokemon` task above the `TransferPokemon` task in your `config.json` file.

Niantic imposes a 12-character limit on all pokemon nicknames, so any new nickname will be truncated to 12 characters if over that limit. Thus, it is up to the user to exercise judgment on what template will best suit their need with this constraint in mind.

Because some pokemon have very long names, you can use the [Format String syntax](https://docs.python.org/2.7/library/string.html#formatstrings) to ensure that your names do not cause your templates to truncate. For example, using `{name:.8s}` causes the Pokemon name to never take up more than 8 characters in the nickname. This would help guarantee that a template like `{name:.8s}_{iv_pct}` never goes over the 12-character limit.

### Config options

* `enable` (default: `true`): To enable or disable this task.
* `nickname_template` (default: `{name}`): The template to rename the pokemon.
* `dont_nickname_favorite` (default: `false`): Prevents renaming of favorited pokemons.
* `good_attack_threshold` (default: `0.7`): Threshold for perfection of the attack in it's type (0.0-1.0) after which attack will be treated as good. Used for {fast_attack_char}, {charged_attack_char}, {attack_code} templates.
* `locale` (default: `en`): The locale to use for the pokemon name.

### Valid names in templates

Key | Info
---- | ----
**{name}** |  Pokemon name     *(e.g. Articuno)*
**{id}**  |  Pokemon ID/Number *(1-151, e.g. 1 for Bulbasaurs)*
**{cp}**  |  Pokemon's Combat Points (CP)    *(10-4145)*
 | **Individial Values (IV)**
**{iv_attack}**  |  Individial Attack *(0-15)* of the current specific pokemon
**{iv_defense}** |  Individial Defense *(0-15)* of the current specific pokemon
**{iv_stamina}** |  Individial Stamina *(0-15)* of the current specific pokemon
**{iv_ads}**     |  Joined IV values in `(attack)/(defense)/(stamina)` format (*e.g. 4/12/9*, matches web UI format -- A/D/S)
**{iv_ads_hex}** |  Joined IV values of `(attack)(defense)(stamina)` in HEX (*e.g. 4C9* for A/D/S = 4/12/9)
**{iv_sum}**     |  Sum of the Individial Values *(0-45, e.g. 45 when 3 perfect 15 IVs)*
 |  **Basic Values of the pokemon (identical for all of one kind)**
**{base_attack}**   |  Basic Attack *(40-284)* of the current pokemon kind
**{base_defense}**  |  Basic Defense *(54-242)* of the current pokemon kind
**{base_stamina}**  |  Basic Stamina *(20-500)* of the current pokemon kind
**{base_ads}**      |  Joined Basic Values *(e.g. 125/93/314)*
 |  **Final Values of the pokemon (Base Values + Individial Values)**
**{attack}**        |  Basic Attack + Individial Attack
**{defense}**       |  Basic Defense + Individial Defense
**{stamina}**       |  Basic Stamina + Individial Stamina
**{sum_ads}**       |  Joined Final Values *(e.g. 129/97/321)*
 |  **Individial Values perfection percent**
**{iv_pct}**     |  IV perfection *(in 000-100 format - 3 chars)*
**{iv_pct2}**    |  IV perfection *(in 00-99 format - 2 chars).* So 99 is best (it's a 100% perfection)
**{iv_pct1}**    |  IV perfection *(in 0-9 format - 1 char)*
 |  **IV CP perfection - kind of IV perfection percent but calculated using weight of each IV in its contribution to CP of the best evolution of current pokemon.**<br> It tends to be more accurate than simple IV perfection.
**{ivcp_pct}**      |  IV CP perfection *(in 000-100 format - 3 chars)*
**{ivcp_pct2}**     |  IV CP perfection *(in 00-99 format - 2 chars).* So 99 is best (it's a 100% perfection)
**{ivcp_pct1}**     |  IV CP perfection *(in 0-9 format - 1 char)*
 |  **Moveset perfection percents for attack and for defense.**<br> Calculated for current pokemon only, not between all pokemons. So perfect moveset can be weak if pokemon is weak (e.g. Caterpie)
**{attack_pct}**   |  Moveset perfection for attack *(in 000-100 format - 3 chars)*
**{attack_pct2}**  |  Moveset perfection for attack *(in 00-99 format - 2 chars)*
**{attack_pct1}**  |  Moveset perfection for attack *(in 0-9 format - 1 char)*
**{defense_pct}**  |  Moveset perfection for defense *(in 000-100 format - 3 chars)*
**{defense_pct2}** |  Moveset perfection for defense *(in 00-99 format - 2 chars)*
**{defense_pct1}** |  Moveset perfection for defense *(in 0-9 format - 1 char)*
 |  **Character codes for fast/charged attack types.**<br> If attack is good character is uppecased, otherwise lowercased.<br>Use `'good_attack_threshold'` option for customization.<br><br> It's an effective way to represent type with one character.<br> If first char of the type name is unique - it's used, in other case suitable substitute used.<br><br> Type codes:<br> &nbsp;&nbsp;`Bug: 'B'`<br> &nbsp;&nbsp;`Dark: 'K'`<br> &nbsp;&nbsp;`Dragon: 'D'`<br> &nbsp;&nbsp;`Electric: 'E'`<br> &nbsp;&nbsp;`Fairy: 'Y'`<br> &nbsp;&nbsp;`Fighting: 'T'`<br> &nbsp;&nbsp;`Fire: 'F'`<br> &nbsp;&nbsp;`Flying: 'L'`<br> &nbsp;&nbsp;`Ghost: 'H'`<br> &nbsp;&nbsp;`Grass: 'A'`<br> &nbsp;&nbsp;`Ground: 'G'`<br> &nbsp;&nbsp;`Ice: 'I'`<br> &nbsp;&nbsp;`Normal: 'N'`<br> &nbsp;&nbsp;`Poison: 'P'`<br> &nbsp;&nbsp;`Psychic: 'C'`<br> &nbsp;&nbsp;`Rock: 'R'`<br> &nbsp;&nbsp;`Steel: 'S'`<br> &nbsp;&nbsp;`Water: 'W'`
**{fast_attack_char}**   |  One character code for fast attack type (e.g. 'F' for good Fire or 's' for bad Steel attack)
**{charged_attack_char}**   |  One character code for charged attack type (e.g. 'n' for bad Normal or 'I' for good Ice attack)
**{attack_code}**           |  Joined 2 character code for both attacks (e.g. 'Lh' for pokemon with strong Flying and weak Ghost attacks)
 |  **Special case: pokemon object**<br> You can access any available pokemon info via it.<br>Examples:<br> &nbsp;&nbsp;`'{pokemon.ivcp:.2%}'             ->  '47.00%'`<br> &nbsp;&nbsp;`'{pokemon.fast_attack}'          ->  'Wing Attack'`<br> &nbsp;&nbsp;`'{pokemon.fast_attack.type}'     ->  'Flying'`<br> &nbsp;&nbsp;`'{pokemon.fast_attack.dps:.2f}'  ->  '10.91'`<br> &nbsp;&nbsp;`'{pokemon.fast_attack.dps:.0f}'  ->  '11'`<br> &nbsp;&nbsp;`'{pokemon.charged_attack}'       ->  'Ominous Wind'`
**{pokemon}**   |  Pokemon instance (see inventory.py for class sources)

> **NOTE:** Use a blank template (`""`) to revert all pokemon to their original names (as if they had no nickname).

#### Sample usages

- `"{name}_{iv_pct}"` => `Mankey_069`
- `"{iv_pct}_{iv_ads}"` => `091_15/11/15`
- `""` -> `Mankey`
- `"{attack_code}{attack_pct1}{defense_pct1}{ivcp_pct1}{name}"` => `Lh474Golbat`
![sample](https://cloud.githubusercontent.com/assets/8896778/17285954/0fa44a88-577b-11e6-8204-b1302f4294bd.png)

### Sample configuration

```json
{
  "type": "NicknamePokemon",
  "config": {
    "enabled": true,
    "dont_nickname_favorite": false,
    "good_attack_threshold": 0.7,
    "nickname_template": "{iv_pct}_{iv_ads}",
    "locale": "en"
  }
}
```

## Sniping _(MoveToLocation)_

### Description
This task will fetch current pokemon spawns from /raw_data of an PokemonGo-Map instance. For information on how to properly setup PokemonGo-Map have a look at the Github page of the project [here](https://github.com/AHAAAAAAA/PokemonGo-Map/). There is an example config in `config/config.json.map.example`

### Options
* `Address` - Address of the webserver of PokemonGo-Map. ex: `http://localhost:5000`
* `Mode` - Which mode to run snipin on
    - `distance` - Will move to the nearest pokemon
    - `priority` - Will move to the pokemon with the highest priority assigned (tie breaking by distance)
* `prioritize_vips` - Will prioritize vips in distance and priority mode above all normal pokemon if set to true
* `min_time` - Minimum time the pokemon has to be available before despawn
* `max_distance` - Maximum distance the pokemon is allowed to be when walking, ignored when sniping
* `snipe`:
    - `True` - Will teleport to target pokemon, encounter it, teleport back then catch it
    - `False` - Will walk normally to the pokemon
* `update_map` - disable/enable if the map location should be automatically updated to the bots current location
* `catch` - A dictionary of pokemon to catch with an assigned priority (higher => better)
* `snipe_high_prio_only` - Whether to snipe pokemon above a certain threshold.
* `snipe_high_prio_threshold` - The threshold number corresponding with the `catch` dictionary. 
*   - Any pokemon above this threshold value will be caught by teleporting to its location, and getting back to original location if `snipe` is `True`.
*   - Any pokemon under this threshold value will make the bot walk to the Pokemon target wether `snipe` is `True` or `False`.

#### Example
```
{
  \\ ...
  {
    "type": "MoveToMapPokemon",
    "config": {
      "address": "http://localhost:5000",
      "max_distance": 500,
      "min_time": 60,
      "min_ball": 50,
      "prioritize_vips": true,
      "snipe": true,
      "snipe_high_prio_only": true,
      "snipe_high_prio_threshold": 400,
      "update_map": true,
      "mode": "priority",
      "catch": {
        "Aerodactyl": 1000,
        "Ditto": 900,
        "Omastar": 500,
        "Omanyte": 150,
        "Caterpie": 10,
      }
    }
  }
  \\ ...
}
```
