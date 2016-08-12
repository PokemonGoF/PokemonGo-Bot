# PokemonGo-Bot Plugins
Plugins are collections of tasks distributed outside of the main repo. Using plugins lets you use community built tasks that haven't been accepted into the core bot. Some tasks are better suited to not live in the main bot. An example might be a task that reports seen pokemon to a central server.

## Using Plugins
Plugins are used by adding some new information to your `config.json`.

In your `config.json`, you can add a new array:

```
  ...
  "plugins": [
  ],
  ...
```

In this array, you can put a Github URL that contains the revision you want to use. For example:

```
  ...
  "plugins": [
    "TheSavior/test-pgo-plugin#2d54eddde33061be9b329efae0cfb9bd58842655"
  ],
  ...
```

Once that is there, you can add to your `tasks` array the task you want to use from the plugin. Plugins can expose many tasks, check the plugin's documentation for what tasks can be used.

```
  ...
  "tasks": [
    {
      "type": "test-pgo-plugin.PrintText"
    }
  ]
  ..
```

Then start the bot. It will download the specified plugins and use them when requested in your `tasks` list.

## Developing Plugins
The plugins array can be given a full path to a folder containing a plugin as well as the github url format. When developing a plugin, use a directory outside the root of the bot and add it to your plugins array. Unlike the github url format, it won't be copied to the bot when it is started up, it will be loaded directly from the specified directory.

Plugins have access to any of the things that the tasks in the official repo have access to.

### Example
I recommend looking at this plugin for an example of how to write a plugin: https://github.com/TheSavior/test-pgo-plugin

### API Versioning
We may at some point need to make a backwards incompatible change to the plugin BaseTask. We will avoid this as much as possible, but in the event that occurs, this is how incompatibilities are detected:

The `BaseTask` class specifies:

```
class BaseTask(object):
  TASK_API_VERSION = 1
```

When we need to make a backwards incompatible change, we will increment that number. Plugins have the following:

```
class PrintText(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1
```

If a user tries to use a plugin that has a `SUPPORTED_TASK_API_VERSION` that does not match the current bot's `TASK_API_VERSION`, an exception will be raised.

