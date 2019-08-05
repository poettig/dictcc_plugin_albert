# Dict.cc Translator for albert
Dict.cc translator plugin for the [Albert keyboard launcher](https://albertlauncher.github.io/).
It is based on the Google Translate Python plugin and uses a modified version of [dict.cc.py](https://github.com/rbaron/dict.cc.py).
Dict.cc is a cross-language dictionary that can translate English and German in many other languages. The main difference between this plugin and the Google Translate plugin is its ability to display multiple results at once.

## Dependencies
* [requests](https://pypi.org/project/requests/)
* [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

## How To Install
Just clone this project into `~/.local/share/albert/org.albert.extension.python/modules/` and activate it under Extensions->Python in the Albert settings.

## Issues
If you find an issue with the plugin, please submit an issue in the issue tracker including the query you made and all other information about what you did that you think might useful to me.

## Attributions
Thanks to Manuel Schneider for developing Albert and his great work. It was exactly what I missed from the Cinnamon menu search!

I'd also like to thank Raphael/[rbaron](https://github.com/rbaron) for parsing dict.cc's results into python objects and putting that code under public domain.
I would not have attempted this project without this foundation.
