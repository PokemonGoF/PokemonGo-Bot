TelegramTask configuration and subscriptions for updates


**Authentication**

There are two ways to be authenticated with the Telegram task of the bot:
* authentication for one predefined userid or username (config parameter: `master`, can be given as a number (userid) or as a string(username); for username, please note that it is case-sensitive); this will automatically authenticate all requests coming from the particular userid/username (note: when providing username, you will need to send a message to the bot in order for the bot to learn your user id). Hardcoded notifications will only be sent to this username/userid.
* authentication by a password (config parameter: `password`): this will wait for a `/login <password>` command to be sent to the bot and will from then on treat the corresponding userid as authenticated until a `/logout` command is sent from that user id.

**Hardcoded notifications - please consider this feature deprecated, it will be removed in the future**

Certain notifications (egg_hatched, bot_sleep, spin_limit, catch_limit, level_up) will always be sent to the "master" and cannot be further configured. 
The notification for pokemon_caught can be configured by using the "alert_catch" configuration parameter. This parameter can be:
* either a plain list (in this case, a notification will be sent for every pokemon on the list caught, with "all" matching all pokemons)
* or a "key: value" dict of the following form 

> "pokemon_name": {"operator": "and/or", "cp": cpmin, "iv": ivmin }

Again, "all" will apply to all pokemons. If a matching pokemon is caught, depending on "operator" being "and" or "or", a notification will be sent if both or one of the criteria is met.
Example:
> "Dratini": { "operator": "and", "cp": 1200, "iv": 0.99 }

This will send a notification if a Dratini is caught with at least 1200CP and at least 0.99 potential.

**Dynamic notifications(subscriptions)**

Every authenticated user can subscribe to be notified in case a certain event is emitted. The list of currently available events can be retrieved by sending `/events` command:
> /events

List all available eventy (MANY!)

> /events egg

List all events matching regular expression .\*egg.\*

In order to subscribe to a certain event, e.g. to "no_pokeballs", you simply send the `/sub` command as follows:
> /sub no_pokeballs

In order to remove this subscription:
> /unsub no_pokeballs

*Note: the `/unsub` command must match exactly the corresponding `/sub` command*
A special case is `/sub all` - it will subscribe you to all events. Be prepared for huge amount of events! `/unsub all` will remove this subscription, without changing other subscriptions.
Another special case is `/unsub everything` - this will remove all your subscriptions.
Currently, only pokemon_caught event can be configured with more detail, here is an example:
> /sub pokemon_caught operator:and cp:1200 pokemon:Dratini iv:0.99

This will subscribe you to be notified every time a Dratini has been caught with cp equal or higher than 1200 and iv equal or higher than 0.99 (same as in "Hardcoded notifications" above)

`/showsubs` will show your current subscriptions.


**Listing pokemon**

> /top 10 iv

List top 10 pokemon, ordered by IV, descending order

> /top 15 cp

List top 15 pokemon, ordered by CP, descending order

> /top 5 dated

List top 5 pokemon, ordered by catching date, descending order

Same logic for :
/evolved <num> <cp-or-iv-or-dated>
/hatched <num> <cp-or-iv-or-dated>
/caught <num> <cp-or-iv-or-dated>
/released <num> <cp-or-iv-or-dated>
/vanished <num> <cp-or-iv-or-dated>
