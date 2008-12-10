"""Convenient validators and converters for data coming in from the web.

This module also imports everything from formencode.validators, so all
common validation routines are available here."""

import pkg_resources
#XXX Remove in 1.0.3 when everyone has already upgraded FE
#    so we don't need to keep this in sync with setup.py
pkg_resources.require("FormEncode >= 0.7.1")

import time
import re
from datetime import datetime
import cgi # FieldStorageUploadConverter
import warnings

import simplejson
from formencode.validators import *
from formencode.compound import *
from formencode.api import Invalid, NoDefault
from formencode.schema import Schema
from formencode import ForEach

from turbogears.i18n import format
from turbogears import util
from turbojson import jsonify

from formencode import validators # Needed to disambiguate the Number validator... 

import __builtin__

def _(s): return s # dummy

Validator.gettextargs['domain'] = 'FormEncode' # FormEncode should call Tg's gettext \
                                               # function with domain = "FormEncode"

class TgFancyValidator(FancyValidator):
    gettextargs = {'domain':'TurboGears'}
    
class Money(TgFancyValidator):
    
    messages = {
        'badFormat': _('Invalid number format'),
        'empty': _('Empty values not allowed'),
    }
    
    def __init__(self, allow_empty=None, *args, **kw):
        if allow_empty is not None:
            warnings.warn("Use not_empty instead of allow_empty",
                          DeprecationWarning, 2)
            not_empty = not allow_empty
            kw["not_empty"] = not_empty
        super(Money, self).__init__(*args, **kw)

    def _to_python(self, value, state):
        """ parse a string and returns a float or integer """
        try:
            return format.parse_decimal(value)
        except ValueError:
            raise Invalid(self.message('badFormat', state), value, state)

    def _from_python(self, value, state):
        """ returns a string using the correct grouping """
        return format.format_currency(value)


class Number(TgFancyValidator):

    def _to_python(self, value, state):
        """ parse a string and returns a float or integer """
        if isinstance(value, basestring):
            try:
                value = format.parse_decimal(value)
            except ValueError:
                pass
        return validators.Number.to_python(value, state)

    def _from_python(self, value, state):
        """ returns a string using the correct grouping """
        dec_places = util.find_precision(value)
        if dec_places > 0:
            return format.format_decimal(value, dec_places)
        else:
            return format.format_number(value)


class DateTimeConverter(TgFancyValidator):

    """
    Converts Python date and datetime objects into string representation and back.
    """
    messages = {
        'badFormat': _('Invalid datetime format'),
        'empty': _('Empty values not allowed'),
    }

    def __init__(self, format = "%Y/%m/%d %H:%M", allow_empty = None,
                *args, **kwargs):
        if allow_empty is not None:
            warnings.warn("Use not_empty instead of allow_empty",
                          DeprecationWarning, 2)
            not_empty = not allow_empty
            kwargs["not_empty"] = not_empty
        super(TgFancyValidator, self).__init__(*args, **kwargs)
        self.format = format

    def _to_python(self, value, state):
        """ parse a string and return a datetime object. """
        if value and isinstance(value, datetime):
            return value
        else:
            try:
                tpl = time.strptime(value, self.format)
            except ValueError:
                raise Invalid(self.message('badFormat', state), value, state)
            # shoudn't use time.mktime() because it can give OverflowError,
            # depending on the date (e.g. pre 1970) and underlying C library
            return datetime(year=tpl.tm_year, month=tpl.tm_mon, day=tpl.tm_mday,
                    hour=tpl.tm_hour, minute=tpl.tm_min, second=tpl.tm_sec)

    def _from_python(self, value, state):
        if not value:
            return None
        elif isinstance(value, datetime):
            # Python stdlib can only handle dates with year greater than 1900
            if value.year <= 1900:
                return strftime_before1900(value, self.format)
            else:
                return value.strftime(self.format)
        else:
            return value

