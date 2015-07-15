# tgbotplug
tgbotplug is meant to be an easy-to-extend telegram bot built around [twx.botapi](https://github.com/datamachine/twx.botapi).

Plugin examples can be found in [tgbotplug-plugins](https://github.com/fopina/tgbotplug-plugins).

Using tgbotplug, after choosing/developing your plugins, is as simple as:

```python
import tgbot
tgbot.TGBot(
  'YOUR_BOT_TOKEN',
  plugins=[
    Plugin1(),
    ...,
    PluginN(),
  ],
).run()
```

Plugins should inherit `tgbot.TGPluginBase`and implement `list_commands()` (and the methods mapped in its result).
