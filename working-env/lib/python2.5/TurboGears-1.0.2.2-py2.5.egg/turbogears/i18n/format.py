"""
Localized formatting functions. These functions extract localization data from config files 
located in the data/directory.  
"""

from turbogears.i18n.utils import get_locale
import pkg_resources
import os
import re

def is_locale_format(locale):

    py_filename = pkg_resources.resource_filename("turbogears.i18n.data", "%s.py" %locale)
    if os.path.exists(py_filename):return True
    
    pyc_filename = pkg_resources.resource_filename("turbogears.i18n.data", "%s.pyc" %locale)
    if os.path.exists(pyc_filename):return True
    
    return False
    
def get_locale_module(locale):

    try:
        # check if locale is supported. If not, check again with first part of locale
        # for example, "fi_FI" > "fi".
        
        if not is_locale_format(locale):
        
           locale = locale[:2]
           
        name = "turbogears.i18n.data.%s" %locale
        
        mod = __import__(name)
        parts = name.split(".")[1:]
        for p in parts:mod = getattr(mod, p)
        return mod
    
    except (ImportError, AttributeError):
        return None
        
def get(locale, name, default=None):

    locale = get_locale(locale)
    mod = get_locale_module(locale)
    
    return getattr(mod, name, default)
    
def get_countries(locale=None):
    """
    Returns list of tuples, consisting of international country code and localized 
    name, e.g. ('AU', 'Australia')
    """
    
    countries = get(locale, "countries", {}).items()
    countries.sort(lambda x,y:cmp(x[1], y[1]))
    return countries  
    
def get_country(key, locale=None):
    """
    Returns localized name of country based on international country code
    """
    
    return get(locale, "countries", {})[key]
    
def get_languages(locale=None):
    """Returns list of tuples, with language code and localized name, e.g. ('en', 'English')
    """
    
    languages = get(locale, "languages", {}).items()
    languages.sort(lambda x,y:cmp(x[1], y[1]))
    return languages  

def get_language(key, locale=None):
    """
    Returns localized name of language based on language code
    """
    
    return get(locale, "languages", {})[key]
        
def get_month_names(locale=None):
    """Returns list of full month names, starting with January
    """
    return get(locale, "months", [])
    
def get_abbr_month_names(locale=None):
    """Returns list of abbreviated month names, starting with Jan
    """
    
    return get(locale, "abbrMonths", [])
    
def get_weekday_names(locale=None):
    """Returns list of full weekday names
    """
            
    return get(locale, "days", [])
    
def get_abbr_weekday_names(locale=None):
    """Returns list of abbreviated weekday names
    """

    return get(locale, "abbrDays", get_weekday_names(locale))
    
def get_decimal_format(locale=None):

    return get(locale, "numericSymbols").get("decimal", ".")

def get_group_format(locale=None):

    return get(locale, "numericSymbols").get("group", ",")


def format_number(value, locale=None):
    
    """
    Returns number formatted with grouping for thousands, e.g. 5000000>5,000,000
    """
   
    gf = get_group_format(locale)

    thou=re.compile(r"([0-9])([0-9][0-9][0-9]([%s]|$))" %gf).search

    v=str(value)
    mo=thou(v)
    while mo is not None:
        l = mo.start(0)
        v=v[:l+1]+gf+v[l+1:]
        mo=thou(v)
    return unicode(v)


def format_decimal(value, num_places, locale=None):

    """
    Returns number formatted with grouping for thousands and correct 
    notation, e.g. 5000000.898>5,000,000.898
    """

    format = "%%.%df"%num_places
    str = format%value        
    num, decimals = str.split(".")
    return unicode(format_number(num, locale) + get_decimal_format(locale) + decimals)
    
def format_currency(value, locale=None):

    """
    Returns formatted currency value
    """
    
    return format_decimal(value, 2, locale)

def parse_number(value, locale=None):

    """
    Takes localized number string and returns a long integer  (or throws ValueError if bad format)
    """
    
    return long(value.replace(get_group_format(locale), ""))
    
def parse_decimal(value, locale=None):

    """
    Takes localized decimal string and returns a float  (or throws ValueError if bad format)
    """

    value = value.replace(get_group_format(locale), "")
    value = value.replace(get_decimal_format(locale), ".")
    return float(value)
    
def get_date_format(format, locale=None):

    formats = get(locale, "dateFormats", {})
    return formats.get(format, None)

def format_date(dt, format="medium", locale=None, time_format="", date_format=""):
    """Returns formatted date value.

    Format can be "full", "long", "medium" or "short".  To have complete control over
    formatting, use time_format and date_format parameters.

    @param dt: datetime
    @type dt: datetime.datetime
    @param format: format("full", "long", "medium", "short")
    @type format:string
    @param locale
    @param time_format: standard time formatting string, e.g. %H:%M
    @type time_format:string
    @param time_format: date formatting template string. Template variables include
    standard date formatting string like %d or %Y plus a few locale-specific names:
    %%(abbrmonthname)s, %%(dayname)s, %%(abbrmonthname)s and %%(monthname)s.
    @type time_format:string
    """

    if date_format:
        pattern = date_format
    else:
        pattern = get_date_format(format, locale)

    if not pattern:return str(dt)

    month = dt.month-1
    weekday = dt.weekday()

    # becase strftime() accepts str only but not unicode
    # we encode string to utf-8 and then decode back
    date_str = dt.strftime(pattern.encode('utf8')+time_format)
    return date_str.decode('utf8') % {
        'monthname':get_month_names(locale)[month],
        'abbrmonthname':get_abbr_month_names(locale)[month],
        'dayname':get_weekday_names(locale)[weekday],
        'abbrdayname':get_abbr_weekday_names(locale)[weekday],
    }

