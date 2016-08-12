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
| `walk`             | 4.16    | Set the walking speed in kilometers per hour. (14 km/h is the maximum speed for egg hatching)                                                                                               |
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
* RecycleItems
  * `item_filter`: Pass a list of unwanted [items (using their JSON codes)](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Item-ID's) to recycle when collected at a Pokestop
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

Valid names in templates are:
- `name` = pokemon name
- `id` = pokemon type id (e.g. 1 for Bulbasaurs)
- `cp` = pokemon's CP
- `iv_attack` = pokemon's attack IV
- `iv_defense` = pokemon's defense IV
- `iv_stamina` = pokemon's stamina IV
- `iv_ads` = pokemon's IVs in `(attack)/(defense)/(stamina)` format (matches web UI format -- A/D/S)
- `iv_sum` = pokemon's IVs as a sum (e.g. 45 when 3 perfect 15 IVs)
- `iv_pct` = pokemon's IVs as a percentage (0-100)

> **NOTE:** Use a blank template (`""`) to revert all pokemon to their original names (as if they had no nickname).

Sample usages:
- `"{name}_{iv_pct}"` => `Mankey_69`
- `"{iv_pct}_{iv_ads}"` => `91_15/11/15`
- `""` -> `Mankey`
![sample](https://cloud.githubusercontent.com/assets/8896778/17285954/0fa44a88-577b-11e6-8204-b1302f4294bd.png)

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
* `snipe_high_prio_threshold` - The threshold number corresponding with the `catch` dictionary. Any pokemon above this threshold will be caught. Other will be igonored.

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
