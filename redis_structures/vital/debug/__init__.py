#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""

  `Debug tools`
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde

"""
import re
import sys
import time
import string
import random
import inspect
import subprocess
from math import floor

from functools import wraps
from collections import *

from . import colors


__all__ = (
  "get_terminal_width",
  "line",
  "flag",
  "padd",
  "colorize",
  "uncolorize",
  "bold",
  "table_mapping",
  "gen_rand_str",
  "rand_readable",
  "prepr",
  "get_parent_name",
  "get_obj_name",
  "format_obj_name",
)

def get_terminal_width():
    """ Returns the width of the terminal window """
    # http://www.brandonrubin.me/2014/03/18/
    #    python-snippet-get-terminal-width/
    command = ['tput', 'cols']
    try:
        width = int(subprocess.check_output(command))
    except OSError as e:
        print("Invalid Command '{0}': exit status ({1})".format(
              command[0], e.errno))
    except subprocess.CalledProcessError as e:
        print("'{0}' returned non-zero exit status: ({1})".format(
              command, e.returncode))
    else:
        return width

def line(separator="-·-", color=None, padding=None, num=1):
    for x in range(num):
        """ Prints a line separator the full width of the terminal """
        columns = get_terminal_width()
        # Print separator
        separator = "".join(separator for x in
            range(floor(columns/len(separator))))
        print(padd(colorize(separator.strip(), color), padding))


def padd(text, padding="top"):
    # Add padding to top
    if padding:
        padding = padding.lower()
        return "{}{}{}".format(
            "\n" if padding and (padding == 'top' \
                or padding.lower() == 'all') else "",
            text,
            "\n" if padding and (padding == 'bottom' or \
                padding.lower() == 'all')  else "" )
    return text

def colorize(text, color="BLUE", close=True):
    if color:
        color = getattr(colors, color.upper())
        return color + uncolorize(str(text)) + (colors.RESET if close else "")
    return text

_find_colors = re.compile(r"""(\033\[([\d;]*)m?)""")
def uncolorize(text):
    return _find_colors.sub("", text)

def bold(text, close=True):
    return getattr(colors, "BOLD") + str(text) + (colors.RESET if close else "")

def cut(text, length=50, replace_with="…"):
    text_len = len(uncolorize(text))
    if text_len > length:
        replace_len = len(replace_with)
        color_spans = [
            _colors.span() for _colors in _find_colors.finditer(text) ]
        chars = 0
        _length = length+1 - replace_len
        for i, c in enumerate(text):
            broken = False
            for span in color_spans:
                if span[0] <= i < span[1]:
                    broken = True
                    break
            if broken:
                continue
            chars+=1
            if chars <= _length:
                cutoff = i
            else:
                break
        return text[:cutoff]+replace_with+colors.RESET
    return text

def flag(text=None, color=None, padding=None, show=True):
    if text:
        _flag = padd("({})".format(colorize(text, color)), padding)
        if not show:
            return _flag
        else:
            print(_flag)
    return text

def table_mapping(data, padding=1, separator=" "):
    if data:
        ml = max(len(k) for k in data.keys())+1
        return "\n".join("{}{}{}".format(
            bold(k.rjust(ml+padding, " ")), separator, v)
            for k, v in data.items())
    return ""

def gen_rand_str(*size, use=None, keyspace=None):
    keyspace = keyspace or string.ascii_letters+string.digits
    use = use or random
    return ''.join(use.choice(keyspace)
        for _ in range(use.randint(*size)))

def rand_readable(*size, use=None, density=6):
    use = use or random
    keyspace = [c for c in string.ascii_lowercase if c != "l"]
    vowels = ("a", "e", "i", "o", "u")
    use_vowel = lambda density: not use.randint(0, density)
    return ''.join(use.choice(vowels if use_vowel(density) else keyspace)
        for _ in range(use.randint(*size)))

lambda_sub = re.compile(r"""([\w\d=\s]{0,}?)lambda([\s\w\d]{0,})([:]?)\s+""")\
    .sub
whitespace_sub = re.compile(r"""\s{2,}""").sub
def get_parent_name(meth):
    try:
        name = meth.__self__.__class__.__name__
        assert name != 'module'
        return name
    except (AssertionError, AttributeError):
        if hasattr(meth, '__module__') and meth.__module__:
            if hasattr(meth, '__name__') and meth.__name__ == "<lambda>":
                return whitespace_sub("", inspect.getsource(meth))\
                    .replace("\n", "; ").strip()
            return sys.modules[meth.__module__].__name__ or \
                (sys.modules[meth.__module__].__class__.__name__ \
                if hasattr(sys.modules[meth.__module__], '__class__') \
                else None)
    return None

def get_obj_name(obj):
    has_name_attr = hasattr(obj, '__name__')
    return str(obj.__name__ if has_name_attr else\
        obj.__class__.__name__).strip("<>") \
        if has_name_attr or hasattr(obj, '__class__') \
        else str(obj.__repr__())

def format_obj_name(obj, delim="<>"):
    return "{}{}{}{}".format(
        get_obj_name(obj), delim[0], get_parent_name(obj), delim[1]) \
        if obj else None

# from http://stackoverflow.com/questions/3627793/best-output-type-and-
#   encoding-practices-for-repr-functions
def stdout_encode(u, default='utf-8'):
    encoding = sys.stdout.encoding or default
    return u.encode(encoding, "replace").decode(encoding, "replace")


class prepr(UserString):
    __slots__ = ('obj', 'data', 'options', 'outputs', 'line_break',
        'supplemental', 'hex')
    def __init__(self, *attrs, _self=None, _break=True, _doc=False,
        _address=True, **kwattrs):
        self.obj = _self
        self.line_break = _break;
        self.data = ""
        self.doc = _doc
        self.address = _address
        self.attrs = OrderedDict()
        self.supplemental = None
        self.add_attrs(*attrs, **kwattrs)

    def __str__(self): return str(self.format())
    __repr__ = __str__

    def __call__(self, obj):
        @wraps(obj)
        def wrapper(*args, **kwargs):
            self.obj = args[0]
            supp = obj(args[0])
            self.supplemental = str(supp) if supp else None
            return str(self.format())
        return wrapper

    def __len__(self):
        return len(uncolorize(self.data))

    def add_attrs(self, *args, _order=[], **kwargs):
        """ Adds attributes to the __repr__ string
            @order: optional #list containing order to display kwargs
        """
        for arg in args:
            if isinstance(arg, (tuple, list)):
                key, color = arg
                self.attrs[key] = (None, color)
            else:
                self.attrs[arg] = (None, None)
        if not _order:
            for key, value in kwargs.items():
                self.attrs[key] = (value, None)
        else:
            for key in _order:
                self.attrs[key] = (kwargs[key], None)

    def _getattrs(self, func, obj, attrs):
        for attr in attrs:
            try:
                obj = func(obj, attr)
            except (AttributeError, TypeError):
                raise AttributeError("`{} not in class".format(attr))
        return obj

    def _format_attrs(self):
        """ Formats the self.attrs #OrderedDict """
        attrs = []
        add_attr = attrs.append
        if self.doc and hasattr(self.obj, "__doc__"):
            # Optionally attaches documentation
            if self.obj.__doc__:
                add_attr("`{}`".format(self.obj.__doc__.strip()))
        if self.attrs:
            # Attach request attributes
            for key, value in self.attrs.items():
                value, color = value
                try:
                    value = value or \
                        self._getattrs(getattr, self.obj, key.split("."))
                except AttributeError:
                    pass
                value = colorize(value, color) if color else value
                if value:
                    value = "`{}`".format(value) \
                        if isinstance(value, Look.str_) else value
                    add_attr("{}={}".format(bold(key), value))
                else:
                    add_attr("{}={}".format(bold(key), str(value)))
        # Attach memory address and return
        if self.address:
            add_attr("{}=`{}`".format(bold("hex"), hex(id(self.obj))))
        if len(attrs):
            breaker = "\n    " if self.line_break and len(attrs) > 1 else ""
            return breaker+((", "+breaker).join(attrs))
        else:
            return ""

    def format(self):
        """ Formats the __repr__ string
            -> #str containing __repr__ output
        """
        self.data = "<{}.{}({})>{}".format(
            self.obj.__module__ if hasattr(self.obj, "__module__") \
                else "__main__",
            bold(self.obj.__class__.__name__),
            self._format_attrs(),
            "\n"+self.supplemental if self.supplemental else "")
        return stdout_encode(self.data)
