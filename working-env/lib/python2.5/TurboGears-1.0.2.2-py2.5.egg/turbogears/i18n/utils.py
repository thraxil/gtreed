"""
General i18n utility functions.
"""

import os
import urllib
import httplib
import re
import cherrypy
from turbogears import config
from turbogears.util import parse_http_accept_header, request_available

def google_translate(from_lang, to_lang, text):

    params = urllib.urlencode({"langpair":"%s|%s" %(from_lang, to_lang), "text":text,
    "ie":"UTF8", "oe":"UTF8"})
    conn = httplib.HTTPConnection("translate.google.com")
    conn.request("POST", "/translate_t", params)

    resp = conn.getresponse()
    s = resp.read()
    conn.close()

    match = re.compile('<textarea name=q.*?>(.*?)</textarea>',
                       re.DOTALL).search(s)
    data = match.groups()[0]
    return unicode(data, "utf-8").strip()

def lang_in_gettext_format(lang):
    if len(lang) > 2:
        country = lang[3:].upper()
        lang = lang[:2] + "_" + country
    return lang

def get_accept_languages(accept):
    """Returns a list of languages, by order of preference, based on an
    HTTP Accept-Language string.See W3C RFC 2616
    (http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html) for specification.
    """
    langs = parse_http_accept_header(accept)
    for index, lang in enumerate(langs):
        langs[index] = lang_in_gettext_format(lang)
    return langs

def get_locale(locale=None):
    """
    Returns user locale, using _get_locale or app-specific locale lookup function.
    """
    if not locale:
        get_locale_f = config.get("i18n.get_locale", _get_locale)
        locale = get_locale_f()
    return locale

def _get_locale():
    """Default function for returning locale. First looks in session for locale key,
    then checks the HTTP Accept-Language header, and finally checks the config default
    locale setting. This can be replaced by your own function by setting cherrypy
    config setting i18n.get_locale to your function name.
    """
    if not request_available():
        return config.get("i18n.default_locale", "en")
    
    if config.get("session_filter.on", False):
        locale_key = config.get("i18n.session_key", "locale")
        locale = cherrypy.session.get(locale_key)
        if locale:
            return locale
    browser_accept_lang = _get_locale_from_accept_header()
    return browser_accept_lang or config.get("i18n.default_locale", "en")

def _get_locale_from_accept_header():
    """
    Checks HTTP Accept-Language header to find preferred language if any.
    """
    try:
        header = cherrypy.request.headers.get("Accept-Language")
        if header:
            accept_languages = get_accept_languages(header)
            if accept_languages:
                return accept_languages[0]
    except AttributeError:
        pass

def set_session_locale(locale):
    """
    Sets the i18n session locale.

    Raises an error if session support is not enabled.
    """
    cherrypy.session[config.get("i18n.session_key", "locale")] = locale



