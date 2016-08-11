> $ git clone --recursive -b dev https://github.com/PokemonGoF/PokemonGo-Bot
> $ cd PokemonGo-Bot
> // create virtualenv using Python 2.7 executable
> $ virtualenv -p C:\python27\python.exe venv
> $ source venv/Scripts/activate
> $ pip install -r requirements.txt

Once you are you to date with [dev-branch] (https://github.com/PokemonGoF/PokemonGo-Bot/tree/dev) create a pull request and it will be re-viewed


### How to add/discover new API
The example is [here](https://github.com/PokemonGoF/PokemonGo-Bot/commit/46e2352ce9f349cc127a408959679282f9999585)
1. Check the type of your API request in   [POGOProtos](https://github.com/AeonLucid/POGOProtos/blob/eeccbb121b126aa51fc4eebae8d2f23d013e1cb8/src/POGOProtos/Networking/Requests/RequestType.proto) For example: RECYCLE_INVENTORY_ITEM
2. Convert to the api call in pokemongo_bot/__init__.py,  RECYCLE_INVENTORY_ITEM change to self.api.recycle_inventory_item
```
def drop_item(self,item_id,count):
    self.api.recycle_inventory_item(...............)
```
3. Where is the param list?
You need check this [Requests/Messages/RecycleInventoryItemMessage.proto](https://github.com/AeonLucid/POGOProtos/blob/eeccbb121b126aa51fc4eebae8d2f23d013e1cb8/src/POGOProtos/Networking/Requests/Messages/RecycleInventoryItemMessage.proto)
4. Then our final api call is
```
def drop_item(self,item_id,count):
    self.api.recycle_inventory_item(item_id=item_id,count=count)
    inventory_req = self.api.call()
    print(inventory_req)
```
5. You can now debug on the log to see if get what you need
