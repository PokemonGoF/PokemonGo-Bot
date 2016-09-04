# Pokemon Optimizer
- [About](#about)
- [Configuration](#configuration)
    - [Default configuration](#default-configuration)
    - [Understand parameters](#understand-parameters)
        - [enabled](#enabled)
        - [min_slots_left](#min_slots_left)
        - [transfer](#transfer)
        - [transfer_wait_min](#transfer_wait_min)
        - [transfer_wait_max](#transfer_wait_max)
        - [evolve](#evolve)
        - [evolve_time](#evolve_time)
        - [evolve_for_xp](#evolve_for_xp)
        - [evolve_only_with_lucky_egg](#evolve_only_with_lucky_egg)
        - [evolve_count_for_lucky_egg](#evolve_count_for_lucky_egg)
        - [may_use_lucky_egg](#may_use_lucky_egg)
        - [upgrade](#upgrade)
        - [upgrade_level](#upgrade_level)
        - [groups](#groups)
        - [keep](#keep)
            - [mode](#keep-mode)
            - [names](#keep-names)
            - [top](#keep-top)
            - [sort](#keep-sort)
            - [evolve](#keep-evolve)
    - [Examples of configuration](#examples-of-configuration)
- [Eevee case](#eevee-case)

# About
The Pokemon Optimizer manage transfer, evolution and upgrade of your Pokemon.
<br>It can replace or complement the classical Evolve and Transfer tasks.
<br>It will be triggered when you bag of Pokemon is full and has no effect until it happens.

The Pokemon Optimizer will first Transfer, then Evolve, then Upgrade.
There is only one pass at each action.

[[back to top](#pokemon-optimizer)]

# Configuration
## Default configuration
```
{
    "tasks": [
        {
            "type": "PokemonOptimizer",
            "config": {
                "enabled": true,
                "min_slots_left": 5,
                "transfer": true,
                "transfer_wait_min": 3,
                "transfer_wait_max": 5,
                "evolve": true,
                "evolve_time": 25,
                "evolve_for_xp": true,
                "evolve_only_with_lucky_egg": false,
                "evolve_count_for_lucky_egg": 80,
                "may_use_lucky_egg": true,
                "upgrade": true,
                "upgrade_level": 60,
                "groups": {
                    "gym": ["Dragonite", "Snorlax", "Lapras", "Arcanine"]
                },
                "keep": [
                    {
                        "mode": "by_family",
                        "top": 1,
                        "sort": [{"iv": 0.9}],
                        "evolve": true,
                        "upgrade": false
                    },
                    {
                        "mode": "by_family",
                        "top": 1,
                        "sort": [{"ncp": 0.9}],
                        "evolve": true,
                        "upgrade": false
                    },
                    {
                        "mode": "by_family",
                        "top": 1,
                        "sort": ["cp"],
                        "evolve": false,
                        "upgrade": false
                    },
                    {
                        "mode": "by_family",
                        "names": ["gym"],
                        "top": 3,
                        "sort": [{"iv": 0.9}, {"ncp": 0.9}],
                        "evolve": true,
                        "upgrade": true
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

### min_slots_left
| Parameter        | Possible values | Default |
|------------------|-----------------|---------|
| `min_slots_left` | `[0-N]`         | `5`     |

The Pokemon Optimizer will be triggered when you have that number (or less) empty slots in your Pokemon Bag.

[[back to top](#pokemon-optimizer)]

### transfer
| Parameter  | Possible values | Default |
|------------|-----------------|---------|
| `transfer` | `true`, `false` | `false` |

The `transfer` parameter activate or deactivate the transfer of Pokemon.

At `true`, you allow the Pokemon Optimizer to transfer every Pokemon that are not good enough to be kept according to your own criteria.
<br>At `false`, and regardless of other parameters, no Pokemon is ever going to be transfered.

Note that, whatever is the value you choose to give to that parameter, you will still see logs explaining which Pokemon are transfered.
<br>The purpose of this is to show you what choices are made by the Pokemon Optimizer.
It can help you rectify your configuration or guide you during manual transfer.

`Exchanged Magikarp [IV 0.4] [CP 69] [481 candies]`

[[back to top](#pokemon-optimizer)]

### transfer_wait_min
| Parameter           | Possible values | Default |
|---------------------|-----------------|---------|
| `transfer_wait_min` | `[0-N]`         | `3`     |

This is the minimum time to wait after transferring a Pokemon.

[[back to top](#pokemon-optimizer)]

### transfer_wait_max
| Parameter           | Possible values | Default |
|---------------------|-----------------|---------|
| `transfer_wait_max` | `[0-N]`         | `5`     |

This is the maximum time to wait after transferring a Pokemon.

[[back to top](#pokemon-optimizer)]

### evolve
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `evolve`  | `true`, `false` | `false` |

The `evolve` parameter activate or deactivate the evolution of Pokemon.

At `true`, you allow the Pokemon Optimizer to evolve every Pokemon that are the best according to your own criteria.
<br>You also allow it to evolve lower quality Pokemon when [`evolve_for_xp`](#evolve_for_xp) parameter is `true`.
<br>At `false`, and regardless of other parameters, no Pokemon is ever going to be evolved.
<br>`evolve` parameter can be deactivated separately for each rule (see [`evolve`](#keep-evolve)).

Note that, whatever is the value you choose to give to that parameter, you will still see logs explaining which Pokemon are evolved.
<br>The purpose of this is to show you what choices are made by the Pokemon Optimizer.
It can help you rectify your configuration or guide you during manual evolution.

`Evolved Magikarp [IV 0.96] [CP 231] [+1000 xp] [82 candies]`

[[back to top](#pokemon-optimizer)]

### evolve_time
| Parameter     | Possible values | Default |
|---------------|-----------------|---------|
| `evolve_time` | `[0-N]`         | `25`    |

This is the duration of the evolution animation and time to wait after performing an evolution.
<br>The actual time used is randomized between more or less 10% of the parameter value.

[[back to top](#pokemon-optimizer)]

### evolve_for_xp
| Parameter       | Possible values | Default |
|-----------------|-----------------|---------|
| `evolve_for_xp` | `true`, `false` | `true`  |

Let you choose if you want the Pokemon Otimizer to use your candies to evolve low quality Pokemon.

Better quality Pokemon have priority for evolution and the Pokemon Optimizer will never evolve for xp if a better Pokemon is waiting for candies to evolve.
<br>These low quality Pokemon will only be used if you have plenty of candies left after evolving your best Pokemon.

The below 2% rule help the Pokemon Optimizer to disregard rare Pokemon and focus on common Pokemon to evolve for xp.

###### 2% rule
For each family of Pokemon, if, after evolving your best Pokemon, you have enough candies left to evolve 2% of your total bag capacity, the first rank of the family are eligible for xp evolution.
<br>If you do not have enough candies or Pokemon to evolve these 2%, they will be transfered.

For example, for a bag total capacity of 250, you must have enough candies and Pokemon to evolve 5 of them for xp evolution.
<br>This usually means that the rarest Pokemon in your area will never be eligible since you never have 5 low quality of them at the point where your bag is full.

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

If you allow the Pokemon Optimizer to use a lucky egg, this parameter let you define the minimum number of Pokemons that must evolve when using a lucky egg.

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

### upgrade
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `upgrade` | `true`, `false` | `false` |

The `upgrade` parameter activate or deactivate the upgrade (power-up) of Pokemon.

At `true`, you allow the Pokemon Optimizer to upgrade every Pokemon that are the best according to your own criteria.
<br>If `evolve` is also activated, evolution has priority over upgrade.
Which means that the Pokemon Optimizer is going to wait that a Pokemon is fully evolved before upgrading it.
<br>At `false`, and regardless of other parameters, no Pokemon is ever going to be upgraded.
<br>`upgrade` parameter can be deactivated separately for each rule (see [`upgrade`](#keep-upgrade)).

Note that, whatever is the value you choose to give to that parameter, you will still see logs explaining which Pokemon are upgraded.
<br>The purpose of this is to show you what choices are made by the Pokemon Optimizer.
It can help you rectify your configuration or guide you during manual power-up.

`Upgraded Magikarp [IV 0.96] [CP 231] [81 candies] [132450 stardust]`

[[back to top](#pokemon-optimizer)]

### upgrade_level
| Parameter       | Possible values | Default |
|-----------------|-----------------|---------|
| `upgrade_level` | `[1-80]`        | `60`    |

This the maximum level at which you want the Pokemon Optimizer to upgrade your Pokemon.
<br>Pokemon upgrade level cannot be higher than 2 times player level. The parameter value will be majored by `2 * player level`.

Pokemon are either fully upgraded to the maximum possible level or not upgraded at all.
The higher the level is, the more costly in candies and stardust it becomes to upgrade a Pokemon.

###### Cumulative upgrade cost (candy, stardust)

| From - To | 10        | 20          | 30          | 40          | 50          | 60            | 70            | 80            |
|-----------|:---------:|:-----------:|:-----------:|:-----------:|:-----------:|:-------------:|:-------------:|:-------------:|
| 1         | 9<br>3000 | 19<br>11000 | 38<br>25500 | 58<br>47500 | 87<br>80000 | 126<br>125000 | 196<br>190000 | 319<br>280000 |
| 10        |           | 10<br>8000  | 29<br>22500 | 49<br>44500 | 78<br>77000 | 117<br>122000 | 187<br>187000 | 310<br>277000 |
| 20        |           |             | 19<br>14500 | 39<br>36500 | 68<br>69000 | 107<br>114000 | 177<br>179000 | 300<br>269000 |
| 30        |           |             |             | 20<br>22000 | 49<br>54500 |  88<br>99500  | 158<br>164500 | 281<br>254500 |
| 40        |           |             |             |             | 29<br>32500 |  68<br>77500  | 138<br>142500 | 261<br>232500 |
| 50        |           |             |             |             |             |  39<br>45000  | 109<br>110000 | 232<br>200000 |
| 60        |           |             |             |             |             |               |  70<br>65000  | 193<br>155000 |
| 70        |           |             |             |             |             |               |               | 123<br>90000  |

[[back to top](#pokemon-optimizer)]

### groups
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `groups`  | (see below)     | `{}`    |

You can define `groups` of Pokemon to help you restrict rules to a specific set of Pokemon.
<br>You can then use these `groups` names in the [`names`](#keep-names) parameter of your rule to refer to list of Pokemon

`groups` are list of Pokemon names:
```
"groups": {
    "gym": ["Dragonite", "Snorlax"],
    "my_love": ["Pikachu"],
    "vip": ["Lapras", "Arcanine", "Gyarados", "gym"],
    "trash": ["!vip", "!my_love"]
},
```

A same Pokemon name can appear in different `groups`. And `groups` may reference each others.
<br>Just like [`names`](#keep-names), you can also negate a group by preceding its name by a `!` or `-`.
<br>Including `groups` and negating others allow you to create group unions and/or intersections.

[[back to top](#pokemon-optimizer)]

### keep
| Parameter | Possible values | Default     |
|-----------|-----------------|-------------|
| `keep`    | (see below)     | (see below) |

This parameter is a list that contains as many element as you want.
<br>Each element of that list define a rule that select what Pokemon are the best.
<br>Each of these rules is going to be handled individually and will result in a list of Pokemon to keep.

The conjunction of all rules define the list of all Pokemon to keep.
Every Pokemon not selected is candidate for transfer.

```
[
    {"mode": "by_family", "top": 1, "sort": [{"iv": 0.9}], "evolve": True, "upgrade": False},
    {"mode": "by_family", "top": 1, "sort": [{"ncp": 0.9}], "evolve": True, "upgrade": False},
    {"mode": "by_family", "top": 1, "sort": ["cp"], "evolve": False, "upgrade": False},
    {"mode": "by_family", "top": 3, "names": ["gym"], "sort": [{"iv": 0.9}, {"ncp": 0.9}], "evolve": True, "upgrade": True}
]
```

[[back to top](#pokemon-optimizer)]

#### keep mode
| Parameter | Possible values                            | Default       |
|-----------|--------------------------------------------|---------------|
| `mode`    | `"by_pokemon"`, `"by_family"`, `"overall"` | `"by_family"` |

The `mode` define how the Pokemon Optimizer is going to apply the rule.
- `"by_pokemon"` will apply the rule for each Pokemon.
<br>In that mode, each Pokemon will be compared to other Pokemon of the same name.
<br>This is the most conservative mode and the one that will result in the most number of Pokemon kept.

- `"by_family"` will apply the rule for each Pokemon family.
<br>In that mode, each Pokemon will be compared to other Pokemon of the same family.

- `"overall"` will apply the rule to the whole bag.
<br>In that mode, each Pokemon will be compared to all other Pokemon in the bag.
<br>This is the most aggressive mode and will result in the less number of Pokemon kept.

[[back to top](#pokemon-optimizer)]

#### keep names
| Parameter | Possible values | Default                  |
|-----------|-----------------|--------------------------|
| `names`   | list of strings | `[]` = All Pokemon names |

The `names` allow you to restrict a rule to a selected set of Pokemon.
<br>It is a list of Pokemon names or Pokemon [`groups`](#groups).
<br>You can negate a name by preceding it by a `!` or `-`. In that case, the rule apply to all except the negated names.
<br>You can combine Pokemon names and group names together in the same list.

By default, rules apply to all Pokemons.
- In `by_family` mode, if a Pokemon name is present in the `names` list, it refer to all Pokemon in that Pokemon family.
- In `overall` mode, the `names` list behave as a filter on the whole Pokemon bag.

[[back to top](#pokemon-optimizer)]

#### keep top
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

#### keep sort
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `sort`    | (see below)     | `[]`    |

Define according to which criteria you want to sort your Pokemon.
<br>Available criteria are:

| Criteria             | Description                                                                  |
|----------------------|------------------------------------------------------------------------------|
| `iv`                 | individual value between 0 and 1                                             |
| `ivcp`               | iv weighted so that for equal iv, attack > defense > stamina                 |
| `cp`                 | combat power (can be increased with candies)                                 |
| `cp_exact`           | combat power (not rounded)                                                   |
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

You can put multiple criteria in the list by separating them by a comma: `"sort": ["iv", "cp"]`
<br>If multiple criteria are present, Pokemon will be ranked according to the first, then if equals the second, etc...

In addition to define sorting criteria, the `sort` list may contain minimum requirements for evolution and upgrade:
- `"top": 1, "sort": ["iv"], "evolve": True` will rank Pokemon by `iv`.
<br>It will keep and evolve the best of them.
- `"top": 1, "sort": [{"iv": 0.9}], "evolve": True` will rank Pokemon by `iv`.
<br>It will keep the best of them and evolve it only if its `iv` is greater than `0.9`.
- `"top": 3, "sort": [{"iv": 0.9}, {"cp": 1200}], "evolve": True` will rank Pokemon by `iv` and then `cp`.
<br>It will keep the top 3 of them and evolve them only if their `iv` is greater than `0.9` and their `cp` greater than `1200`.

[[back to top](#pokemon-optimizer)]

#### keep evolve
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `evolve`  | `true`, `false` | `true`  |

The parameter allow you to selectively control what Pokemon to evolve.

At `true`, all Pokemon selected and meeting the minimum evolution criteria (see [`sort`](#keep-sort)) will be evolved.
<br>At `false`, Pokemon selected will not be eligible for evolution, unless they are also selected by another rule that allow them to evolve.

[[back to top](#pokemon-optimizer)]

#### keep upgrade
| Parameter | Possible values | Default |
|-----------|-----------------|---------|
| `upgrade` | `true`, `false` | `false` |

The parameter allow you to selectively control what Pokemon to upgrade.

At `true`, all Pokemon selected and meeting the minimum upgrade criteria (see [`sort`](#keep-sort)) will be upgraded.
<br>At `false`, Pokemon selected will not be eligible for upgrade, unless they are also selected by another rule that allow them to upgrade.

[[back to top](#pokemon-optimizer)]

## Examples of configuration
> Keep the 2 best `iv` of every single Pokemon, and evolve them if they are over 0.9 `iv`. 

```
{
    "mode": "by_pokemon",
    "top": 2,
    "sort": [{"iv": 0.9}],
    "evolve": true
},
```

> Keep my 10 best `cp` Dragonite and Snorlax to fight gyms. 

```
{
    "mode": "by_pokemon",
    "names": ["Dragonite", "Snorlax"]
    "top": 10,
    "sort": ["cp"],
    "evolve": false
},
```

> Keep my Gyarados with the best moveset for attack.

```
{
    "mode": "by_pokemon",
    "names": ["Gyarados"]
    "top": 1,
    "sort": ["dps_attack"],
    "evolve": false
},
```

> I don't want you to use my candies for my loved Pokemon, But for others, it is ok.

```
"groups": {
    "my loves ones" : ["Dragonite", "Snorlax", "Caterpie"]
},
"keep": [
    {
        "mode": "by_family",
        "names": ["my loves ones"]
        "top": 1,
        "sort": ["iv"],
        "evolve": false
    },
    {
        "mode": "by_family",
        "names": ["!my loves ones"]
        "top": 1,
        "sort": ["iv"],
        "evolve": true
    }
    // + Exclude `my loves ones` from any other rule
]
```

> Do not touch my Dragonites !

```
{
    "mode": "by_pokemon",
    "names": ["Dragonite"]
},
// + Exclude Dragonite from any other rule
```

[[back to top](#pokemon-optimizer)]

# Eevee case

For Eevee Pokemon family, and any other family with multiple paths of evolution, the Pokemon Optimizer behaves as if the chances of getting a specific evolution were random and equal.
<br>In practice, here are the effects you might notice regarding Eevee family:
- If you are missing one version of evolution, every Eevee is a possible candidate to the become the best Eevee you have for that specific evolution.
<br>So as long as an evolution version is missing, the Pokemon Optimizer will tentatively try to keep and evolve all Eevees.

- Once you have all version of evolution, things are not yet simple. Every every better than the worst evolution you have is a candidate to replace it.
<br>The Pokemon Optimizer will tentatively try to keep and evolve all Eevees that may replace the worst evolution you have.

- If you deactivate the global `evolve` parameter, the Pokemon Optimizer will not apply above rules since it considers you are manually controlling the evolution of your Eevees.

[[back to top](#pokemon-optimizer)]
