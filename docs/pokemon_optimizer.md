# Pokemon Optimizer
- [About](#about)
- [Configuration](#configuration)
    - [Default configuration](#default-configuration)
    - [Understand parameters](#understand-parameters)
        - [enabled](#enabled)
        - [bulktransfer_enabled](#bulktransfer_enabled)
        - [max_bulktransfer](#max_bulktransfer)
        - [min_slots_left](#min_slots_left)
        - [action_wait_min](#action_wait_min)
        - [action_wait_max](#action_wait_max)
        - [transfer](#transfer)
        - [evolve](#evolve)
        - [evolve_to_final](#evolve_to_final)
        - [evolve_time](#evolve_time)
        - [evolve_for_xp](#evolve_for_xp)
        - [evolve_only_with_lucky_egg](#evolve_only_with_lucky_egg)
        - [evolve_count_for_lucky_egg](#evolve_count_for_lucky_egg)
        - [may_use_lucky_egg](#may_use_lucky_egg)
        - [may_evolve_favorites](#may_evolve_favorites)
        - [may_upgrade_favorites](#may_upgrade_favorites)
        - [may_unfavor_pokemon](#may_unfavor_pokemon)
        - [upgrade](#upgrade)
        - [upgrade_level](#upgrade_level)
        - [groups](#groups)
        - [rules](#rules)
            - [mode](#rule-mode)
            - [names](#rule-names)
            - [top](#rule-top)
            - [sort](#rule-sort)
            - [keep](#rule-keep)
            - [evolve](#rule-evolve)
            - [upgrade](#rule-upgrade)
            - [buddy](#rule-buddy)
            - [favorite](#rule-favorite)
- [Eevee case](#eevee-case)
- [FAQ](#faq)

# About
The Pokemon Optimizer manage buddy, transfer, evolution and upgrade of your Pokemon.
<br>It can replace or complement the classical Evolve and Transfer tasks.
<br>Transfer, evolution and upgrade will be triggered when you bag of Pokemon is full.

The Pokemon Optimizer will first Transfer, then Evolve, then Upgrade.
There is only one pass at each action.

It will also collect the candies from your Buddy and select the next buddy.

In case that logging will be enabled, look for .log file in data folder.

[[back to top](#pokemon-optimizer)]

# Configuration
## Default configuration
```json
{
    "tasks": [
        {
            "type": "PokemonOptimizer",
            "config": {
                "enabled": true,
                "bulktransfer_enabled": False,
                "max_bulktransfer": 10,
                "min_slots_left": 5,
                "action_wait_min": 3,
                "debug": false,
                "action_wait_max": 5,
                "transfer": true,
                "evolve": true,
                "evolve_to_final": true,
                "evolve_time": 25,
                "evolve_for_xp": true,
                "evolve_only_with_lucky_egg": false,
                "evolve_count_for_lucky_egg": 80,
                "may_use_lucky_egg": true,
                "may_evolve_favorites": true,
                "may_upgrade_favorites": true,
                "may_unfavor_pokemon": false,
                "upgrade": true,
                "upgrade_level": 30,
                "groups": {
                    "gym": ["Dragonite", "Snorlax", "Lapras", "Arcanine"]
                },
                "rules": [
                    {
                        "// Of all Pokemon with less than 124 candies, buddy the Pokemon having the highest maximum cp": {},
                        "mode": "overall",
                        "top": 1,
                        "sort": ["max_cp", "cp"],
                        "keep": {"candy": -124},
                        "evolve": false,
                        "buddy": true
                    },
                    {
                        "// Buddy the Pokemon having the less candies. In case no Pokemon match first rule": {},
                        "mode": "overall",
                        "top": 1,
                        "sort": ["-candy", "max_cp", "cp"],
                        "evolve": false,
                        "buddy": true
                    },
                    {
                        "mode": "by_pokemon",
                        "names": ["gym"],
                        "top": 3,
                        "sort": ["iv", "ncp"],
                        "evolve": {"iv": 0.9, "ncp": 0.9},
                        "upgrade": {"iv": 0.9, "ncp": 0.9}
                    },
                    {
                        "// Keep best iv of each family and evolve it if its iv is greater than 0.9": {},
                        "mode": "by_family",
                        "top": 1,
                        "sort": ["iv"],
                        "evolve": {"iv": 0.9}
                    },
                    {
                        "// Keep best ncp of each family and evolve it if its ncp is greater than 0.9": {},
                        "mode": "by_family",
                        "top": 1,
                        "sort": ["ncp"],
                        "evolve": {"ncp": 0.9}
                    },
                    {
                        "// Keep best cp of each family but do not evolve it": {},
                        "mode": "by_family",
                        "top": 1,
                        "sort": ["cp"],
                        "evolve": false
                    },
                    {
                        "// For Pokemon of final evolution and with iv greater than 0.9, keep the best dps_attack": {},
                        "mode": "by_pokemon",
                        "names": ["!with_next_evolution"],
                        "top": 1,
                        "sort": ["dps_attack", "iv"],
                        "keep": {"iv": 0.9}
                    }
                ]
            }
        }
    ]
}
```

[[back to top](#pokemon-optimizer)]

## Understand parameters
### enabled
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `enabled` | `true`, `false` | `true`  |

Enable or disable the task.

[[back to top](#pokemon-optimizer)]

### bulktransfer_enabled
| Parameter              | Posible values  | Default |
|------------------------|-----------------|---------|
| `bulktransfer_enabled` | `true`, `false` | `false` |

Enable bulktransfer pokemon for faster transfer.

[[back to top](#pokemon-optimizer)]

### max_bulktransfer
| Parameter          | Posible values  | Default |
|--------------------|-----------------|---------|
| `max_bulktransfer` | `[0-100]`       | `10`    |

Maximum bulktransfer pokemon at a time.

[[back to top](#pokemon-optimizer)]

### min_slots_left
| Parameter        | Possible values | Default |
|------------------|-----------------|---------|
| `min_slots_left` | `[0-N]`         | `5`     |

The Pokemon Optimizer will be triggered when you have that number (or less) empty slots in your Pokemon Bag.
<br>If this number is higher than your total bag capacity, the Pokemon Optimizer will run each time there is a Pokemon to either transfer, evolve or upgrade.

[[back to top](#pokemon-optimizer)]

### action_wait_min
| Parameter           | Possible values | Default |
|---------------------|-----------------|---------|
| `action_wait_min`   | `[0-N]`         | `3`     |

This is the minimum time to wait after performing an action in the inventory like transferring, upgrading etc.

[[back to top](#pokemon-optimizer)]

### action_wait_max
| Parameter           | Possible values | Default |
|---------------------|-----------------|---------|
| `action_wait_max`   | `[0-N]`         | `5`     |

This is the maximum time to wait after performing an action in the inventory like transferring, upgrading etc.

[[back to top](#pokemon-optimizer)]

### transfer
| Parameter  | Possible values | Default |
|------------|-----------------|---------|
| `transfer` | `true`, `false` | `false` |

The `transfer` parameter activate or deactivate the transfer of Pokemon.

At `true`, you allow the Pokemon Optimizer to transfer every Pokemon that are not good enough to be kept according to your criteria.
<br>At `false`, and regardless of other parameters, no Pokemon is ever going to be transfered.

Note that in test mode, you can see logs explaining which Pokemon would be transfered in non-test mode.
<br>It can help you rectify your configuration or guide you during manual transfer.

```
Exchanged Magikarp [IV 0.4] [CP 69] [481 candies]
```

[[back to top](#pokemon-optimizer)]

### evolve
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `evolve`  | `true`, `false` | `true`  |

The `evolve` parameter activate or deactivate the evolution of Pokemon.

At `true`, you allow the Pokemon Optimizer to evolve every Pokemon that is meeting the evolution criteria.
<br>You also allow it to evolve lower quality Pokemon when [`evolve_for_xp`](#evolve_for_xp) parameter is activated.
<br>At `false`, and regardless of other parameters, no Pokemon is ever going to be evolved.

Note that in test mode, you can see logs explaining which Pokemon would be evolved in non-test mode.
<br>It can help you rectify your configuration or guide you during manual evolution.

```
Evolved Magikarp [IV 0.96] [CP 231] [+1000 xp] [82 candies]
```

[[back to top](#pokemon-optimizer)]

### evolve_to_final
| Parameter         | Possible values | Default |
|-------------------|-----------------|---------|
| `evolve_to_final` | `true`, `false` | `true`  |

Choose whether or not you want to wait to have enough candies to evolve Pokemon to their final evolution.

At `true`, it is only when you have enough candies that your best Pokemon will be evolved directly to their final evolution.
<br>At `false`, your best Pokemon are allowed to evolve progressively.

```
Evolving 2 Pokemon (the best)
Evolved Weedle [IV 0.91] [CP 246] [60 candies] [+500 xp]
Evolved Kakuna [IV 0.91] [CP 265] [11 candies] [+500 xp]
```

[[back to top](#pokemon-optimizer)]

### evolve_time
| Parameter     | Possible values | Default |
|---------------|-----------------|---------|
| `evolve_time` | `[0-N]`         | `25`    |

This is the duration of the evolution animation and time to wait after performing an evolution.
<br>The actual time used is randomized between more or less 10% of the parameter value.

[[back to top](#pokemon-optimizer)]

### evolve_for_xp
| Parameter       | Possible values       | Default |
|-----------------|-----------------------|---------|
| `evolve_for_xp` | `true`, `false`, `[]` | `true`  |

Let you choose if you want the Pokemon Optimizer to use your candies to evolve low quality Pokemon.

At `false`, low quality Pokemon get transferred normally following your rules.
At `true`, this option is restricted to the following list of 18 Pokemon:

|     |     |     |     |     |     |
|:---:|:---:|:---:|:---:|:---:|:---:|
| `#010`<br>`Caterpie`  | `#013`<br>`Weedle` | `#016`<br>`Pidgey`  | `#019`<br>`Rattata` | `#029`<br>`Nidoran F` | `#032`<br>`Nidoran M` |
| `#041`<br>`Zubat`     | `#043`<br>`Oddish` | `#046`<br>`Paras`   | `#048`<br>`Venonat` | `#054`<br>`Psyduck`   | `#072`<br>`Tentacool` |
| `#081`<br>`Magnemite` | `#098`<br>`Krabby` | `#100`<br>`Voltorb` | `#118`<br>`Goldeen` | `#120`<br>`Staryu`    | `#133`<br>`Eevee`     |

You can also define `evolve_for_xp` as a list of Pokemon names or Pokemon [`groups`](#groups).
<br>For example: `"evolve_for_xp": ["Caterpie", "Weedle", "Pidgey"]`

Better quality Pokemon have priority for evolution and the Pokemon Optimizer will never evolve for xp if a better Pokemon is waiting for candies to evolve.
<br>These low quality Pokemon will only be used if you have plenty of candies left after evolving your best Pokemon.

```
Evolving 50 Pokemon (for xp)
Evolved Caterpie [IV 0.62] [CP 58] [574 candies] [+500 xp]
Evolved Caterpie [IV 0.6] [CP 301] [563 candies] [+500 xp]
Evolved Caterpie [IV 0.6] [CP 270] [552 candies] [+500 xp]
Evolved Caterpie [IV 0.53] [CP 245] [541 candies] [+500 xp]
Evolved Caterpie [IV 0.53] [CP 25] [530 candies] [+500 xp]
Evolved Caterpie [IV 0.51] [CP 46] [519 candies] [+500 xp]
...
```

[[back to top](#pokemon-optimizer)]

### evolve_only_with_lucky_egg
| Parameter                    | Possible values | Default |
|------------------------------|-----------------|---------|
| `evolve_only_with_lucky_egg` | `true`, `false` | `false` |

Force the Pokemon Optimizer to wait that a lucky egg is available to perform evolution.
<br>It is advised to keep this parameter to `false` since it is quite restrictive.
<br>You do not always have a lucky egg available and you still need to clean up your bag to make place for new Pokemon.

At `true`, no evolution will be performed unless we have an available lucky egg to use before.

[[back to top](#pokemon-optimizer)]

### evolve_count_for_lucky_egg
| Parameter                    | Possible values | Default |
|------------------------------|-----------------|---------|
| `evolve_count_for_lucky_egg` | `[0-N]`         | `80`    |

If you allow the Pokemon Optimizer to use a lucky egg, this parameter let you define the minimum number of Pokemon that must evolve when using a lucky egg.

If a lucky egg is available, the Pokemon Optimizer is going to wait that number is reached to perform evolution.
<br>If you do not have any available lucky egg, the Pokemon Optimizer will ignore this parameter and evolution will be performed without lucky egg.
<br>It may take long time before reaching that number.

[[back to top](#pokemon-optimizer)]

### may_use_lucky_egg
| Parameter           | Possible values | Default |
|---------------------|-----------------|---------|
| `may_use_lucky_egg` | `true`, `false` | `true`  |

Define whether you allow the Pokemon Optimizer to use a lucky egg before evolving Pokemon or not.
<br>At `true`, and if a lucky egg is available, the Pokemon Optimizer will wait for the [`evolve_count_for_lucky_egg`](#evolve_count_for_lucky_egg) Pokemon to use the lucky egg.
<br>At `false`, or when no luck egg is available, no lucky egg will be used.

[[back to top](#pokemon-optimizer)]

### may_evolve_favorites
| Parameter           | Possible values | Default |
|---------------------|-----------------|---------|
| `may_evolve_favorites` | `true`, `false` | `true`  |

Define whether you allow the Pokemon Optimizer to evolve favorite Pokemon or not.
<br>At `true`, the Pokemon Optimizer will evolve favorite Pokemon according to the rules.
<br>At `false`, the Pokemon Optimizer will not evolve favorite Pokemon.

[[back to top](#pokemon-optimizer)]

### may_upgrade_favorites
| Parameter           | Possible values | Default |
|---------------------|-----------------|---------|
| `may_upgrade_favorites` | `true`, `false` | `true`  |

Define whether you allow the Pokemon Optimizer to upgrade favorite Pokemon or not.
<br>At `true`, the Pokemon Optimizer will upgrade favorite Pokemon according to the rules.
<br>At `false`, the Pokemon Optimizer will not upgrade favorite Pokemon.

[[back to top](#pokemon-optimizer)]

### may_unfavor_pokemon
| Parameter           | Possible values | Default |
|---------------------|-----------------|---------|
| `may_unfavor_pokemon` | `true`, `false` | `false`  |

Define whether you allow the Pokemon Optimizer to unmark favorite Pokemon as favorite or not.
<br>At `true`, the Pokemon Optimizer will unmark favorite Pokemon if it no longer matches favorite rules.
<br>At `false`, the Pokemon Optimizer will not unmark favorite Pokemon.

[[back to top](#pokemon-optimizer)]

### upgrade
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `upgrade` | `true`, `false` | `false` |

The `upgrade` parameter activate or deactivate the upgrade (power-up) of Pokemon.

At `true`, you allow the Pokemon Optimizer to upgrade every Pokemon that is meeting the upgrade criteria.
<br>If `evolve` is also activated, evolution has priority over upgrade.
Which means that the Pokemon Optimizer is going to wait that a Pokemon is fully evolved before upgrading it.
<br>At `false`, and regardless of other parameters, no Pokemon is ever going to be upgraded.

Note that in test mode, you can see logs explaining which Pokemon would be upgraded in non-test mode.
<br>It can help you rectify your configuration or guide you during manual power-up.

`Upgraded Magikarp [IV 0.96] [CP 231] [81 candies] [132450 stardust]`

[[back to top](#pokemon-optimizer)]

### upgrade_level
| Parameter       | Possible values | Default |
|-----------------|-----------------|---------|
| `upgrade_level` | `[1-40]`        | `30`    |

This the maximum level at which you want the Pokemon Optimizer to upgrade your Pokemon.
<br>Pokemon upgrade level cannot be higher than `player level + 1.5` and cannot be higher than `40`.
The parameter value will be majored by `player level + 1.5` or `40` if it goes over that value.

Pokemon are either fully upgraded to the configured level or not upgraded at all.
The higher the level is, the more costly in candies and stardust it becomes to upgrade a Pokemon.

###### Cumulative upgrade cost (candy, stardust)

| From - To | 5         | 10          | 15          | 20          | 25          | 30            | 35            | 40            |
|-----------|:---------:|:-----------:|:-----------:|:-----------:|:-----------:|:-------------:|:-------------:|:-------------:|
| 1         | 8<br>2400 | 18<br>10000 | 36<br>23600 | 56<br>45000 | 84<br>76000 | 124<br>120000 | 188<br>182000 | 306<br>270000 |
| 5         |           | 10<br>7600  | 28<br>21200 | 48<br>42600 | 76<br>73600 | 116<br>117600 | 180<br>179600 | 298<br>267600 |
| 10        |           |             | 18<br>13600 | 38<br>35000 | 66<br>66000 | 106<br>110000 | 170<br>172000 | 288<br>260000 |
| 15        |           |             |             | 20<br>21400 | 48<br>52400 |  88<br>96400  | 152<br>158400 | 270<br>246400 |
| 20        |           |             |             |             | 28<br>31000 |  68<br>75000  | 132<br>137000 | 250<br>225000 |
| 25        |           |             |             |             |             |  40<br>44000  | 104<br>106000 | 222<br>194000 |
| 30        |           |             |             |             |             |               |  64<br>62000  | 182<br>150000 |
| 35        |           |             |             |             |             |               |               | 118<br>88000  |

[[back to top](#pokemon-optimizer)]

### groups
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `groups`  | (see below)     | `{}`    |

You can define `groups` of Pokemon to help you restrict rules to a specific set of Pokemon.
<br>You can then use these `groups` names in the [`names`](#rule-names) parameter of your rule to refer to list of Pokemon

`groups` are list of Pokemon names:
```json
"groups": {
    "gym": ["Dragonite", "Snorlax"],
    "my_love": ["Pikachu"],
    "vip": ["Lapras", "Arcanine", "Gyarados", "gym"],
    "trash": ["!vip", "!my_love"]
},
```

A same Pokemon name can appear in different `groups`. And `groups` may reference each others.
<br>Just like [`names`](#rule-names), you can also negate a group by preceding its name by a `!` or `-`.
<br>Including `groups` and negating others allow you to create group unions and/or intersections.

There is a few predifined group names that you can use in your configuration:
- `with_next_evolution`, target all Pokemon that can be evolved.
- `with_previous_evolution`, target all Pokemon that are the result of an evolution.

[[back to top](#pokemon-optimizer)]

### rules
| Parameter | Possible values | Default     |
|-----------|-----------------|-------------|
| `rules`   | `[]`            | (see below) |

This parameter is a list that contains as many element as you want.
<br>Each element of that list define a rule that select what Pokemon are the best.
<br>Each of these rules is going to be handled individually and will result in a list of Pokemon to keep.

The conjunction of all rules define the list of all Pokemon to keep.
Every Pokemon not selected is candidate for transfer.

The order in which the rule are defined may have an impact on the behavior.
Especially, if there not enough candies/stardust to evolve/upgrade all the selected Pokemon, the Pokemon selected by the first rule will be evolved/upgraded first, then the ones of the second rule etc.
More generally, the first rule always have higher priority for evolve, upgrade or buddy.

```json
"rules": [
    {
        "// Of all Pokemon with less than 124 candies, buddy the Pokemon having the highest maximum cp": {},
        "mode": "overall",
        "top": 1,
        "sort": ["max_cp", "cp"],
        "keep": {"candy": -124},
        "evolve": false,
        "buddy": true
    },
    {
        "// Buddy the Pokemon having the less candies. In case no Pokemon match first rule": {},
        "mode": "overall",
        "top": 1,
        "sort": ["-candy", "max_cp", "cp"],
        "evolve": false,
        "buddy": true
    },
    {
        "mode": "by_pokemon",
        "names": ["gym"],
        "top": 3,
        "sort": ["iv", "ncp"],
        "evolve": {"iv": 0.9, "ncp": 0.9},
        "upgrade": {"iv": 0.9, "ncp": 0.9}
    },
    {
        "// Keep best iv of each family and evolve it if its iv is greater than 0.9": {},
        "mode": "by_family",
        "top": 1,
        "sort": ["iv"],
        "evolve": {"iv": 0.9}
    },
    {
        "// Keep best ncp of each family and evolve it if its ncp is greater than 0.9": {},
        "mode": "by_family",
        "top": 1,
        "sort": ["ncp"],
        "evolve": {"ncp": 0.9}
    },
    {
        "// Keep best cp of each family but do not evolve it": {},
        "mode": "by_family",
        "top": 1,
        "sort": ["cp"],
        "evolve": false
    },
    {
        "// For Pokemon of final evolution and with iv greater than 0.9, keep the best dps_attack": {},
        "mode": "by_pokemon",
        "names": ["!with_next_evolution"],
        "top": 1,
        "sort": ["dps_attack", "iv"],
        "keep": {"iv": 0.9}
    }
]
```

The following table describe how the parameters of a rule affect the selection of Pokemon:

|         |               | Balbusaur `{"iv": 0.38}` | Ivysaur `{"iv": 0.98}` | Venusaur `{"iv": 0.71}` | ... | Dratini `{"iv": 0.47}` | Dratini `{"iv": 0.93}` | Dragonair `{"iv": 0.82}` | Dragonair `{"iv": 0.91}` | Dragonite `{"iv": 1.0}` |
|:-------:|:-------------:|:------------------------:|:----------------------:|:-----------------------:|:---:|:----------------------:|:----------------------:|:------------------------:|:------------------------:|:-----------------------:|
|   mode  |  `per_family` |             A            |            A           |            A            |     |            B           |            B           |             B            |             B            |            B            |
|  names  |  `Dragonite`  |                          |                        |                         |     |            x           |            x           |             x            |             x            |            x            |
|   keep  | `{"iv": 0.8}` |                          |                        |                         |     |                        |            x           |             x            |             x            |            x            |
|   sort  |    `["iv"]`   |                          |                        |                         |     |                        |            2           |             4            |             3            |            1            |
|   top   |      `3`      |                          |                        |                         |     |                        |            x           |                          |             x            |            x            |
|  evolve | `{"iv": 0.9}` |                          |                        |                         |     |                        |            x           |                          |             x            |                         |
| upgrade | `{"iv": 1.0}` |                          |                        |                         |     |                        |                        |                          |                          |            x            |


[[back to top](#pokemon-optimizer)]

#### rule mode
| Parameter | Possible values                            | Default       |
|-----------|--------------------------------------------|---------------|
| `mode`    | `"by_pokemon"`, `"by_family"`, `"overall"` | `"by_family"` |

The `mode` define how the Pokemon Optimizer is going to apply the rule.
- `"by_pokemon"` will apply the rule for each individual pokemon (eg. Bulbasaur, Ivysaur, Venusaur, Charmander etc.)
<br>In that mode, each Pokemon will be compared to other Pokemon of the same type.
<br>This is the most conservative mode and the one that will result in the most number of Pokemon kept.

- `"by_family"` will apply the rule for each Pokemon family.
A family is the group of a Pokemon with all its evolutions.
<br>In that mode, each Pokemon will be compared to other Pokemon of the same family.

- `"overall"` will apply the rule to the whole bag.
<br>In that mode, each Pokemon will be compared to all other Pokemon in the bag.
<br>This is the most aggressive mode and will result in the less number of Pokemon kept.

[[back to top](#pokemon-optimizer)]

#### rule names
| Parameter | Possible values | Default                  |
|-----------|-----------------|--------------------------|
| `names`   | `[]`            | `[]` = All Pokemon names |

The `names` allow you to restrict a rule to a selected set of Pokemon.
<br>It is a list of Pokemon names or Pokemon [`groups`](#groups).
<br>You can negate a name by preceding it by a `!` or `-`. In that case, the rule apply to all except the negated names.
<br>You can combine Pokemon names and group names together in the same list.

By default, rules apply to all Pokemon.
- In `by_family` mode, if a Pokemon name is present in the `names` list, it refer to all Pokemon in that Pokemon family.
- In `overall` mode, the `names` list behave as a filter on the whole Pokemon bag.

[[back to top](#pokemon-optimizer)]

#### rule top
| Parameter | Possible values       | Default |
|-----------|-----------------------|---------|
| `top`     | `0`, `]0-1[`, `[1-N]` | `0`     |

This value define how many Pokemon, at the top of your selection, you wish to keep.

- If the value `N` is an integer greater or equal to `1`, it means you wish to keep the N best Pokemon of your selection.
<br>Pokemon will be sorted according to your sorting rule and the `Nth` first will be kept.
<br>In case of equality between Pokemon, it may result in more than `N` Pokemon selected, but never less.
<br>See examples here

- If the value `N` is a decimal between `0` and `1`, it is a ratio relative to the best Pokemon.
<br>Pokemon will be sorted according to your sorting rule and the best will be elected.
<br>All Pokemon whose criteria does not deviate more than `N*100 %` of the best will also be selected.
<br>See examples here

- If the value `N` is `0` or negative, all Pokemon in the selected will be kept.
<br>See examples here

[[back to top](#pokemon-optimizer)]

#### rule sort
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `sort`    | (see below)     | `[]`    |

Define according to which criteria you want to sort your Pokemon.

###### Available criteria

| Criteria             | Description                                                                  |
|----------------------|------------------------------------------------------------------------------|
| `iv`                 | individual value between 0 and 1                                             |
| `ivcp`               | iv weighted so that for equal iv, attack > defense > stamina                 |
| `cp`                 | combat power (can be increased with candies)                                 |
| `cp_exact`           | combat power (not rounded)                                                   |
| `max_cp`             | maximum possible cp                                                          |
| `ncp`                | normalized cp = ratio cp / max_cp                                            |
| `iv_attack`          | attack component of iv between 0 and 15                                      |
| `iv_defense`         | defense component of iv between 0 and 15                                     |
| `iv_stamina`         | stamina component of iv between 0 and 15                                     |
| `dps`                | raw dps based on the moves of the pokemon                                    |
| `dps1`               | raw dps of the fast attack                                                   |
| `dps2`               | raw dps of the charge attack                                                 |
| `dps_attack`         | estimated average dps when attacking                                         |
| `attack_perfection`  | ratio `dps_attack` / `best_dps_attack`. Return same order as `dps_attack`    |
| `dps_defense`        | estimated average dps when defending                                         |
| `defense_perfection` | ratio `dps_defense` / `best_dps_defense`. Return same order as `dps_defense` |
| `hp`                 | current health points                                                        |
| `hp_max`             | max health points                                                            |
| `candy`              | number of candies for this pokemon                                           |
| `candy_to_evolution` | number of candies missing to evolve this Pokemon                             |
| `evolution_cost`     | total number of candies required to evolve this Pokemon to next evolution    |

You can put multiple criteria in the list by separating them by a comma: `"sort": ["iv", "cp"]`
<br>If multiple criteria are present, Pokemon will be ranked according to the first criteria, then, if equals, to the second criteria, etc.

Pokemon are sorted from highest score to lowest score in the selected criteria.
Preceding the criteria name by a `-` will reverse the order:

- `"sort": ["candy"]` will sort Pokemon from highest to lowest number of candies.
- `"sort": ["-candy"]` will sort Pokemon from lowest to highest number of candies.

[[back to top](#pokemon-optimizer)]

#### rule keep
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `keep`    | (see below)     | `true`  |

Define minimum requirements to keep the Pokemon.
Only Pokemon meeting these minimum requirements will be sorted.
By default, if `keep` is not provided or is empty, all Pokemon will be sorted.

The parameter can be a boolean value (`true` or `false`) or a list a criteria.
The available criteria are the same as for the [`sort`](#available-criteria) parameter.

The minimum requirement values can be a single value or a range.
<br>They can also be a negative value if you wish to keep Pokemon below a certain criteria:

- `"keep": false` will not rank any Pokemon. That is like deactivating the rule.
- `"keep": true` will rank all Pokemon.
- `"keep": {"iv": 0.9}` will only rank Pokemon with `iv` greater than `0.9`.
- `"keep": {"iv": 0.9, "cp": 1200}` will only rank Pokemon with `iv` greater than `0.9` and `cp` greater than `1200`.
- `"keep": {"iv": 0.9}` will only rank Pokemon with `iv` greater than `0.9`.
- `"keep": {"cp": -20}` will only rank Pokemon with `cp` lower than `20`.
- `"keep": {"cp": [10, 20]}` will only rank Pokemon with `cp` between `10` and `20`.
- `"keep": {"iv": [[0.3, 0.5], [0.9, 1.0]]}` will only rank Pokemon with `iv` between `0.3` and `0.5` or between `0.9` and `1.0`.

[[back to top](#pokemon-optimizer)]

#### rule evolve
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `evolve`  | (see below)     | `true`  |

Define minimum requirements to evolve the Pokemon.
Only Pokemon meeting these minimum requirements will be evolved.
By default, if `evolve` is not provided or is empty, no Pokemon will be evolved.

The parameter can be a boolean value (`true` or `false`) or a list a criteria.
The available criteria are the same as for the [`sort`](#available-criteria) parameter.

*Note!* If [may_evolve_favorites](#may_evolve_favorites) is `false`, favorite Pokemon will never be evolved!

The minimum requirement values can be a single value or a range.
<br>They can also be a negative value if you wish to evolve Pokemon below a certain criteria:

- `"evolve": false` will not try to evolve any of the Pokemon selected.
- `"evolve": true` will try to evolve all Pokemon selected.
- `"evolve": {"iv": 0.9}` will only evolve Pokemon with `iv` greater than `0.9`.
- `"evolve": {"iv": 0.9, "cp": 1200}` will only evolve Pokemon with `iv` greater than `0.9` and `cp` greater than `1200`.
- `"evolve": {"iv": 0.9}` will only evolve Pokemon with `iv` greater than `0.9`.
- `"evolve": {"cp": -20}` will only evolve Pokemon with `cp` lower than `20`.
- `"evolve": {"cp": [10, 20]}` will only evolve Pokemon with `cp` between `10` and `20`.
- `"evolve": {"iv": [[0.3, 0.5], [0.9, 1.0]]}` will only evolve Pokemon with `iv` between `0.3` and `0.5` or between `0.9` and `1.0`.

[[back to top](#pokemon-optimizer)]

#### rule upgrade
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `upgrade` | (see below)     | `false` |

Define minimum requirements to upgrade the Pokemon.
Only Pokemon meeting these minimum requirements will be upgraded.
By default, if `upgrade` is not provided or is empty, no Pokemon will be upgraded.

The parameter can be a boolean value (`true` or `false`) or a list a criteria.
The available criteria are the same as for the [`sort`](#available-criteria) parameter.

*Note!* If [may_upgrade_favorites](#may_upgrade_favorites) is `false`, favorite Pokemon will never be upgraded!

The minimum requirement values can be a single value or a range.
<br>They can also be a negative value if you wish to upgrade Pokemon below a certain criteria:

- `"upgrade": false` will not try to upgrade any of the Pokemon selected.
- `"upgrade": true` will try to upgrade all Pokemon selected.
- `"upgrade": {"iv": 0.9}` will only upgrade Pokemon with `iv` greater than `0.9`.
- `"upgrade": {"iv": 0.9, "cp": 1200}` will only upgrade Pokemon with `iv` greater than `0.9` and `cp` greater than `1200`.
- `"upgrade": {"iv": 0.9}` will only upgrade Pokemon with `iv` greater than `0.9`.
- `"upgrade": {"cp": -20}` will only upgrade Pokemon with `cp` lower than `20`.
- `"upgrade": {"cp": [10, 20]}` will only upgrade Pokemon with `cp` between `10` and `20`.
- `"upgrade": {"iv": [[0.3, 0.5], [0.9, 1.0]]}` will only upgrade Pokemon with `iv` between `0.3` and `0.5` or between `0.9` and `1.0`.

[[back to top](#pokemon-optimizer)]

#### rule favorite
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `favorite` | (see below)     | `false` |

Define minimum requirements to favorite the Pokemon.
Only Pokemon meeting these minimum requirements will be marked as favorite.
By default, if `favorite` is not provided or is empty, no Pokemon will be marked favorite.

The parameter can be a boolean value (`true` or `false`) or a list a criteria.
The available criteria are the same as for the [`sort`](#available-criteria) parameter.

The minimum requirement values can be a single value or a range.
<br>They can also be a negative value if you wish to mark Pokemon below a certain criteria as favorite:

- `"favorite": false` will not try to mark any of the Pokemon selected as favorite.
- `"favorite": true` will try to mark all Pokemon selected as favorite.
- `"favorite": {"iv": 0.9}` will only favorite Pokemon with `iv` greater than `0.9`.
- `"favorite": {"iv": 0.9, "cp": 1200}` will only favorite Pokemon with `iv` greater than `0.9` and `cp` greater than `1200`.
- `"favorite": {"iv": 0.9}` will only favorite Pokemon with `iv` greater than `0.9`.
- `"favorite": {"cp": -20}` will only favorite Pokemon with `cp` lower than `20`.
- `"favorite": {"cp": [10, 20]}` will only favorite Pokemon with `cp` between `10` and `20`.
- `"favorite": {"iv": [[0.3, 0.5], [0.9, 1.0]]}` will only favorite Pokemon with `iv` between `0.3` and `0.5` or between `0.9` and `1.0`.

[[back to top](#pokemon-optimizer)]

#### rule buddy
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `buddy`   | (see below)     | `false` |

Define minimum requirements to make a Pokemon your buddy.
Only Pokemon meeting these minimum requirements will be candidate for being a buddy.
By default, if `buddy` is not provided or is empty, no Pokemon will be set as buddy.

The buddy selected if the best Pokemon meeting the requirements.
He will become the new buddy if there is currently no buddy or if the current buddy walked its complete distance.
If multiple rules are used to select a buddy, the order of the rules define which Pokemon will be the new buddy.

The minimum requirement values can be a single value or a range.
<br>They can also be a negative value if you wish to buddy Pokemon below a certain criteria:

- `"buddy": false` will not select any Pokemon as buddy candidate.
- `"buddy": true` will select all Pokemon as buddy candidate.
- `"buddy": {"candy": -400}` will only select Pokemon for which the number of `candy` is less than or equal to `400`.
- `"buddy": {"candy_to_evolution": -5}` will only select Pokemon for which the number of candy missing to evolve it is less than or equal to `5`.
- `"buddy": {"evolution_cost": 50}` will only select Pokemon for which the number of needed for next evolution is a least `50`.

`Buddy Hitmonlee rewards Hitmonlee candies [+1 candies] [6 candies]`

[[back to top](#pokemon-optimizer)]

# Eevee case

For Eevee Pokemon family, and any other family with multiple paths of evolution, the Pokemon Optimizer behaves as if the chances of getting a specific evolution were random and equal.
<br>In practice, here are the effects you might notice regarding Eevee family:
- If you are missing one version of evolution, every Eevee is a possible candidate to become the best Eevee you have for that specific evolution.
<br>So as long as an evolution version is missing, the Pokemon Optimizer will tentatively try to keep and evolve all Eevees.

- Once you have all version of evolution, things are not yet simple. Every Pokemon better than the worst evolution you have is a candidate to replace it.
<br>The Pokemon Optimizer will tentatively try to keep and evolve all Eevees that may replace the worst evolution you have.

- If you deactivate the global `evolve` parameter, the Pokemon Optimizer will not apply above rules since it considers you are manually controlling the evolution of your Eevees.

[[back to top](#pokemon-optimizer)]

# FAQ
#### How do I keep the 2 best `iv` of every single Pokemon, and evolve them if they are over `0.9` `iv` ?

```json
{
    "mode": "by_pokemon",
    "top": 2,
    "sort": ["iv"],
    "evolve": {"iv": 0.9}
},
```

#### How do I keep the 2 best `iv` of every single Pokemon, and evolve them if they are over `0.9` `ncp` ?

```json
{
    "mode": "by_pokemon",
    "top": 2,
    "sort": ["iv"],
    "evolve": {"ncp": 0.9}
},
```

#### How do I keep my 10 best `cp` Dragonite and Snorlax to fight gyms ?

```json
{
    "mode": "by_pokemon",
    "names": ["Dragonite", "Snorlax"],
    "top": 10,
    "sort": ["cp"]
},
```

#### How do I keep the Gyarados with the best moveset for attack ?

```json
{
    "mode": "by_pokemon",
    "names": ["Gyarados"],
    "top": 1,
    "sort": ["dps_attack"]
},
```

#### How do I keep the Gyarados with the best fast attack ?

```json
{
    "mode": "by_pokemon",
    "names": ["Gyarados"],
    "top": 1,
    "sort": ["dps1"]
},
```

#### How do I keep all my Poliwag with `cp` less that `20` ?

```json
{
    "mode": "by_pokemon",
    "names": ["Poliwag"],
    "keep": {"cp": -20}
},
```

#### How do I buddy the Pokemon for which I have the less number of candies ?

```json
{
    "mode": "overall",
    "top": 1,
    "sort": ["-candy", "cp"],
    "buddy": true
},
```

[[back to top](#pokemon-optimizer)]
