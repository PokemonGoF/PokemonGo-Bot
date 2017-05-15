<a class="mk-toclify" id="table-of-contents"></a>

# Table of Contents
- [Usage](#usage)
- [Advanced Configuration](#advanced-configuration)
- [Logging configuration](#logging-configuration)
- [Sleep Schedule configuration](#sleep-schedule-configuration)
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
- [CatchLimiter Settings](#catchlimiter-settings)
- [Sniping _(MoveToLocation)_](#sniping-movetolocation)
    - [Description](#description)
    - [Options](#options)
        - [Example](#example)
- [Sniping _(Sniper)_](#sniper)
    - [Description](#description-1)
    - [Options](#options-1)
        - [Example](#example)
- [FollowPath Settings](#followpath-settings)
    - [Description](#description-2)
    - [Options](#options-2)
    - [Sample Configuration](#sample-configuration-1)
- [UpdateLiveStats Settings](#updatelivestats-settings)
    - [Options](#options-3)
    - [Sample Configuration](#sample-configuration-2)
- [UpdateLiveInventory Settings](#updateliveinventory-settings)
    - [Description](#description-3)
    - [Options](#options-4)
    - [Sample configuration](#sample-configuration-3)
    - [Example console output](#example-console-output)
- [UpdateHashStats Settings](#updatehashstats-settings)
    - [Description](#description-4)
    - [Options](#options-5)
    - [Sample configuration](#sample-configuration-4)
    - [Example console output](#example-console-output-1)
- [Random Pause](#random-pause)
- [Egg Incubator](#egg-incubator)
- [ShowBestPokemon](#showbestpokemon)
- [Telegram Task](#telegram-task)
- [Discord Task](#discord-task)
- [CompleteTutorial](#completetutorial)
- [BuddyPokemon](#buddypokemon)
- [PokemonHunter](#pokemonhunter)

# Configuration files

Document the configuration options of PokemonGo-Bot.

## Usage
[[back to top](#table-of-contents)]

1. copy `auth.json.example` to `auth.json`.
2. Edit `auth.json` and replace `auth_service`, `username`, `password`, `location` and `gmapkey` with your parameters (other keys are optional)
3. copy `config.json.example` to `config.json`.=
3. Simply launch the script with : `./run.sh` or './run.sh ./configs/your_auth_file.json ./configs/your_base_config_file.json'


## Advanced Configuration
[[back to top](#table-of-contents)]

|      Parameter     | Default |                                                                                         Description                                                                                         |
|------------------|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tasks`            | []     | The behaviors you want the bot to do. Read [how to configure tasks](#configuring-tasks).
| `max_steps`        | 5       | The steps around your initial location (DEFAULT 5 mean 25 cells around your location) that will be explored
| `forts.avoid_circles`             | False     | Set whether the bot should avoid circles |
| `forts.max_circle_size`             | 10     | How many forts to keep in ignore list |
| `walk_max`             | 4.16    | Set the maximum walking speed in m/s (1 is about 3.6km/hr) 4.16m/s = 15km/h
| `walk_min`             | 2.16    | Set the minimum walking speed in m/s (1 is about 3.6km/hr) 2.16m/s = 7.8km/h
| `action_wait_min`   | 1       | Set the minimum time setting for anti-ban time randomizer
| `action_wait_max`   | 4       | Set the maximum time setting for anti-ban time randomizer
| `debug`            | false   | Let the default value here except if you are developer                                                                                                                                      |
| `test`             | false   | Let the default value here except if you are developer                                                                                                                                      |
| `walker_limit_output`             | false   | Reduce output from walker functions                                                                                                                                      |                                                                                       |
| `location_cache`   | true    | Bot will start at last known location if you do not have location set in the config                                                                                                         |
| `distance_unit`    | km      | Set the unit to display distance in (km for kilometers, mi for miles, ft for feet)                                                                                                          |
| `evolve_cp_min`           | 300   |                   Min. CP for evolve_all function
|`daily_catch_llimit`    | 800   |                   Limit the amount of pokemon caught in a 24 hour period.
|`pokemon_bag.show_at_start`    | false   |                   At start, bot will show all pokemon in the bag.
|`pokemon_bag.show_count`    | false   |                   Show amount of each pokemon.
|`pokemon_bag.pokemon_info`    | []   |                   Check any config example file to see available settings.
|`favorite_locations`    | []   | Allows you to define a collection of locations and coordinates, allowing rapid switch using a "label" on your location config
| `live_config_update.enabled`            | false     | Enable live config update
| `live_config_update.tasks_only`            | false     | True: quick update for Tasks only (without re-login). False: slower update for entire config file.
| `enable_social`            | true     | True: to chat with other pokemon go bot users [more information](https://github.com/PokemonGoF/PokemonGo-Bot/pull/4596)
| `reconnecting_timeout`   |  5      | Set the wait time for the bot between tries, time will be randomized by 40%

## Logging configuration
[[back to top](#table-of-contents)]

- 'logging'.'color' (default false) Enabled colored logging
- 'logging'.'show_datetime' (default true) Show date and time in log
- 'logging'.'show_process_name' (default true) Show name of process generating output in log
- 'logging'.'show_log_level' (default true) Show level of log message in log (eg. "INFO")
- 'logging'.'show_thread_name' (default false) Show name of thread in log

## Sleep Schedule configuration
[[back to top](#table-of-contents)]

Pauses the execution of the bot every day for some time

Simulates the user going to sleep every day for some time, the sleep time and the duration is changed every day by a random offset defined in the config file.

### Example Config
```
"sleep_schedule": {
  "enabled": true,
  "enable_reminder": false,
  "reminder_interval": 600,
  "entries": [
    {
      "enabled": true,
      "time": "12:00",
      "duration": "5:30",
      "time_random_offset": "00:30",
      "duration_random_offset": "00:30",
      "wake_up_at_location": ""
    },
    {
      "enabled": true,
      "time": "17:45",
      "duration": "3:00",
      "time_random_offset": "01:00",
      "duration_random_offset": "00:30",
      "wake_up_at_location": ""
    }
  ]
}
```

- enabled: (true | false) enables/disables SleepSchedule. Inside of entry will enable/disable single entry, but will not override global value. Default: true
- enable_reminder: (true | false) enables/disables sleep reminder. Default: false
- reminder_interval: (interval) reminder interval in seconds. Default: 600

- entries: [{}] SleepSchedule entries. Default: []
- enabled: (true | false) see above
- time: (HH:MM) local time that the bot should sleep
- duration: (HH:MM) the duration of sleep
- time_random_offset: (HH:MM) random offset of time that the sleep will start, for this example the possible start times are 11:30-12:30 and 16:45-18:45. Default: 01:00
- duration_random_offset: (HH:MM) random offset of duration of sleep, for this example the possible durations are 5:00-6:00 and 2:30-3:30. Default: 00:30
- wake_up_at_location: (label | lat, long | lat, long, alt | "") the location at which the bot wake up. You can use location "label" set in favorite_location config. Default: "". *Note that an empty string ("") will not change the location*.


## Configuring Tasks
[[back to top](#table-of-contents)]

The behaviors of the bot are configured via the `tasks` key in the `config.json`. This enables you to list what you want the bot to do and change the priority of those tasks by reordering them in the list. This list of tasks is run repeatedly and in order. For more information on why we are moving config to this format, check out the [original proposal](https://github.com/PokemonGoF/PokemonGo-Bot/issues/142).


### Task Options:
[[back to top](#table-of-contents)]
* CatchPokemon
  * `enabled`: Default "true" | Enable/Disable the task.
  * `treat_unseen_as_vip`: Default `"true"` | If true, treat new to dex as VIP
  * `catch_visible_pokemon`:  Default "true" | If enabled, attempts to catch "visible" pokemon that are reachable
  * `catch_lured_pokemon`: Default "true" | If enabled, attempts to catch "lured" pokemon that are reachable
  * `catch_incensed_pokemon`: Default "true" | If enabled, attempts to catch pokemon that are found because of an active incense
  * `min_ultraball_to_keep`: Default 5 | Minimum amount of reserved ultraballs to have on hand (for VIP)
  * `berry_threshold`: Default 0.35 | Catch percentage we start throwing berries
  * `vip_berry_threshold`: Default 0.9 | Something similar?
  * `treat_unseen_as_vip`: Default "true" | If enabled, treat new to our dex as VIP
  * `daily_catch_limit`: Default 800 | How many pokemon we limit ourselves to daily
  * `catch_throw_parameters`: Variable catch settings
    * `excellent_rate`: 0.1 | Change of excellent throw
    * `great_rate`: 0.5 | Change of excellent throw
    * `nice_rate`: 0.3 | Change of nice throw
    * `normal_rate`: 0.1 | Change of normal throw
    * `spin_success_rate` : 0.6 | Change of using a spin throw
    * `hit_rate`: 0.75 | Change of overall hit chance
  `catch_simulation`:
    * `flee_count`: 3 | ??
    * `flee_duration`: 2 | ??
    * `catch_wait_min`: 3 | Minimum time to wait after a catch
    * `catch_wait_max`: 6 | Maximum time to wait after a catch
    * `berry_wait_min`: 3 | Minimum time to wait after throwing berry
    * `berry_wait_max`: 5 | Maxiumum time to wait after throwing berry
    * `changeball_wait_min`: 3 | Minimum time to wait when changing balls
    * `changeball_wait_max`: 5 | Maximum time to wait when changing balls
    * `newtodex_wait_min`: 20 | Minimum time to wait if we caught a new type of pokemon
    * `newtodex_wait_max`: 39 | Maximum time to wait if we caught a new type of pokemon
* Catch Limiter
  * `enabled`: Default false | Enable/disable the task
  * `min_balls`: Default 20 | Minimum balls on hand before catch tasks enabled
  * `resume_at_balls`: Default 100 | When this number of balls is reached, immediately resume catching
  * `duration`: Default 15 | Length of time to disable catch tasks
* EvolvePokemon
  * `enable`: Disable or enable this task.
  * `evolve_all`: Default `NONE` | Depreciated. Please use evolve_list and donot_evolve_list
  * `log_interval`: `Default: 120`. Time (in seconds) to periodically print how far you are from having enough pokemon to evolve (more than `min_pokemon_to_be_evolved`)
  * `evolve_list`: Default `all` | Set to all, or specifiy different pokemon seperated by a comma
  * `donot_evolve_list`: Default `none` | Pokemon seperated by comma, will be ignored from evolve_list
  * `min_evolve_speed`: Default `25` | Minimum seconds to wait between each evolution
  * `max_evolve_speed`: Default `30` | Maximum seconds to wait between each evolution
  * `min_pokemon_to_be_evolved`: Default: `1` | Minimum pokemon to be evolved
  * `use_lucky_egg`: Default: `False` | Only evolve if we can use a lucky egg
* FollowPath
  * `enable`: Disable or enable this task.
  * `disable_while_hunting`: Default `true` | Disable walking when Pokemon Hunter has a target locked.
  * `path_mode`: Default `loop` | Set the mode for the path navigator (loop, linear or single).
  * `path_file`: Default `NONE` | Set the file containing the waypoints for the path navigator.
* FollowSpiral
  * `enable`: Disable or enable this task.
  * `spin_wait_min`: Default 3 | Minimum wait time after fort spin
  * `spin_wait_max`: Default 5 | Maximum wait time after fort spin
  * `daily_spin_limit`: Default 2000 | Daily spin limit
  * `min_interval`: Default 120 | When daily spin limit is reached, how often should the warning message be shown
  * `exit_on_limit_reached`: Default `True` | Code will exits if daily_spin_limit is reached
* HandleSoftBan
* IncubateEggs
  * `enable`: Disable or enable this task.
  * `longer_eggs_first`: Depreciated
  * `infinite_longer_eggs_first`:  Default `false` | Prioritize longer eggs in perminent incubators.
  * `infinite_random_eggs`:  Default `false` | Put a random egg in perminent incubators.
  * `breakable_longer_eggs_first`:  Default `true` | Prioritize longer eggs in breakable incubators.
  * `min_interval`: Default `120` | Minimum number of seconds between incubation updates.
  * `infinite`: Default `[2,5,10]` | Types of eggs to be incubated in permanent incubators.
  * `breakable`: Default `[2,5,10]` | Types of eggs to be incubated in breakable incubators.
* MoveToFort
  * `enable`: Disable or enable this task.
  * `lure_attraction`: Default `true` | Be more attracted to lured forts than non
  * `lure_max_distance`: Default `2000` | Maxmimum distance lured forts influence this task
  * `walker`: Default `StepWalker` | Which walker moves us
  * `log_interval`: Default `5` | Log output interval
* [MoveToMapPokemon](#sniping-movetolocation)
* NicknamePokemon
  * `enable`: Disable or enable this task.
  * `nickname_template`: Default `""` | See the [Pokemon Nicknaming](#pokemon-nicknaming) section for more details
  * `nickname_above_iv`: Default `0` | Rename pokemon which iv is highter than the value
  * `dont_nickname_favorite`: Default `false` | Prevents renaming of favorited pokemons
  * `good_attack_threshold`: Default `0.7` | Threshold for perfection of the attack in it's type *(0.0-1.0)* after which attack will be treated as good.<br>Used for `{fast_attack_char}`, `{charged_attack_char}`, `{attack_code}`  templates
* RecycleItems
  * `enabled`: Default `true` | Disable or enable this task
  * `min_empty_space`: Default 15 | minimum spaces before forcing transfer
  * `max_balls_keep`: Default 150 | Maximum cumlative balls to keep
  * `max_potions_keep`: Default 50 | Maximum cumlative potions to keep
  * `max_berries_keep`: Default 70 | Maximum culative berries to keep
  * `max_revives_keep`: Default 70 | Maxiumum culative revies to keep
  * `recycle_wait_min`: 3 | Minimum wait time after recycling an item
  * `recycle_wait_max`: 5 | Maxiumum culative revies to keep
  * `recycle_force`: Default true  | Enable/Disable time forced item recycling
  * `recycle_force_min`: Default `00:01:00`  | Minimum time to wait before forcing recycling
  * `recycle_force_max`: default `00:05:00`  | Maximum time to wait before forcing recycling

  > **NOTE:** It's highly recommended to put this task before MoveToFort and SpinFort tasks. This way you'll most likely be able to loot.
  * `min_empty_space`: Default `6` | Minimum empty space to keep in inventory. Once the inventory has less empty space than that amount, the recycling process is triggered. Set it to the inventory size to trigger it at every tick.
  * `item_filter`: Pass a list of unwanted [items (using their JSON codes or names)](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Item-ID's) to recycle.
  * `max_balls_keep`: Default `None` | Maximum amount of balls to keep in inventory
  * `max_potions_keep`: Default `None` | Maximum amount of potions to keep in inventory
  * `max_berries_keep`: Default `None` | Maximum amount of berries to keep in inventory
  * `max_revives_keep`: Default `None` | Maximum amount of revives to keep in inventory
  * `recycle_force`: Default `False` | Force scheduled recycle, even if min_empty_space not exceeded
  * `recycle_force_min`: Default `00:01:00` | Minimum time to wait before scheduling next forced recycle
  * `recycle_force_max`: Default `00:10:00` | Maximum time to wait before scheduling next forced recycle

* SpinFort
  * `enabled`: Default true | Enable for disable this task
  * `spin_wait_min`: Defaut 3 | Minimum wait after spinning a fort
  * `spin_wait_max`: Default 5 | Maximum wait after spinning a fort
* TransferPokemon
  * `enable`: Disable or enable this task.
  * `min_free_slot`: Default `5` | Once the pokebag has less empty slots than this amount, the transfer process is triggered. | Big values (i.e 9999) will trigger the transfer process after each catch.
* UpdateLiveStats
* [UpdateLiveInventory](#updateliveinventory-settings)
* CollectLevelUpReward
  * `collect_reward`: Default `True` | Collect level up rewards.
  * `level_limit`: Default `-1` | Bot will stop automatically after trainer reaches level limit. Set to `-1` to disable.
* All tasks
  * `log_interval`: Default `0` | Minimum seconds interval before next log of the current task will be printed


### Specify a custom log_interval for specific task

  ```
    {
      "type": "MoveToFort",
      "config": {
        "enabled": true,
        "lure_attraction": true,
        "lure_max_distance": 2000,
        "walker": "StepWalker",
        "log_interval": 5
      }
    }
   ```

   Result:

    2016-08-26 11:43:18,199 [MoveToFort] [INFO] [moving_to_fort] Moving towards pokestop ... - 0.07km
    2016-08-26 11:43:23,641 [MoveToFort] [INFO] [moving_to_fort] Moving towards pokestop ... - 0.06km
    2016-08-26 11:43:28,198 [MoveToFort] [INFO] [moving_to_fort] Moving towards pokestop ... - 0.05km

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

Default configuration will catch all Pokémon.

```"any": {"catch_above_cp": 0, "catch_above_iv": 0, "logic": "or"}```

You can override the global configuration with Pokémon-specific options, such as:

```"Pidgey": {"catch_above_cp": 0, "catch_above_iv": 0.8", "logic": "and"}``` to only catch Pidgey with a good roll.

Additionally, you can specify always_catch and never_catch flags.

For example: ```"Pidgey": {"never_catch": true}``` will stop catching Pidgey entirely.

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

```"release": {"any": {"keep_best_cp": 2}}```, ```"release": {"any": {"keep_best_cp": 10}}``` - can be any number. In the latter case for every pokemon type bot will keep no more that 10 best CP pokemon.

If you wish to limit your pokemon bag as a whole, not type-wise, use `all`:
```"release": {"all": {"keep_best_cp": 200}}```. In this case bot looks for 200 best CP pokemon in bag independently of their type. For example, if you have 150 Snorlax with 1500 CP and 100 Pidgeys with CP 100, bot will keep 150 Snorlax and 50 Pidgeys for a total of 200 best CP pokemon.

### Keep the best custom pokemon configuration (dev branch)
[[back to top](#table-of-contents)]

Define a list of criteria to keep the best Pokemons according to those criteria.

The list of criteria is the following:```'cp','iv', 'iv_attack', 'iv_defense', 'iv_stamina', 'moveset.attack_perfection', 'moveset.defense_perfection', 'hp', 'hp_max'```

#### Examples:

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
    "nickname_template": "{iv_pct}-{iv_ads}",
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
"use_pinap_on_vip": false,
"pinap_on_level_below": 0,
"pinap_operator": "or",
"pinap_ignore_threshold": false,
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
`use_pinap_on_vip` | Use pinap berry instead of razz berry on on VIP pokemon. The bot will use razz berry if pinap berry has run out
`pinap_on_level_below` | Set at what level (and below) of the pokemon should Pinap berry br use on. Set to 0 to disable use of pinap berry
`pinap_operator` | Set if Pinap berry going to be use together with "use_pinap_on_vip" or without (Operator "or", "and")
`pinap_ignore_threshold` | Set if bot is going to ignore catch rate threshold when using pinap berry
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

## CatchLimiter Settings
[[back to top](#table-of-contents)]

These settings define thresholds and duration to disable all catching tasks for a specified duration when balls are low. This allows your bot to spend time moving/looting and recovering balls spent catching.

## Default Settings

```
"enabled": false,
"min_balls": 20,
"duration": 15
```

### Settings Description
[[back to top](#table-of-contents)]

Setting | Description
---- | ----
`enabled` | Specify whether this task should run or not
`min_balls` | Determine minimum ball level required for catching tasks to be enabled
`duration` | How long to disable catching

Catching will be disabled when balls on hand reaches/is below "min_balls" and will be re-enabled when "duration" is reached, or when balls on hand > min_balls (whichever is later)

## Sniping _(MoveToLocation)_
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

This task will fetch current pokemon spawns from /raw_data of an PokemonGo-Map instance. For information on how to properly setup PokemonGo-Map have a look at the Github page of the project [here](https://github.com/PokemonGoMap/PokemonGo-Map). There is an example config in `config/config.json.map.example`

### Options
[[back to top](#table-of-contents)]

* `Address` - Address of the webserver of PokemonGo-Map. ex: `http://localhost:5000`
* `Mode` - Which mode to run sniping on
   - `distance` - Will move to the nearest pokemon
   - `priority` - Will move to the pokemon with the highest priority assigned (tie breaking by distance)
* `prioritize_vips` - Will prioritize vips in distance and priority mode above all normal pokemon if set to true
* `min_time` - Minimum time the pokemon has to be available before despawn
* `min_ball` - Minimum amount of balls required to run task
* `max_sniping_distance` - Maximum distance the pokemon is allowed to be caught when sniping. (m)
* `max_walking_distance` - Maximum distance the pokemon is allowed to be caught when sniping is turned off. (m)
* `snipe`:
   - `True` - Will teleport to target pokemon, encounter it, teleport back then catch it
   - `False` - Will walk normally to the pokemon
* `update_map` - disable/enable if the map location should be automatically updated to the bots current location
* `catch` - A dictionary of pokemon to catch with an assigned priority (higher => better)
* `snipe_high_prio_only` - Whether to snipe pokemon above a certain threshold.
* `snipe_high_prio_threshold` - The threshold number corresponding with the `catch` dictionary.
*   - Any pokemon above this threshold value will be caught by teleporting to its location, and getting back to original location if `snipe` is `True`.
*   - Any pokemon under this threshold value will make the bot walk to the Pokemon target whether `snipe` is `True` or `False`.
*   `max_extra_dist_fort` : Percentage of extra distance allowed to move to a fort on the way to the targeted Pokemon
*   `debug` : Output additional debugging information
*   `skip_rounds` : Try to snipe every X rounds
*   `update_map_min_distance_meters` : Update map if more than X meters away
*   `update_map_min_time_sec` : Update map if older than X seconds
*   `snipe_sleep_sec` : Sleep for X seconds after snipes
*   `snipe_max_in_chain` : Maximum snipes in chain

#### Example
[[back to top](#table-of-contents)]

```
{
  \\ ...
  {
    "type": "MoveToMapPokemon",
    "config": {
      "address": "http://localhost:5000",
      "//NOTE: Change the max_sniping_distance to adjust the max sniping range (m)": {},
      "max_sniping distance": 10000,
      "//NOTE: Change the max_walking_distance to adjust the max walking range when snipe is off (m)": {},
      "max__walking_distance": 500,
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

## Sniper
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

This task is an upgrade version of the MoveToMapPokemon task. It will fetch pokemon informations from any number of urls (sources), including PokemonGo-Map, or from the social feature. You can also use the old PokemonGo-Map project. For information on how to properly setup PokemonGo-Map have a look at the Github page of the project [here](https://github.com/PokemonGoMap/PokemonGo-Map). You can also use [this](https://github.com/YvesHenri/PogoLocationFeeder), which is an adapted version of the application that NecroBot used to snipe. There is an example config in `config/config.json.map.example`.

### Options
[[back to top](#table-of-contents)]

* `enabled` - Defines whether the **WHOLE** task is enabled or not. Please bear in mind that even if the task is enabled, all or any of its sources can be disabled. (default: false)
* `mode` - The mode on which the sniper will fetch the informations. (default: social)
   - `social` - Information will come from the social network.
   - `url` - Information will come from one or multiple urls.
   - `telegram` - Manual snipping through telegram.  In telegram, use "/snipe <PokemonName> <Lat> <Lng>" to snipe. Subscript to "/sub sniper_log" and "/sub pokemon_vip_caught" to retrieve snipping results through telegram.
* `bullets` - Each bullet corresponds to an **ATTEMPT** of catching a pokemon. (default: 1)
* `homing_shots` - This will ensure that each bullet **will catch** a target. If disabled, a target might not exist and thus it wont be caught. When enabled, this will jump to the next target (if any) and try again to catch it. This will be repeated untill you've spent all the bullets. (default: true)
* `special_iv` - This will skip the catch list if the value is greater than or equal to the target's IV. This currently does not work with `social` mode and only works if the given `url` has this information. (default: 100)
* `time_mask` - The time mask used (if `expiration.format` is a full date). The default mask is '%Y-%m-%d %H:%M:%S'.
* `cooldown_enabled` - Do we set the sniper on a cool down of a random time after snipping? This might help avoiding bans.
* `loiter_after_snipe` - Do we wait a random time after sniping (aside of the above cooldown)? This might also help avoiding bans.
* `order` - The order on which you want to snipe. This can be one or multiple of the following values (default: [`missing`, `vip`, `priority`]):
   - `iv` - Order by IV, if any. See `special_iv`.
   - `vip` - Order by VIP.
   - `missing` - Order by the target's pokedex missing status.
   - `priority` - Order by the priority you have specified in the `catch` list.
   - `expiration_timestamp_ms` - Order by the expiration time.
* `sources` - This should map a JSON param values from a given url. For example: different urls will provide different JSON response formats. **PLEASE ADVISED THAT, IF A PARAM DOES NOT EXIST (OR CONTAINS WRONG DATA LIKE PokeSnipers's ID PARAM), DO NOT SPECIFY IT!** Pokesnipers is a special case where it does provide IDs, however theyre wrong. Map bellow their corresponding values:
* `sources.key` - The JSON key that contains the results, eg.: For a JSON response such as `{ "SomeWeirdoName": [{"id": 123, ...}, {"id": 143, ...}]}`, `SomeWeirdoName` would be the key name.
* `sources.url` - The URL that will provide the JSON.
* `sources.enabled` - Defines whether this source is enabled or not. This has nothing to do with the task's `enabled`.
* `sources.timeout` - How long to wait for this source to respond before giving up (default 5 seconds)
* `mappings`- Map JSON parameters to required values.
   - `iv` - The JSON param that corresponds to the pokemon IV. Only certain sources provide this info. **NOTE:** `social` mode does not provide this info!
   - `id` - The JSON param that corresponds to the pokemon ID. (required)
   - `name` - The JSON param that corresponds to the pokemon name. (required)
   - `latitude` - The JSON param that corresponds to the latitude. It will work if a single param is used for both `latitude` and `longitude`, eg.: "coords": "1.2345, 6.7890" (required)
   - `longitude` - The JSON param that corresponds to the longitude. It will work if a single param is used for both `latitude` and `longitude`, eg.: "coords": "1.2345, 6.7890" (required)
   - `encounter` - The JSON param that corresponds to encounter ID. This value is very unlikely to be provided by third-party urls. However, it is safely updated internally.
   - `spawnpoint` - The JSON param that corresponds to spawnpoint ID. This value is very unlikely to be provided by third-party urls. However, it is safely updated internally.
   - `expiration` - The JSON param that correspond to the pokemon expiration time.
   - `expiration.format` - The time type. It can be either seconds, milliseconds or utc
* `catch` - A dictionary of pokemon to catch with an assigned priority (higher => better).

#### Example
[[back to top](#table-of-contents)]

```
{
    "type": "Sniper",
    "config": {
        "enabled": true,
        "mode": "url",
        "bullets": 1,
        "homing_shots": true,
        "special_iv": 100,
        "order": ["missing", "iv", "priority", "vip"],
        "sources": [
            {
                "url": "http://pokesnipers.com/api/v1/pokemon.json",
                "enabled": true,
                "timeout": 15,
                "key": "results",
                "mappings": {
                    "iv": { "param": "iv" },
                    "name": { "param": "name" },
                    "latitude": { "param": "coords" },
                    "longitude": { "param": "coords" },
                    "expiration": { "param": "until", "format": "utc" }
                }
            },
            {
                "url": "http://localhost:5000/raw_data",
                "key": "pokemons",
                "enabled": true,
                "timeout": 5,
                "mappings": {
                    "id": { "param": "pokemon_id" },
                    "name": { "param": "pokemon_name" },
                    "latitude": { "param": "latitude" },
                    "longitude": { "param": "longitude" },
                    "expiration": { "param": "disappear_time", "format": "milliseconds" }
                }
            },
            {
                "url": "https://pokewatchers.com/grab/",
                "enabled": true,
                "timeout": 15,
                "mappings": {
                    "iv": { "param": "iv" },
                    "id": { "param": "pid" },
                    "name": { "param": "pokemon" },
                    "latitude": { "param": "cords" },
                    "longitude": { "param": "cords" },
                    "expiration": { "param": "timeend", "format": "seconds" }
                }
            }
        ],
        "catch": {
            "Snorlax": 1000,
            "Dragonite": 1000,
            "Growlithe": 600,
            "Clefairy": 500,
            "Kabuto": 500,
            "Dratini": 500,
            "Dragonair": 500,
            "Mr. Mime": 500,
            "Magmar": 500,
            "Electabuzz": 500,
            "Tangela": 500,
            "Tauros": 500,
            "Primeape": 500,
            "Chansey": 500,
            "Pidgey": 100,
            "Caterpie": 100,
            "Weedle": 100
        }
    }
  }
```

## FollowPath Settings
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

Walk to the specified locations loaded from .gpx or .json file. It is highly
recommended to use website such as [GPSies](http://www.gpsies.com) which allow
you to export your created track in JSON file. Note that you'll have to first
convert its JSON file into the format that the bot can understand. See [Example
of pier39.json] below for the content. I had created a simple python script to
do the conversion.

The `location` fields in the `.json` file can also contain a street address. In
this case the `location` is interpreted by the Google Maps API.

The json file can contain for each point an optional `wander` field. This
indicated the number of seconds the bot should wander after reaching the point.
During this time, the next Task in the configuration file is executed, e.g. a
MoveToFort task. This allows the bot to walk around the waypoint looking for
forts for a limited time.

The `loiter` field, also optional for each point in the json file, works
similarly to the `wander` field. The difference is that with `loiter` the
next `Task` in the configuration file is /not/ executed, meaning the bot
will wait, without moving, at the point in the json file with the `loiter`
option.

### Options
[[back to top](#table-of-contents)]
* `path_mode` - linear, loop, single
   - `loop` - The bot will walk along all specified waypoints and then move directly to the first waypoint again.
   - `linear` - The bot will turn around at the last waypoint and along the given waypoints in reverse order.
   - `single` - The bot will walk the path only once.
* `path_start_mode` - first, closest
   - `first` - The bot will start at the first point of the path.
   - `closest` - The bot will start the path at the point which is the closest to the current bot location.
* `path_file` - "/path/to/your/path.json"
* `disable_location_output` - true,false. Set to true if you do not want to see follow path updating information. Default false.

### Notice
If you use the `single` `path_mode` without e.g. a `MoveToFort` task, your bot
with /not move at all/ when the path is finished. Similarly, if you use the
`wander` option in your json path file without a following `MoveToFort` or
similar task, your bot will not move during the wandering period. Please
make sure, when you use `single` mode or the `wander` option, that another
move-type task follows the `FollowPath` task in your `config.json`.

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

## UpdateHashStats Settings
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

Periodically displays the hash stats in the terminal.

### Options
[[back to top](#table-of-contents)]

* `min_interval` : The minimum interval at which the stats are displayed, in seconds (defaults to 60 seconds). The update interval cannot be accurate as workers run synchronously.
* `stats` : An array of items to display and their display order (implicitly), see available items below (defaults to ["period", "remaining", "maximum", "expiration"]).

### Sample configuration
[[back to top](#table-of-contents)]
```json
{
    "type": "UpdateHashStats",
    "config": {
        "enabled": true,
        "min_interval": 60,
        "stats": ["period", "remaining", "maximum", "expiration"]
    }
}
```

### Example console output
[[back to top](#table-of-contents)]
```
[2017-04-03 17:55:15] [MainThread] [UpdateHashStats] [INFO] Period: 2017-04-03 09:56:37 | Remaining: 147 | Maximum: 150 | Expiration: 2017-04-15 06:21:11
```

## Random Pause
[[back to top](#table-of-contents)]

Pause the execution of the bot at a random time for a random time.

Simulates the random pause of the day (speaking to someone, getting into a store, ...) where the user stops the app. The interval between pauses and the duration of pause are configurable.

- `min_duration`: (HH:MM:SS) the minimum duration of each pause
- `max_duration`: (HH:MM:SS) the maximum duration of each pause
- `min_interval`: (HH:MM:SS) the minimum interval between each pause
- `max_interval`: (HH:MM:SS) the maximum interval between each pause

### Example Config
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

## Egg Incubator
[[back to top](#table-of-contents)]

Configure how the bot should use the incubators.

- `infinite_longer_eggs_first`: (True | False ) should the bot start by the longer eggs first for the unbreakable incubator. If set to true, the bot first use the 10km eggs, then the 5km eggs, then the 2km eggs.
- `breakable_longer_eggs_first`: (True | False ) should the bot start by the longer eggs first for the breakable incubator. If set to true, the bot first use the 10km eggs, then the 5km eggs, then the 2km eggs.
- `infinite`: ([2], [2,5], [2,5,10], []) the type of egg the infinite (ie. unbreakable) incubator(s) can incubate. If set to [2,5], the incubator(s) can only incubate the 2km and 5km eggs. If set to [], the incubator(s) will not incubate any type of egg.
- `breakable`: ([2], [2,5], [2,5,10], []) the type of egg the breakable incubator(s) can incubate. If set to [2,5], the incubator(s) can only incubate the 2km and 5km eggs. If set to [], the incubator(s) will not incubate any type of egg.

### Example Config
```
{
  "type": "IncubateEggs",
    "config": {
    "infinite_longer_eggs_first": false,
    "breakable_longer_eggs_first": true,
    "infinite": [2,5],
    "breakable": [10]
  }
}
```

## ShowBestPokemon
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

Periodically displays the user best pokemon in the terminal.

### Options
[[back to top](#table-of-contents)]

* `min_interval` : The minimum interval at which the pokemon are displayed, in seconds (defaults to 120 seconds). The update interval cannot be accurate as workers run synchronously.
* `amount` : Amount of pokemon to show.
* `order_by` : Stat that will be used to get best pokemons.
Available Stats: 'cp', 'iv', 'ivcp', 'ncp', 'dps', 'hp', 'level'
* `info_to_show` : Info to show for each pokemon

Available `info_to_show` :
```
'cp',
'iv_ads',
'iv_pct',
'ivcp',
'ncp',
'level',
'hp',
'moveset',
'dps'
```

### Sample configuration
[[back to top](#table-of-contents)]
```json
{
    "type": "ShowBestPokemon",
    "config": {
        "enabled": true,
        "min_interval": 60,
        "amount": 5,
        "order_by": "cp",
        "info_to_show": ["cp", "ivcp", "dps"]
    }
}
```

### Example console output
[[back to top](#table-of-contents)]
```
2016-08-25 21:20:59,642 [ShowBestPokemon] [INFO] [show_best_pokemon] [Tauros, CP 575, IVCP 0.95, DPS 12.04] | [Grimer, CP 613, IVCP 0.93, DPS 13.93] | [Tangela, CP 736, IVCP 0.93, DPS 14.5] | [Staryu, CP 316, IVCP 0.92, DPS 10.75] | [Gastly, CP 224, IVCP 0.9, DPS 11.7]
```

## Telegram Task
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

[Telegram bot](https://telegram.org/) Announcer Level up, pokemon cought

Bot answer on command '/info' self stats.

### Options

* `telegram_token` : bot token (getting [there](https://core.telegram.org/bots#6-botfather) - one token per bot)
* `master` : id (without quotes) of bot owner, who will get alerts and may issue commands or a (case-sensitive!) user name.
* `alert_catch` : dict of rules pokemons catch.
* `password` : a password to be used to authenticate to the bot

The bot will only alert and respond to a valid master. If you're unsure what this is, send the bot a message from Telegram and watch the log to find out.

### Sample configuration
[[back to top](#table-of-contents)]
```json
{
    "type": "TelegramTask",
    "config": {
        "enabled": true,
        "master": 12345678,
        "alert_catch": {
          "all": {"operator": "and", "cp": 1300, "iv": 0.95},
          "Snorlax": {"operator": "or", "cp": 900, "iv": 0.9}
        },
        "password": "alwoefhq348"
    }
}
```

## Discord Task
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

[Discord bot](https://discordapp.com/) Announcer Level up, pokemon cought

Bot answer on command '/info' self stats.

### Options

* `discord_token` : bot token (getting [tutorial](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token) - one token per bot)
* `master` : username with discriminator of bot owner('user#1234') , who will get alerts and may issue commands or a (case-sensitive!) user name.
* `alert_catch` : dict of rules pokemons catch.

The bot will only alert and respond to a valid master. If you're unsure what this is, send the bot a message from Discord and watch the log to find out.

### Sample configuration
[[back to top](#table-of-contents)]
```json
{
    "type": "DiscordTask",
    "config": {
        "enabled": true,
        "master": "user#1234",
        "alert_catch": {
          "all": {"operator": "and", "cp": 1300, "iv": 0.95},
          "Snorlax": {"operator": "or", "cp": 900, "iv": 0.9}
        }
    }
}
```

## CompleteTutorial
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

Completes the tutorial:

* Legal screen
* Avatar selection
* First Pokemon capture
* Set nickname
* Firte time experience
* Pick team at level 5


### Options
[[back to top](#table-of-contents)]

* `nickname` : Nickname to be used ingame.
* `team` : `Default: 0`. Team to pick after reaching level 5.

Available `team` :
```
0: Neutral (No team)
1: Blue (Mystic)
2: Red (Valor)
3: Yellow (Instinct)
```

### Sample configuration
[[back to top](#table-of-contents)]
```json
{
  "type": "CompleteTutorial",
  "config": {
  "enabled": true,
    "nickname": "PokemonGoF",
    "team": 2
  }
}
```

## BuddyPokemon
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

Makes use of the Pokemon Buddy system.
It's able to switch the buddy automatically given an list of pokemon that should be using this feature.
Periodically logs the status of the buddy walking.
After setting a buddy it's not possible to remove it, only change it. So if a buddy is already selected and no buddy list is given, it will still run with the buddy already selected.

### Options
[[back to top](#table-of-contents)]

* `buddy_list`: `Default: []`. List of pokemon names that will be used as buddy. If '[]' or 'none', will not use or change buddy.
* `best_in_family`: `Default: True`. If True, picks best Pokemon in the family (sorted by cp).
* `candy_limit`: `Default: 0`. Set the candy limit to be rewarded per buddy, when reaching this limit the bot will change the buddy to the next in the list. When candy_limit = 0 or only one buddy in list, it has no limit and never changes buddy.
* `candy_limit_absolute`: `Default: 0`. Set the absolute candy limit to be rewarded per buddy, when reaching this limit the bot will change the buddy to the next in the list. When candy_limit_absolute = 0 or only one buddy in list, it has no limit and never changes buddy. Use this to stop collecting candy when a candy threshold for your buddy's pokemon family is reached (e.g. 50 for evolving).
* `force_first_change`: `Default: False`. If True, will try to change buddy at bot start according to the buddy list. If False, will use the buddy already set until candy_limit is reached and then use the buddy list.
* `buddy_change_wait_min`: `Default: 3`. Minimum time (in seconds) that the buddy change takes.
* `buddy_change_wait_max`: `Default: 5`. Maximum time (in seconds) that the buddy change takes.
* `min_interval`: `Default: 120`. Time (in seconds) to periodically log the buddy walk status.

### Sample configuration
[[back to top](#table-of-contents)]
```json
{
  "type": "BuddyPokemon",
    "config": {
      "enabled": true,
        "buddy_list": "dratini, magikarp",
        "best_in_family": true,
        "// candy_limit = 0 means no limit, so it will never change current buddy": {},
        "candy_limit": 0,
        "candy_limit_absolute": 0,
        "// force_first_change = true will always change buddy at start removing current one": {},
        "force_first_change": false,
        "buddy_change_wait_min": 3,
        "buddy_change_wait_max": 5,
        "min_interval": 120
  }
}
```

## PokemonHunter
[[back to top](#table-of-contents)]

### Description
[[back to top](#table-of-contents)]

Hunts down nearby Pokemon. Searches for Pokemon to complete the Pokedex, or if a Pokemon is a VIP. Can be set to hunt ALL nearby Pokemon

### Options
[[back to top](#table-of-contents)]

* `max_distance`: `Default: 2000`. Maxium of meters for the "nearby" part.
* `hunt_all`: `Default: false`. Should we hunt for ALL nearby Pokemon?
* `hunt_vip`: `Default: true`. Should we hunt for VIP Pokemon?
* `hunt_pokedex`: `Default: true`. Should we hunt for Pokemon we need to complete the Pokedex (make family complete)
* `lock_on_target`: `Default: false`. Should we ignore all other Pokemon while hunting?
* `lock_vip_only`: `Default: true`. Is the above only used for real VIPs? (Not to complete the Pokedex)
* `disabled_while_camping`: `Default: true`. Should we stop hunting for nearby Pokemon while sitting at lures?
* `treat_unseen_as_vip`: `Default: true`. Should we treat unseen Pokemons as VIPs?

### Sample configuration
[[back to top](#table-of-contents)]
```json
{
    "type": "PokemonHunter",
    "config": {
        "enabled": true,
        "max_distance": 1500,
        "hunt_all": false,
        "hunt_vip": true,
        "hunt_pokedex": true,
        "lock_on_target": false,
        "lock_vip_only": true,
        "disabled_while_camping": true,
        "treat_unseen_as_vip": true
    }
}
```
