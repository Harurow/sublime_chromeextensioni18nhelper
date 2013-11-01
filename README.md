# ChromeExtensionI18nHelper for Sublime Text plug-in

Sublime Text 2/3 plug-in.

This plug-in support your `manifest.json`, `message.json` file.
using chorome.i18n application.

ex)

manifest.json to message.json

*before:*
```json
# manifest.json
  {
    "name": "HogeHoge Application"
  }
```
*after:*
```json
# manifest.json
  {
    "name": "__MSG_appName__"
  }
# _locales/en/messages.json
  {
    "appName": {
      "message": "HogeHoge Application"
    }
  }


Translation localized message.json from default locale.

# _locales/ja/messages.json
  {
    "appName": {
      "message": "HogeHogeアプリケーション"
      "description": "manifest.json - name(en->ja)"
    }
  }
```


## How to Install ##

With [Package Control](https://sublime.wbond.net/installation):

1. Run “Package Control: Install Package” command, find and install `ChromeExtensionI18nHelper` plugin.

Manually:

1. Clone or [download](https://github.com/Harurow/sublime_chromeextensioni18nhelper/archive/master.zip) git repo into your packages folder (in ST, find Browse Packages... menu item to open this folder)

## Setting ##

first, set your default location.

1. Run “[Preferences] - [Package Settings] - [ChromeExtensionI18nHelper] - [Settings -User]”

2. input your default location
{
	"default_location": "**YOUR DEFAULT LOCATION**"
}

Valid location is the following.
"am ar bg bn ca cs da de el en en_GB en_US es es_419 et fi fil fr gu he hi hr hu
 id it ja kn ko lt lv ml mr nb nl or pl pt pt_BR pt_PT ro ru sk sl sr sv sw ta te
 th tr uk vi zh zh_CN zh_TW"


## License
The MIT License (MIT)

Copyright (c) 2013 Motoharu Tsubaki.

Permission is hereby granted, free of charge, to any person obtaining a 
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
