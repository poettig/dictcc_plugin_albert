# -*- coding: utf-8 -*-

"""
Translate text using dict.cc via dict.cc.py.

Usage: cc <src lang> <dest lang> <text>
       cc [>] <text> for en->de
       cc < <text> for de->en
Example: cc en fr hello
"""

import os
import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup
    BeautifulSoup.find_all = BeautifulSoup.findAll

from albertv0 import *

__iid__ = "PythonInterface/v0.1"
__prettyname__ = "Dict.cc Translator"
__version__ = "1.0"
__trigger__ = "cc "
__author__ = "Peter Oettig"
__dependencies__ = []

iconPath = "%s/icon.png" % (os.path.dirname(__file__))
if not os.path.isfile(iconPath):
    iconPath = ":python_module"

error_text = "Something went wrong. Please report your query to my developer via a Git Issue!"

AVAILABLE_LANGUAGES = {
    "en": "english",
    "de": "german",
    "fr": "french",
    "sv": "swedish",
    "es": "spanish",
    "nl": "dutch",
    "bg": "bulgarian",
    "ro": "romanian",
    "it": "italian",
    "pt": "portuguese",
    "ru": "russian"
}


class UnavailableLanguageError(Exception):
    def __str__(self):
        return "Languages have to be in the following list: {}".format(
            ", ".join(AVAILABLE_LANGUAGES.keys()))


class Result(object):
    def __init__(self, from_lang=None, to_lang=None, translation_tuples=None, request_url=None):
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.translation_tuples = list(translation_tuples) \
            if translation_tuples else []
        self.request_url = request_url

    @property
    def n_results(self):
        return len(self.translation_tuples)


class Dict(object):
    @classmethod
    def translate(cls, word, from_language, to_language):
        if any(map(lambda l: l.lower() not in AVAILABLE_LANGUAGES.keys(),
                   [from_language, to_language])):
            raise UnavailableLanguageError

        response = cls._get_response(word, from_language, to_language)
        response_body = response.content.decode("utf-8")
        result = cls._parse_response(response_body)
        result.request_url = response.request.url

        return result

    @classmethod
    def _get_response(cls, word, from_language, to_language):
        res = requests.get(
            url="https://" + from_language.lower() + "-" + to_language.lower() + ".dict.cc",
            params={"s": word.encode("utf-8")},
            headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0'}
        )
        return res

    # Quick and dirty: find javascript arrays for input/output words on response body
    @classmethod
    def _parse_response(cls, response_body):
        soup = BeautifulSoup(response_body, "html.parser")

        suggestions = [tds.find_all("a") for tds in soup.find_all("td", class_="td3nl")]
        if len(suggestions) == 2:
            languages = [lang.string for lang in soup.find_all("td", class_="td2")][:2]
            if len(languages) != 2:
                raise Exception("dict.cc results page layout change, please raise an issue.")

            return Result(
                from_lang=languages[0],
                to_lang=languages[1],
                translation_tuples=zip(
                    [e.string for e in suggestions[0]],
                    [e.string for e in suggestions[1]]
                ),
            )

        translations = [tds.find_all("a") for tds in soup.find_all("td", class_="td7nl", attrs={'dir': "ltr"})]
        if len(translations) >= 2:
            languages = [next(lang.strings) for lang in soup.find_all("td", class_="td2", attrs={'dir': "ltr"})]
            if len(languages) != 2:
                raise Exception("dict.cc results page layout change, please raise an issue.")

            return Result(
                from_lang=languages[0],
                to_lang=languages[1],
                translation_tuples=zip(
                    [" ".join(map(lambda e: " ".join(e.strings), r)) for r in translations[0:-1:2]],
                    [" ".join(map(lambda e: e.string if e.string else "".join(e.strings), r)) for r in
                     translations[1:-1:2]]
                ),
            )

        return Result()


