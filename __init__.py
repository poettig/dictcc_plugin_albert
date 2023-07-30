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
import albert

from bs4 import BeautifulSoup

md_iid = "1.0"
md_version = "0.5"
md_name = "Dict.cc Dictionary Lookups"
md_description = "Look up words in the dict.cc dictionary"
md_maintainers = "Peter Oettig"
md_lib_dependencies = ["beautifulsoup4"]

icon = f"{os.path.dirname(__file__)}/icon.png"
if not os.path.isfile(icon):
    icon = [":python_module"]
else:
    icon = [icon]

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
        return f"Languages have to be in the following list: {', '.join(AVAILABLE_LANGUAGES.keys())}"


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


class Plugin(albert.TriggerQueryHandler):
    def id(self):
        return __name__

    def name(self):
        return md_name

    def description(self):
        return md_description

    def synopsis(self):
        return "<srclang> <dstlang> <text>"

    def defaultTrigger(self):
        return "cc "

    def handleTriggerQuery(self, query):
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
                    query.add(
                        albert.Item(
                            id="unsupported_lang_combination",
                            icon=icon,
                            text="Unsupported language combination!",
                            subtext="One language must be one of ['en', 'de']."
                        )
                    )
                    return
                elif src not in AVAILABLE_LANGUAGES or dst not in AVAILABLE_LANGUAGES:
                    query.add(
                        albert.Item(
                            id="unsupported_language",
                            icon=icon,
                            text="Unsupported language!",
                            subtext=f"Source and destination language must be one of {[x for x in AVAILABLE_LANGUAGES.keys()]}."
                        )
                    )
                    return
        else:
            return

        result = Dict.translate(txt, src, dst)
        items = []
        for idx, (input_word, output_word) in enumerate(result.translation_tuples):
            # critical(input_word + " | " + output_word)
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

            items.append(
                albert.Item(
                    id=f"translation_{idx}",
                    text=output,
                    subtext=f"{src}->{dst} translation of '{inp}'",
                    icon=icon,
                    actions=[
                        albert.Action("translation_to_clipboard", "Copy translation to clipboard", lambda out=output: albert.setClipboardText(out))
                    ]
                )
            )

        # If there were no results
        if len(items) == 0:
            items.append(
                albert.Item(
                    id="no_results",
                    text="No results found!",
                    icon=icon
                )
            )
        else:
            # Add URL entry
            item = items.insert(
                0,
                albert.Item(
                    id="open_dictcc",
                    icon=icon,
                    text="Show all results (opens browser)",
                    subtext="Tip: You can scroll Alberts result list with your arrow keys to show more results.",
                    actions=[
                        albert.Action("open", "Open dict.cc", lambda: openUrl(result.request_url))
                    ]
                )
            )

        query.add(items)
