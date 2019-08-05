# -*- coding: utf-8 -*-

"""
Translate text using dict.cc via dict.cc.py.

Usage: cc <src lang> <dest lang> <text>
       cc [>] <text> for en->de
       cc < <text> for de->en
Example: cc en fr hello
"""

import os
import configparser
import urllib.parse
from dictcc import Dict

from albertv0 import *

__iid__ = "PythonInterface/v0.1"
__prettyname__ = "Dict.cc Translator"
__version__ = "1.0"
__trigger__ = "cc "
__author__ = "Peter Oettig"
__dependencies__ = ["dict.cc.py"]

iconPath = "{}/icon.png".format(os.path.dirname(__file__))
if not os.path.isfile(iconPath):
    iconPath = ":python_module"


def getItemCount():
    path = configLocation() + "/albert.conf"
    config = configparser.ConfigParser()
    config.read(path)
    if "org.albert.frontend.widgetboxmodel" in config and "itemCout" in config["org.albert.frontend.widgetboxmodel"]:   
        return config["org.albert.frontend.widgetboxmodel"]["itemCount"]
    else:
        # Return default value
        return 5


def handleQuery(query):
    if query.isTriggered:
        fields = query.string.split()
        if len(fields) == 1:
            src = "de"
            dst = "en"
            txt = " ".join(fields)
        elif len(fields) >= 2:
            src = ""
            dst = ""
            if fields[0] == ">":
                src = "en"
                dst = "de"
                txt = " ".join(fields[1:])
            elif fields[0] == "<":
                src = "de"
                dst = "en"
                txt = " ".join(fields[1:])
            else: 
                src = fields[0]
                dst = fields[1]
                txt = " ".join(fields[2:])
        else:
            item = Item(id=__prettyname__, icon=iconPath, completion=query.rawString)
            item.text = __prettyname__
            item.subtext = "Enter a query in the form of \"&lt;srclang&gt; &lt;dstlang&gt; &lt;text&gt;\""
            return item
    
        result = Dict.translate(txt, src, dst)
        itemCount = getItemCount()
        items = []
        for i, (input_word, output_word) in enumerate(result.translation_tuples):
            item = Item(id=__prettyname__, icon=iconPath, completion=query.rawString)
            if i != 0:
                item.text = output_word
                item.subtext = "{}-{} translation of {}".format(src, dst, txt)
                item.addAction(ClipAction("Copy translation to clipboard", output_word))
                items.append(item)                
            else:
                url = "https://dict.cc/?s={}".format(urllib.parse.quote(txt))
                item.text = "Show more results"
                item.subtext = "Opens " + url + " in your default browser"
                item.addAction(UrlAction("Open dict.cc", url))
                items.append(item)
                if i == itemCount - 1:
                    break

        return items