def resolve(from_lang, to_lang, input_word, output_word, reference, is_source):
    if reference in from_lang:
        if is_source:
            inp = input_word
            output = output_word
        else:
            inp = output_word
            output = input_word
    elif reference in to_lang:
        if is_source:
            inp = output_word
            output = input_word
        else:
            inp = input_word
            output = output_word
    else:
        inp = None
        output = error_text

    return inp, output


def handleQuery(query):
    if query.isTriggered:
        fields = query.string.split()
        if len(fields) == 1:
            src = "de"
            dst = "en"
            txt = " ".join(fields)
        elif len(fields) >= 2:
            if fields[0] == ">":
                src = "de"
                dst = "en"
                txt = " ".join(fields[1:])
            elif fields[0] == "<":
                src = "en"
                dst = "de"
                txt = " ".join(fields[1:])
            else:
                src = fields[0]
                dst = fields[1]
                txt = " ".join(fields[2:])

                # If neither source nor destination are valid languages, assume that it is a standard case with
                # multiple words (cc kinder erziehen)
                if src not in AVAILABLE_LANGUAGES and dst not in AVAILABLE_LANGUAGES:
                    src = "de"
                    dst = "en"
                    txt = " ".join(fields)
                elif src not in ["de", "en"] and dst not in ["de", "en"]:
                    item = Item(id=__prettyname__, icon=iconPath, completion=query.rawString)
                    item.text = "Unsupported language combination!"
                    item.subtext = "One language must be one of ['en', 'de']."
                    return item
                elif src not in AVAILABLE_LANGUAGES or dst not in AVAILABLE_LANGUAGES:
                    item = Item(id=__prettyname__, icon=iconPath, completion=query.rawString)
                    item.text = "Unsupported language!"
                    item.subtext = "Source and destination language must be one of %s." % [x for x in AVAILABLE_LANGUAGES.keys()]
                    return item
        else:
            item = Item(id=__prettyname__, icon=iconPath, completion=query.rawString)
            item.text = __prettyname__
            item.subtext = "Enter a query in the form of \"&lt;srclang&gt; &lt;dstlang&gt; &lt;text&gt;\""
            return item

        result = Dict.translate(txt, src, dst)
        items = []
        for input_word, output_word in result.translation_tuples:
            # Select correct value as translation
            # Dict.cc can only do <any language> <-> German or English
            # If src->dst are de->en or en->de, de is always the output
            # If src or dst is something else, it can vary, but we can detect that:
            #   * If src or dst is german, from or to is "Deutsch", the other one is the other language
            #   * If src or dst is english, form or to is "English", the other one is the other language
            if src == "de" and dst == "en":
                inp = output_word
                output = input_word
            elif src == "en" and dst == "de":
                inp = input_word
                output = output_word
            elif src == "de":
                inp, output = resolve(result.from_lang, result.to_lang, input_word, output_word, "Deutsch", True)
            elif dst == "de":
                inp, output = resolve(result.from_lang, result.to_lang, input_word, output_word, "Deutsch", False)
            elif src == "en":
                inp, output = resolve(result.from_lang, result.to_lang, input_word, output_word, "English", True)
            elif dst == "en":
                inp, output = resolve(result.from_lang, result.to_lang, input_word, output_word, "English", False)
            else:
                inp, output = error_text

            item = Item(id=__prettyname__, icon=iconPath, completion=query.rawString)
            item.text = output
            item.subtext = "%s->%s translation of '%s'" % (src, dst, inp)
            item.addAction(ClipAction("Copy translation to clipboard", output))
            items.append(item)

        # Add URL entry
        item = Item(id=__prettyname__, icon=iconPath, completion=query.rawString)
        item.addAction(UrlAction("Open dict.cc", result.request_url))
        item.text = "Show all results (opens browser)"
        item.subtext = "Tip: You can scroll Alberts result list with your arrow keys to show more results."
        items.insert(0, item)

        # If there where no results
        if len(items) == 0:
            item = Item(id=__prettyname__, icon=iconPath, completion=query.rawString)
            item.text = "No results found!"
            items.append(item)

        return items
