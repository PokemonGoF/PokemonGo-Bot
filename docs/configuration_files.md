<a class="mk-toclify" id="table-of-contents"></a>

# Table of Contents
- [Usage](#usage)
- [Advanced Configuration](#advanced-configuration)
- [Configuring Tasks](#configuring-tasks)
    - [Task Options:](#task-options)
    - [Example configuration:](#example-configuration)
    - [Specifying configuration for tasks](#specifying-configuration-for-tasks)
    - [An example task configuration if you only wanted to collect items from forts:](#an-example-task-configuration-if-you-only-wanted-to-collect-items-from-forts)
- [Catch Configuration](#catch-configuration)
- [Release Configuration](#release-configuration)
    - [Common configuration](#common-configuration)
    - [Keep the strongest pokemon configuration (dev branch)](#keep-the-strongest-pokemon-configuration-dev-branch)
    - [Keep the best custom pokemon configuration (dev branch)](#keep-the-best-custom-pokemon-configuration-dev-branch)
- [Evolve All Configuration](#evolve-all-configuration)
- [Path Navigator Configuration](#path-navigator-configuration)
        - [Number of Laps](#number-of-laps)
- [Pokemon Nicknaming](#pokemon-nicknaming)
    - [Config options](#config-options)
    - [Valid names in templates](#valid-names-in-templates)
        - [Sample usages](#sample-usages)
    - [Sample configuration](#sample-configuration)
- [CatchPokemon Settings](#catchpokemon-settings)
    - [Default Settings](#default-settings)
    - [Settings Description](#settings-description)
    - [`flee_count` and `flee_duration`](#flee_count-and-flee_duration)
    - [Previous `catch_simulation` Behaviour](#previous-catch_simulation-behaviour)
- [Sniping _(MoveToLocation)_](#sniping-_-movetolocation-_)
    - [Description](#description)
    - [Options](#options)
        - [Example](#example)
- [FollowPath Settings](#followpath-settings)
    - [Description](#description)
    - [Options](#options)
    - [Sample Configuration](#sample-configuration)
- [UpdateLiveStats Settings](#updatelivestats-settings)
    - [Options](#options)
    - [Sample Configuration](#sample-configuration)
- [UpdateLiveInventory Settings](#updateliveinventory-settings)
    - [Description](#description)
    - [Options](#options)
    - [Sample configuration](#sample-configuration)
    - [Example console output](#example-console-output)
- [Sleep Schedule Task](#sleep-schedule-task)
- [Random Pause](#random-pause)
- [Egg Incubator](#egg-incubator)

#Configuration files

Document the configuration options of PokemonGo-Bot.

## Usage
[[back to top](#table-of-contents)]

1. copy `config.json.example` to `config.json`.
2. Edit `config.json` and replace `auth_service`, `username`, `password`, `location` and `gmapkey` with your parameters (other keys are optional, check `Advance Configuration` below)
3. Simply launch the script with : `./run.sh` or `./pokecli.py` or `python pokecli.py -cf ./configs/config.json` if you want to specify a config file


## Advanced Configuration
[[back to top](#table-of-contents)]

|      Parameter     | Default |                                                                                         Description                                                                                         |
|------------------|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tasks`            | []     | The behaviors you want the bot to do. Read [how to configure tasks](#configuring-tasks).
| `max_steps`        | 5       | The steps around your initial location (DEFAULT 5 mean 25 cells around your location) that will be explored
| `forts.avoid_circles`             | False     | Set whether the bot should avoid circles |
| `forts.max_circle_size`             | 10     | How many forts to keep in ignore list |
| `walk_max`             | 4.16    | Set the maximum walking speed (1 is about 1.5km/hr)
| `walk_min`             | 2.16    | Set the minimum walking speed (1 is about 1.5km/hr)
| `action_wait_min`   | 1       | Set the minimum time setting for anti-ban time randomizer
| `action_wait_max`   | 4       | Set the maximum time setting for anti-ban time randomizer
| `debug`            | false   | Let the default value here except if you are developer                                                                                                                                      |
| `test`             | false   | Let the default value here except if you are developer                                                                                                                                      |                                                                                       |
| `location_cache`   | true    | Bot will start at last known location if you do not have location set in the config                                                                                                         |
| `distance_unit`    | km      | Set the unit to display distance in (km for kilometers, mi for miles, ft for feet)                                                                                                          |
| `evolve_cp_min`           | 300   |                   Min. CP for evolve_all function
|`daily_catch_llimit`    | 800   |                   Limit the amount of pokemon caught in a 24 hour period.
|`pokemon_bag.show_at_start`    | false   |                   At start, bot will show all pokemon in the bag.
|`pokemon_bag.show_count`    | false   |                   Show amount of each pokemon.
|`pokemon_bag.pokemon_info`    | []   |                   Check any config example file to see available settings.


## Configuring Tasks
[[back to top](#table-of-contents)]

The behaviors of the bot are configured via the `tasks` key in the `config.json`. This enables you to list what you want the bot to do and change the priority of those tasks by reordering them in the list. This list of tasks is run repeatedly and in order. For more information on why we are moving config to this format, check out the [original proposal](https://github.com/PokemonGoF/PokemonGo-Bot/issues/142).


### Task Options:
[[back to top](#table-of-contents)]
* CatchPokemon
  * `treat_unseen_as_vip`: Default `"true"` | Set to `"false"` to disable treating pokemons you don't have in your pokedex as VIPs.
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
  * `nickname_above_iv`: Default `0` | Rename pokemon which iv is highter than the value
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
  * `min_free_slot`: Default `5` | Once the pokebag has less empty slots than this amount, the transfer process is triggered. | Big values (i.e 9999) will trigger the transfer process after each catch.
* UpdateLiveStats
* [UpdateLiveInventory](#updateliveinventory-settings)


### Example configuration:
[[back to top](#table-of-contents)]

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
      "type": "CatchPokemon"
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
[[back to top](#table-of-contents)]

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
[[back to top](#table-of-contents)]

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
[[back to top](#table-of-contents)]

Default configuration will capture all Pokémon.

```"any": {"catch_above_cp": 0, "catch_above_iv": 0, "logic": "or"}```

You can override the global configuration with Pokémon-specific options, such as:

```"Pidgey": {"catch_above_cp": 0, "catch_above_iv": 0.8", "logic": "and"}``` to only capture Pidgey with a good roll.

Additionally, you can specify always_capture and never_capture flags.

For example: ```"Pidgey": {"never_capture": true}``` will stop catching Pidgey entirely.

## Release Configuration
[[back to top](#table-of-contents)]

### Common configuration
[[back to top](#table-of-contents)]

Default configuration will not release any Pokémon.

```"release": {"any": {"release_below_cp": 0, "release_below_iv": 0, "logic": "or"}}```

You can override the global configuration with Pokémon-specific options, such as:

```"release": {"Pidgey": {"release_below_cp": 0, "release_below_iv": 0.8, "logic": "or"}}``` to only release Pidgey with bad rolls.

Additionally, you can specify always_release and never_release flags. For example:

```"release": {"Pidgey": {"always_release": true}}``` will release all Pidgey caught.

### Keep the strongest pokemon configuration (dev branch)
[[back to top](#table-of-contents)]

You can set ```"release": {"Pidgey": {"keep_best_cp": 1}}``` or ```"release": {"any": {"keep_best_iv": 1}}```.

In that case after each capture bot will check that do you have a new Pokémon or not.

If you don't have it, it will keep it (no matter was it strong or weak Pokémon).

If you already have it, it will keep a stronger version and will transfer the a weaker one.

```"release": {"any": {"keep_best_cp": 2}}```, ```"release": {"any": {"keep_best_cp": 10}}``` - can be any number.

### Keep the best custom pokemon configuration (dev branch)
[[back to top](#table-of-contents)]

Define a list of criteria to keep the best Pokemons according to those criteria.

The list of criteria is the following:```'cp','iv', 'iv_attack', 'iv_defense', 'iv_stamina', 'moveset.attack_perfection', 'moveset.defense_perfection', 'hp', 'hp_max'```

####Examples:

- Keep the top 25 Zubat with the best hp_max:

```"release": {"Zubat": {"keep_best_custom": "hp_max", "amount":25}}```
- Keep the top 10 Zubat with the best hp_max and, if there are Zubat with the same hp_max, to keep the one with the highest hp:

```"release": {"Zubat": {"keep_best_custom": "hp_max,hp", "amount":10}}````

## Evolve All Configuration
[[back to top](#table-of-contents)]

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
[[back to top](#table-of-contents)]

Setting the `navigator.type` setting to `path` allows you to specify waypoints which the bot will follow. The waypoints can be loaded from a GPX or JSON file. By default the bot will walk along all specified waypoints and then move directly to the first waypoint again. When setting `navigator.path_mode` to `linear`, the bot will turn around at the last waypoint and along the given waypoints in reverse order.

An example for a JSON file can be found in `configs/path.example.json`. GPX files can be exported from many online tools, such as gpsies.com.The bot loads the first segment of the first track.

<a class="mk-toclify" id="number-of-laps"></a>
#### Number of Laps
[[back to top](#table-of-contents)]

In the path navigator configuration task, add a maximum of passage above which the bot stop for a time before starting again. *Note that others tasks (such as SleepSchedule or RandomPause) can stop the bot before.*

- number_lap set-up the number of passage. **To allow for an infinity number of laps, set-up the number at -1**.

`"number_lap": 10` (will do 10 passages before stopping)
- timer_restart_min is the minimum time the bot stop before starting again (format Hours:Minutes:Seconds).

`"timer_restart_min": "00:10:00"` (will stop for a minimum of 10 minutes)
- timer_restart_max is the maximum time the bot stop before starting again (format Hours:Minutes:Seconds).

`"timer_restart_max": "00:20:00"` (will stop for a maximum of 10 minutes)


## Pokemon Nicknaming
[[back to top](#table-of-contents)]

A `nickname_template` can be specified for the `NicknamePokemon` task to allow a nickname template to be applied to all pokemon in the user's inventory. For example, a user wanting all their pokemon to have their IV values as their nickname could use a template `{iv_ads}`, which will cause their pokemon to be named something like `13/7/12` (depending on the pokemon's actual IVs).

The `NicknamePokemon` task will rename all pokemon in inventory on startup to match the given template and will rename any newly caught/hatched/evolved pokemon as the bot runs. _It may take one or two "ticks" after catching/hatching/evolving a pokemon for it to be renamed. This is intended behavior._

> **NOTE:** If you experience frequent `Pokemon not found` error messages, this is because the inventory cache has not been updated after a pokemon was released. This can be remedied by placing the `NicknamePokemon` task above the `TransferPokemon` task in your `config.json` file.

Niantic imposes a 12-character limit on all pokemon nicknames, so any new nickname will be truncated to 12 characters if over that limit. Thus, it is up to the user to exercise judgment on what template will best suit their need with this constraint in mind.

Because some pokemon have very long names, you can use the [Format String syntax](https://docs.python.org/2.7/library/string.html#formatstrings) to ensure that your names do not cause your templates to truncate. For example, using `{name:.8s}` causes the Pokemon name to never take up more than 8 characters in the nickname. This would help guarantee that a template like `{name:.8s}_{iv_pct}` never goes over the 12-character limit.

### Config options
[[back to top](#table-of-contents)]

* `enable` (default: `true`): To enable or disable this task.
* `nickname_template` (default: `{name}`): The template to rename the pokemon.
* `dont_nickname_favorite` (default: `false`): Prevents renaming of favorited pokemons.
* `good_attack_threshold` (default: `0.7`): Threshold for perfection of the attack in it's type (0.0-1.0) after which attack will be treated as good. Used for {fast_attack_char}, {charged_attack_char}, {attack_code} templates.
* `locale` (default: `en`): The locale to use for the pokemon name.

### Valid names in templates
[[back to top](#table-of-contents)]

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
[[back to top](#table-of-contents)]

- `"{name}_{iv_pct}"` => `Mankey_069`
- `"{iv_pct}_{iv_ads}"` => `091_15/11/15`
- `""` -> `Mankey`
- `"{attack_code}{attack_pct1}{defense_pct1}{ivcp_pct1}{name}"` => `Lh474Golbat`
![sample](https://cloud.githubusercontent.com/assets/8896778/17285954/0fa44a88-577b-11e6-8204-b1302f4294bd.png)

### Sample configuration
[[back to top](#table-of-contents)]

```json
{
  "type": "NicknamePokemon",
  "config": {
    "enabled": true,
    "dont_nickname_favorite": false,
    "good_attack_threshold": 0.7,
    "nickname_template": "{iv_pct}_{iv_ads}"
    "locale": "en"
  }
}
```

## CatchPokemon Settings
[[back to top](#table-of-contents)]

These settings determine how the bot will catch pokemon. `catch_simulate` simulates the app by adding pauses to throw the ball and navigate menus.  All times in `catch_simulation` are in seconds.

### Default Settings
[[back to top](#table-of-contents)]

The default settings are 'safe' settings intended to simulate human and app behaviour.

```
"catch_visible_pokemon": true,
"catch_lured_pokemon": true,
"min_ultraball_to_keep": 5,
"berry_threshold": 0.35,
"vip_berry_threshold": 0.9,
"catch_throw_parameters": {
  "excellent_rate": 0.1,
  "great_rate": 0.5,
  "nice_rate": 0.3,
  "normal_rate": 0.1,
  "spin_success_rate" : 0.6,
  "hit_rate": 0.75
},
"catch_simulation": {
  "flee_count": 3,
  "flee_duration": 2,
  "catch_wait_min": 2,
  "catch_wait_max": 6,
  "berry_wait_min": 2,
  "berry_wait_max": 3,
  "changeball_wait_min": 2,
  "changeball_wait_max": 3
}
```

### Settings Description
[[back to top](#table-of-contents)]

Setting | Description
---- | ----
`min_ultraball_to_keep` | Allows the bot to use ultraballs on non-VIP pokemon as long as number of ultraballs is above this setting
`berry_threshold` | The ideal catch rate threshold before using a razz berry on normal pokemon (higher threshold means using razz berries more frequently, for example if we raise `berry_threshold` to 0.5, any pokemon that has an initial catch rate between 0 to 0.5 will initiate a berry throw)
`vip_berry_threshold` | The ideal catch rate threshold before using a razz berry on VIP pokemon
`flee_count` | The maximum number of times catching animation will play before the pokemon breaks free
`flee_duration` | The length of time for each animation
`catch_wait_min`| The minimum amount of time to throw the ball
`catch_wait_max`| The maximum amount of time to throw the ball
`berry_wait_min`| The minimum amount of time to use a berry
`berry_wait_max`| The maximum amount of time to use a berry
`changeball_wait_min`| The minimum amount of time to change ball
`changeball_wait_max`| The maximum amount of time to change ball

### `flee_count` and `flee_duration`
[[back to top](#table-of-contents)]

This part is app simulation and the default settings are advised.  When we hit a pokemon in the app the animation will play randomly 1, 2 or 3 times for roughly 2 seconds each time.  So we pause for a random number of animations up to `flee_count` of duration `flee_duration`

### Previous `catch_simulation` Behaviour
[[back to top](#table-of-contents)]

If you want to make your bot behave as it did prior to the catch_simulation update please use the following settings.

```
"catch_simulation": {
    "flee_count": 1,
    "flee_duration": 2,
    "catch_wait_min": 0,
    "catch_wait_max": 0,
    "berry_wait_min": 0,
    "berry_wait_max": 0,
    "changeball_wait_min": 0,
    "changeball_wait_max": 0
}
```

## Sniping _(MoveToLocation)_
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

This task will fetch current pokemon spawns from /raw_data of an PokemonGo-Map instance. For information on how to properly setup PokemonGo-Map have a look at the Github page of the project [here](https://github.com/AHAAAAAAA/PokemonGo-Map/). There is an example config in `config/config.json.map.example`

### Options
[[back to top](#table-of-contents)]

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
*   `max_extra_dist_fort` : Percentage of extra distance allowed to move to a fort on the way to the targeted Pokemon

#### Example
[[back to top](#table-of-contents)]

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
      "max_extra_dist_fort": 10,   
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

## FollowPath Settings
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

Walk to the specified locations loaded from .gpx or .json file. It is highly recommended to use website such as [GPSies](http://www.gpsies.com) which allow you to export your created track in JSON file. Note that you'll have to first convert its JSON file into the format that the bot can understand. See [Example of pier39.json] below for the content. I had created a simple python script to do the conversion. 

### Options
[[back to top](#table-of-contents)]
* `path_mode` - linear, loop
   - `loop` - The bot will walk along all specified waypoints and then move directly to the first waypoint again. 
   - `linear` - The bot will turn around at the last waypoint and along the given waypoints in reverse order.
* `path_start_mode` - first
* `path_file` - "/path/to/your/path.json"


### Sample Configuration
[[back to top](#table-of-contents)]

```
{
	"type": "FollowPath",
    "config": {
    	"path_mode": "linear",
	  	"path_start_mode": "first",
      "path_file": "/home/gary/bot/PokemonGo-Bot/configs/path/pier39.json"
    }
}
```

Example of pier39.json
```
[{"location": "37.8103848,-122.410325"}, 
{"location": "37.8103306,-122.410435"}, 
{"location": "37.8104662,-122.41051"}, 
{"location": "37.8106146,-122.41059"}, 
{"location": "37.8105934,-122.410719"}
]
```

You would then see the [FollowPath] [INFO] console log as the bot walks to each location in the path.json file.
```
2016-08-21 00:09:36,521 [FollowPath] [INFO] [position_update] Walk to (37.8093976, -122.4103554, 0) now at (37.80934873280548, -122.40986165166986, 0), distance left: (43.7148620033 m) ..
2016-08-21 00:09:38,392 [FollowPath] [INFO] [position_update] Walk to (37.8093976, -122.4103554, 0) now at (37.809335215749876, -122.40987810257064, 0), distance left: (42.5005577777 m) ..
2016-08-21 00:09:39,899 [FollowPath] [INFO] [position_update] Walk to (37.8093976, -122.4103554, 0) now at (37.809331611049714, -122.40991111241473, 0), distance left: (39.7144254183 m) ..
2016-08-21 00:09:42,038 [FollowPath] [INFO] [position_update] Walk to (37.8093976, -122.4103554, 0) now at (37.80935188969784, -122.4099397940133, 0), distance left: (36.8630805218 m) ..
2016-08-21 00:09:43,791 [FollowPath] [INFO] [position_update] Walk to (37.8093976, -122.4103554, 0) now at (37.80936378035156, -122.40998419490474, 0), distance left: (32.8264884039 m) ..
2016-08-21 00:09:45,766 [FollowPath] [INFO] [position_update] Walk to (37.8093976, -122.4103554, 0) now at (37.80935021728436, -122.40999180104075, 0), distance left: (32.3738347114 m) ..
```

## UpdateLiveStats Settings
[[back to top](#table-of-contents)]

Periodically displays stats about the bot in the terminal and/or in its title.

Fetching some stats requires making API calls. If you're concerned about the amount of calls your bot is making, don't enable this worker.

### Options
[[back to top](#table-of-contents)]
```
min_interval : The minimum interval at which the stats are displayed,
               in seconds (defaults to 120 seconds).
               The update interval cannot be accurate as workers run synchronously.
stats : An array of stats to display and their display order (implicitly),
        see available stats below (defaults to []).
terminal_log : Logs the stats into the terminal (defaults to false).
terminal_title : Displays the stats into the terminal title (defaults to true).
```

Available `stats` parameters:
```
- login : The account login (from the credentials).
- username : The trainer name (asked at first in-game connection).
- uptime : The bot uptime.
- km_walked : The kilometers walked since the bot started.
- level : The current character's level.
- level_completion : The current level experience, the next level experience and the completion
                     percentage.
- level_stats : Puts together the current character's level and its completion.
- xp_per_hour : The estimated gain of experience per hour.
- xp_earned : The experience earned since the bot started.
- stops_visited : The number of visited stops.
- pokemon_encountered : The number of encountered pokemon.
- pokemon_caught : The number of caught pokemon.
- captures_per_hour : The estimated number of pokemon captured per hour.
- pokemon_released : The number of released pokemon.
- pokemon_evolved : The number of evolved pokemon.
- pokemon_unseen : The number of pokemon never seen before.
- pokemon_stats : Puts together the pokemon encountered, caught, released, evolved and unseen.
- pokeballs_thrown : The number of thrown pokeballs.
- stardust_earned : The number of earned stardust since the bot started.
- highest_cp_pokemon : The caught pokemon with the highest CP since the bot started.
- most_perfect_pokemon : The most perfect caught pokemon since the bot started.
```

### Sample Configuration
[[back to top](#table-of-contents)]

Following task will shows the information on the console every 10 seconds.
```
{
  "type": "UpdateLiveStats",
  "config": {
    "enabled": true,
    "min_interval": 10,
    "stats": ["username", "uptime", "level_completion", "stardust_earned", "xp_earned", "xp_per_hour", "stops_visited", "km_walked", "pokemon_encountered", "pokemon_caught", "pokemon_released", "pokemon_unseen", "pokeballs_thrown", "highest_cp_pokemon", "most_perfect_pokemon"],
    "terminal_log": true,
    "terminal_title": true
  }
}
```

Example console output
```
2016-08-20 23:55:48,513 [UpdateLiveStats] [INFO] [log_stats] USERNAME | Uptime : 0:17:17 | Level 26 (192,995 / 390,000, 49%) | Earned 900 Stardust | +2,810 XP | 9,753 XP/h | Visited 23 stops | 0.80km walked | Caught 9 pokemon
```

## UpdateLiveInventory Settings
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

Periodically displays the user inventory in the terminal.

### Options
[[back to top](#table-of-contents)]
* `min_interval` : The minimum interval at which the stats are displayed, in seconds (defaults to 120 seconds). The update interval cannot be accurate as workers run synchronously.
* `show_all_multiple_lines` : Logs all items on inventory using multiple lines. Ignores configuration of 'items' 
* `items` : An array of items to display and their display order (implicitly), see available items below (defaults to []).

Available `items` :
```
- 'pokemon_bag' : pokemon in inventory (i.e. 'Pokemon Bag: 100/250')
- 'space_info': not an item but shows inventory bag space (i.e. 'Items: 140/350')
- 'pokeballs'
- 'greatballs'
- 'ultraballs'
- 'masterballs'
- 'razzberries'
- 'blukberries'
- 'nanabberries'
- 'luckyegg'
- 'incubator'
- 'troydisk'
- 'potion'
- 'superpotion'
- 'hyperpotion'
- 'maxpotion'
- 'incense'
- 'incensespicy'
- 'incensecool'
- 'revive'
- 'maxrevive'
```

### Sample configuration
[[back to top](#table-of-contents)]
```json
{
    "type": "UpdateLiveInventory",
    "config": {
      "enabled": true,
      "min_interval": 120,
      "show_all_multiple_lines": false,
      "items": ["space_info", "pokeballs", "greatballs", "ultraballs", "razzberries", "luckyegg"]
```

### Example console output
[[back to top](#table-of-contents)]
```
2016-08-20 18:56:22,754 [UpdateLiveInventory] [INFO] [show_inventory] Items: 335/350 | Pokeballs: 8 | GreatBalls: 186 | UltraBalls: 0 | RazzBerries: 51 | LuckyEggs: 3
```

## Sleep Schedule Task
[[back to top](#table-of-contents)]

Pauses the execution of the bot every day for some time

Simulates the user going to sleep every day for some time, the sleep time and the duration is changed every day by a random offset defined in the config file.

- `time`: (HH:MM) local time that the bot should sleep
- `duration`: (HH:MM) the duration of sleep
- `time_random_offset`: (HH:MM) random offset of time that the sleep will start for this example the possible start time is 11:30-12:30
- `duration_random_offset`: (HH:MM) random offset of duration of sleep for this example the possible duration is 5:00-6:00
- `wake_up_at_location`: (lat, long | lat, long, alt | "") the location at which the bot wake up *Note that an empty string ("") will not change the location*.

###Example Config
```
{
	"type": "SleepSchedule",
	"config": {
		"time": "12:00",
		"duration":"5:30",
		"time_random_offset": "00:30",
		"duration_random_offset": "00:30"
		"wake_up_at_location": "39.408692,149.595838,590.8"
	}
}
```

## Random Pause
[[back to top](#table-of-contents)]

Pause the execution of the bot at a random time for a random time.

Simulates the random pause of the day (speaking to someone, getting into a store, ...) where the user stops the app. The interval between pauses and the duration of pause are configurable.

- `min_duration`: (HH:MM:SS) the minimum duration of each pause
- `max_duration`: (HH:MM:SS) the maximum duration of each pause
- `min_interval`: (HH:MM:SS) the minimum interval between each pause
- `max_interval`: (HH:MM:SS) the maximum interval between each pause

###Example Config
```
{
	"type": "RandomPause",
	"config": {
		"min_duration": "00:00:10",
		"max_duration": "00:10:00",
		"min_interval": "00:10:00",
		"max_interval": "02:00:00"
	}
}
```

##Egg Incubator
[[back to top](#table-of-contents)]

Configure how the bot should use the incubators.

- `longer_eggs_first`: (True | False ) should the bot start by the longer eggs first. If set to true, the bot first use the 10km eggs, then the 5km eggs, then the 2km eggs.
- `infinite`: ([2], [2,5], [2,5,10], []) the type of egg the infinite (ie. unbreakable) incubator(s) can incubate. If set to [2,5], the incubator(s) can only incubate the 2km and 5km eggs. If set to [], the incubator(s) will not incubate any type of egg.
- `breakable`: ([2], [2,5], [2,5,10], []) the type of egg the breakable incubator(s) can incubate. If set to [2,5], the incubator(s) can only incubate the 2km and 5km eggs. If set to [], the incubator(s) will not incubate any type of egg.

###Example Config
```
{
	"type": "IncubateEggs",
    "config": {
		"longer_eggs_first": true,
		"infinite": [2,5],
		"breakable": [10]
	}
}
```


