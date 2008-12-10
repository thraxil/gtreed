__all__ = ["TinyMCE"]

import logging
import pkg_resources

from turbojson.jsonify import encode
from turbogears.widgets import JSSource, JSLink, TextArea, WidgetDescription, \
                               register_static_directory
from turbogears.i18n.utils import get_locale
from tinymce import utils

log = logging.getLogger('tinymce')
js_dir = pkg_resources.resource_filename("tinymce", "static/javascript")
register_static_directory("tinymce", js_dir)



class TinyMCE(TextArea):
    """WYSIWYG editor for textareas. You can pass options directly to TinyMCE
    at consruction or display time via the 'mce_options' dict parameter.
    """
    template = """
    <span xmlns:py="http://purl.org/kid/ns#">
        <textarea
            name="${name}"
            class="${field_class}"
            id="${field_id}"
            rows="${rows}"
            cols="${cols}"
            py:attrs="attrs"
            py:content="value"
        />
        <script type="text/javascript">${TinyMCEInit}</script>
    </span>
    """
    langs = utils.get_available_languages()
    params = ["mce_options", "new_options"]
    params_doc = {
            'mce_options' : _("Options to initialize TinyMCE's javascript. This"
                              " dict will override the defaults"),
            'new_options' : _("Options to initialize TinyMCE's javascript. This"
                              " dict will update the defaults"),
            }
    rows = 25
    mce_options = dict(
        mode = "exact",
        theme = "advanced",
        plugins = "advimage",
        theme_advanced_toolbar_location = "top",
        theme_advanced_toolbar_align = "center",
        theme_advanced_statusbar_location = "bottom",
        extended_valid_elements = "a[href|target|name]",
        theme_advanced_resizing = True,
        paste_use_dialog = False,
        paste_auto_cleanup_on_paste = True,
        paste_convert_headers_to_strong = False,
        paste_strip_class_attributes = "all",
    )
    new_options = {}
    validator = utils.HTMLCleaner()
    javascript = [JSLink("tinymce", "tiny_mce_src.js")]

    def _get_locale(self):
        locale = get_locale().lower()
        if locale in self.langs:
            log.debug("Locale %s is available" % locale)
            return locale
        else:
            log.debug("Locale %s is not available" % locale)
            #See if a less specific locale is available
            locale = locale.split('_')[0]
            if locale in self.langs:
                log.debug("Locale %s is available" % locale)
                return locale
        log.debug(
            "Locale %s is not available, resorting to default locale" % locale
            )
        return None
    _get_locale = utils.cache_for_request('_get_locale')(_get_locale)

    def update_params(self, d):
        super(TinyMCE, self).update_params(d)
        d['mce_options'].update(d['new_options'])
        locale = self._get_locale()
        if locale:
            d['mce_options'].setdefault('language', locale)
        if d['mce_options'].get('mode', 'textareas') == 'exact':
            d['mce_options']['elements'] = d['field_id']
        d['TinyMCEInit'] = "tinyMCE.init(%s);" % encode(d['mce_options'])



class TinyMCEDesc(WidgetDescription):
    name = "TinyMCE"
    for_widget = TinyMCE("mce_sample")
    value = "<h1>This is some sample text.</h1>Edit me as you please."
