Individual Values, or IVs function like a Pokémon's "Genes". They are the traits which are passed down from one generation to the next.

![](http://vignette3.wikia.nocookie.net/pokemon/images/d/dd/ImagesCAD6WL01.jpg/revision/latest?cb=20110511020243)

**Individual values**

Every stat has an IV ranging from 0 to 31 for each stat (HP, ATK, DEF, SPA, SPD, and SPE), and at level 100, their IVs are added to the Pokémon's stats for their total values. For example, a level 100 Tyranitar with no Effort Values and 0 IVs has 310 HP, however if it had 31 IVs, it would have 341 HP.


These stats are provided randomly for every Pokémon, caught or bred, and although as insignificant as 31 points may seem, they are required for Ace Trainers to obtain when breeding Pokémon with perfect natures/stats. On some occasions they are even the tipping point in a close matchup. For example, if there was a Terrakion with 0 Attack IV, it will have an attack of 358 at level 100 (with an attack improving nature), while a Terrakion with perfect Attack IVs would have 392 Attack. This small difference can mean the difference between a one-hit kill (not an OHKO) and survival with 1 HP.


**Breeding IVs**
Fortunately for trainers, Ace Trainers and Pokémon Breeders especially, IVs can be bred to obtain the perfect Pokémon.

The process of breeding IVs is as follows, the example displayed below is to breed Nidorans:

* The child's IV's are generated randomly, for example: 7/27/31/14/19/2, in HP/ATK/DEF/SPA/SPD/SPE format.
* Three stats are inherited from the parents, and are selected in three checks:
1. First check: A random stat (HP/ATK/DEF/SPA/SPD/SPE) is selected from either the Mother or the Father and passed on to the child.
2. Second check: A random stat with the exception of HP (ATK/DEF/SPA/SPD/SPE) is selected from either the Mother or the Father and passed on to the child.
3. Third check: A random stat with the exception of HP and DEF (ATK/SPA/SPD/SPE) is selected from either the Mother or the Father and passed on to the child.
This means that HP and DEF are less likely to pass on to the child, however there are ways to make sure the IVs are passed on.

Letting either one of the parents hold a Power Item can ensure that the Power Item's respective stat will be passed on to the offspring from the parent that holds it.

If the Power Item called Power Weight (doubles all HP EV gained) is held by a parent with a perfect IV of 31 for HP and the first check selects this parent, the child is ensured to have a perfect IV for HP. The other checks, though, will be random, and either luck or patience is required to eventually get the desired stats.

Important: Only three stats are inherited per Pokémon, and these can stack. For example, the DEF IV can be inherited from both parents, thus rendering one redundant.



**Checking IVs**
Beginning in Generation III, there has always been an NPC that allows players to check the IVs of their Pokémon.


If you wanted to check the IV's yourself the formula is as follows:

The formula for HP is different from the rest of the stats, so here is the formula for HP:

> IV=((Stat - Level Value - 10) * 100 / Level Value) - 2 * Base stat - (Math.Floor(EV/4))

In layman terms:

> Individual Value= ((Current Stat Level - Current Level Value - 10) * 100 / Current Level Value) - 2 * Base Stat - (Math.Floor(EV/4))

Just in case you don't know (Math.Floor(EV/4)) means to take the amount of EVs you have in HP and divide it by 4 and then round down.
The formula you use for the rest of the stats is the same, so here it is:

> IV=((Math.Ceiling(Stat/Nature) - 5) * 100 / Level Value) - 2 * Base Stat - (Math.Floor(EV/4))

In layman terms:

> Individual Value= (Math.Ceiling(Current Stat Value/Nature Bonus) * 100 / Current Level Value) - 2 * Base Stat - (Math.Floor(EV/4))

Just in case you don't know (Math.Floor(EV/4)) means to take the amount of EVs you have in HP and divide it by 4 and then round down.

Just in case you don't know (Math.Ceiling(Current Stat Value/Nature Bonus)) means to take the Current Stat Value and divide it by the bonus you get from the Pokémon's nature and then round up. If the stat gets an increase from the nature you divide the Current Stat Value by 1.1, and if it is a decrease from the nature you divide the Current Stat Value by 0.9.