# formencode trunk contains UnicodeString implementation 
# but it is different from ours and was broken at the time.
# remove this impl. when formencode.validators.UnicodeString will be identical to ours.
class UnicodeString(String):
    encoding = 'utf-8'
    messages = {
        'badEncoding' : _("Invalid data or incorrect encoding"),
    }
    def __init__(self, inputEncoding=None, outputEncoding=None, **kw):
        String.__init__(self, **kw)
        self.inputEncoding = inputEncoding or self.encoding
        self.outputEncoding = outputEncoding or self.encoding
    def _to_python(self, value, state):
        if value:
            if isinstance(value, unicode):
                return value
            if hasattr(value, '__unicode__'):
                return unicode(value)
            try:
                return unicode(value, self.inputEncoding)
            except UnicodeDecodeError:
                raise Invalid(self.message('badEncoding', state), value, state)
        return u''
    def _from_python(self, value, state):
        if hasattr(value, '__unicode__'):
            value = unicode(value)
        if isinstance(value, unicode):
            return value.encode(self.outputEncoding)
        return str(value)

# another formencode workaround,
# see #1464357 on FE bugtracker (http://tinyurl.com/lm9ae).
# Custom version of FieldStorage validator that does not break FE schema validator.
class FieldStorageUploadConverter(TgFancyValidator):
    def to_python(self, value, state=None):
        if isinstance(value, cgi.FieldStorage):
            if value.filename:
                return value
            raise Invalid('invalid', value, state)
        else:
            return value 

# For translated messages that are not wrapped in a Validator.messages
# dictionary, we need to reinstate the Turbogears gettext function under
# the name "_", with the "TurboGears" domain, so that the TurboGears.mo
# file is selected.
import turbogears.i18n
_ = lambda s: turbogears.i18n.gettext(s, domain='TurboGears')

class MultipleSelection(ForEach):
    if_missing = NoDefault
    if_empty = []

    def to_python(self, value, state=None):
        try:
            return super(MultipleSelection, self).to_python(value, state)
        except Invalid:
            raise Invalid(_("Please select at least a value"), value, state)

class Schema(Schema):
    """ A Schema validator """
    filter_extra_fields = True
    allow_extra_fields = True
    if_key_missing = None

    def from_python(self,value,state=None):
        # The Schema shouldn't do any from_python conversion because
        # adjust_value already takes care of that for all childs.
        return value

class JSONValidator(TgFancyValidator):

    def _from_python(self, value, state):
        return jsonify.encode(value)

    def _to_python(self, value, state):
        return simplejson.loads(value)

_illegal_s = re.compile(r"((^|[^%])(%%)*%s)")

def _findall(text, substr):
     # Also finds overlaps
     sites = []
     i = 0
     while 1:
         j = text.find(substr, i)
         if j == -1:
             break
         sites.append(j)
         i = j+1
     return sites

def strftime_before1900(dt, fmt):
    """
    A strftime implementation that supports proleptic Gregorian dates before 1900.

    @see: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/306860
    """
    import datetime
    if _illegal_s.search(fmt):
        raise TypeError("This strftime implementation does not handle %s")
    if dt.year > 1900:
        return dt.strftime(fmt)

    year = dt.year
    # For every non-leap year century, advance by
    # 6 years to get into the 28-year repeat cycle
    delta = 2000 - year
    off = 6*(delta // 100 + delta // 400)
    year = year + off

    # Move to around the year 2000
    year = year + ((2000 - year)//28)*28
    timetuple = dt.timetuple()
    s1 = time.strftime(fmt, (year,) + timetuple[1:])
    sites1 = _findall(s1, str(year))

    s2 = time.strftime(fmt, (year+28,) + timetuple[1:])
    sites2 = _findall(s2, str(year+28))

    sites = []
    for site in sites1:
        if site in sites2:
            sites.append(site)

    s = s1
    syear = "%4d" % (dt.year,)
    for site in sites:
        s = s[:site] + syear + s[site+4:]
    return s

