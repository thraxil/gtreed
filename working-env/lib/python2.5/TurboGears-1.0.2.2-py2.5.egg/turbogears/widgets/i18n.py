import os
from cherrypy import request
from turbogears.i18n import get_locale
from turbogears import startup, config
from turbogears.util import parse_http_accept_header
from turbogears.i18n.utils import lang_in_gettext_format
from turbogears.widgets.base import JSLink, CoreWD, RenderOnlyWD, static

__all__ = ["CalendarLangFileLink", "LocalizableJSLink"]

class CalendarLangFileLink(JSLink):
    """Links to proper calendar.js language file depending on HTTP info."""
    def update_params(self, d):
        accept_language = parse_http_accept_header(            
            request.headers.get("Accept-Language")
        ) or ['']
        accept_charset = parse_http_accept_header(
            request.headers.get("Accept-Charset")
        ) or ['']
        base_dir = config.get("static_filter.dir", 
                              path="/tg_widgets/%s" % self.mod)
        def find_link():
            for name_pattern in self.name:
                for lang in accept_language:
                    for charset in accept_charset:
                        params = dict()
                        params["lang"] = lang
                        params["charset"] = charset
                        params["gettext_lang"] = lang_in_gettext_format(lang)
                        params["gettext_charset"] = charset.upper()
                        params["custom_lang"] = self.custom_lang(lang)
                        params["custom_charset"] = self.custom_charset(charset)
                        name = name_pattern % params
                        if os.path.exists(base_dir + '/' + name):
                            link = "/%stg_widgets/%s/%s" % (startup.webpath,
                                                            self.mod,
                                                            name)
                            return link
        d["link"] = find_link()

    def custom_lang(self, lang):
        return None

    def custom_charset(self, charset):
        return None

class LocalizableJSLink(JSLink):

    """
    Provides a simple way to include language-specific data in your
    Javascript code.

    Language file to use is determined from the user's locale or from the 'language'
    parameter. If there is no language file for the language (determined via
    'supported_languages' parameter) than 'default_language' is used.
    """

    default_language = 'en'
    supported_languages = ['en']
    params = ['default_language', 'language', 'supported_languages']
    params_doc = {
        'language' : 'language code to use ' \
            '(overrides user locale setting which is the default)',
        'default_language' : 'language code to use ' \
                'if specified language is not supported',
        'supported_languages' : 'list of supported language codes ' \
                ' (which means corresponding language files exist)',
    }

    def update_params(self, d):
        super(LocalizableJSLink, self).update_params(d)
        language = d.get('language') or get_locale()
        if language not in self.supported_languages:
            language = self.default_language
        d['link'] = d['link'] % {'lang':language}

class LocalizableJSLinkDesc(CoreWD, RenderOnlyWD):
    name = "Localizable JS Link"
    for_widget = LocalizableJSLink("turbogears", "js/yourscript-%(lang)s.js")
