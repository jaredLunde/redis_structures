#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""

  `Debugging Tools`
  ```Simple tools to debug and time your scripts & structures```
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
  2014 Jared Lunde © The MIT License (MIT)
  http://github.com/jaredlunde

"""
import os
import re
import gc
import sys
import time
import datetime
import types
import string
import random
import inspect
import importlib
try:
    import numpy as np
    np.random = random.SystemRandom()
except ImportError:
    try:
        import statistics as np
        np.sum = sum
        np.random = random.SystemRandom()
        np.max = max
        np.min = min
        np.std = np.pstdev
    except ImportError:
        from redis_structures.debug.stats import mean, median, pstdev, np
        np.sum = sum
        np.random = random.SystemRandom()
        np.max = max
        np.min = min
        np.std = pstdev
        np.mean = mean
        np.median = median
import subprocess
from io import StringIO
from math import floor
from pydoc import locate
from codecs import getencoder
from functools import wraps
from collections import *

from redis_structures.debug import colors, tlds


__all__ = (
  "stdout_encode",
  "get_terminal_width",
  "line",
  "flag",
  "padd",
  "colorize",
  "uncolorize",
  "bold",
  "cut",
  "table_mapping",
  "gen_rand_str",
  "rand_readable",
  "prepr",
  "RandData",
  "Look",
  "Logg",
  "logg",
  "ProgressBar",
  "Timer",
  "Compare",
  "get_parent_name",
  "get_parent_obj",
  "get_obj_name",
  "format_obj_name",
)


def stdout_encode(u, default='utf-8'):
    """ Encodes a given string with the proper standard out encoding
        If sys.stdout.encoding isn't specified, it this defaults to @default

        @default: default encoding

        -> #str with standard out encoding
    """
    # from http://stackoverflow.com/questions/3627793/best-output-type-and-
    #   encoding-practices-for-repr-functions
    encoding = sys.stdout.encoding or default
    return u.encode(encoding, "replace").decode(encoding, "replace")


def get_terminal_width():
    """ -> #int width of the terminal window """
    # http://www.brandonrubin.me/2014/03/18/python-snippet-get-terminal-width/
    command = ['tput', 'cols']
    try:
        width = int(subprocess.check_output(command))
    except OSError as e:
        print(
            "Invalid Command '{0}': exit status ({1})".format(
                command[0], e.errno))
    except subprocess.CalledProcessError as e:
        print(
            "'{0}' returned non-zero exit status: ({1})".format(
                command, e.returncode))
    else:
        return width


def line(separator="-·-", color=None, padding=None, num=1):
    """ Prints a line separator the full width of the terminal.

        @separator: the #str chars to create the line from
        @color: line color from :mod:redis_structures.debug.colors
        @padding: adds extra lines to either the top, bottom or both
            of the line via :func:padd
        @num: #int number of lines to print
        ..
            from redis_structures.debug import line
            line("__")
            ____________________________________________________________________
        ..
    """
    for x in range(num):
        columns = get_terminal_width()
        separator = "".join(
            separator for x in
            range(floor(columns/len(separator))))
        print(padd(colorize(separator.strip(), color), padding))


def padd(text, padding="top", size=1):
    """ Adds extra new lines to the top, bottom or both of a String

        @text: #str text to pad
        @padding: #str 'top', 'bottom' or 'all'
        @size: #int number of new lines

        -> #str padded @text
        ..
            from redis_structures.debug import *

            padd("Hello world")
            # -> '\\nHello world'

            padd("Hello world", size=5, padding="all")
            # -> '\\n\\n\\n\\n\\nHello world\\n\\n\\n\\n\\n'
        ..
    """
    if padding:
        padding = padding.lower()
        pad_all = padding == 'all'
        padding_top = ""
        if padding and (padding == 'top' or pad_all):
            padding_top = "".join("\n" for x in range(size))
        padding_bottom = ""
        if padding and (padding == 'bottom' or pad_all):
            padding_bottom = "".join("\n" for x in range(size))
        return "{}{}{}".format(padding_top, text, padding_bottom)
    return text


def colorize(text, color="BLUE", close=True):
    """ Colorizes text for terminal outputs

        @text: #str to colorize
        @color: #str color from :mod:colors
        @close: #bool whether or not to reset the color

        -> #str colorized @text
        ..
            from redis_structures.debug import colorize

            colorize("Hello world", "blue")
            # -> '\x1b[0;34mHello world\x1b[1;m'

            colorize("Hello world", "blue", close=False)
            # -> '\x1b[0;34mHello world'
        ..
    """
    if color:
        color = getattr(colors, color.upper())
        return color + uncolorize(str(text)) + (colors.RESET if close else "")
    return text


_find_colors = re.compile(r"""(\033\[([\d;]*)m?)""")
def uncolorize(text):
    """ Attempts to remove color and reset flags from text via regex pattern

        @text: #str text to uncolorize

        -> #str uncolorized @text
        ..
            from redis_structures.debug import uncolorize

            uncolorize('\x1b[0;34mHello world\x1b[1;m')
            # -> 'Hello world'
        ..
    """
    return _find_colors.sub("", text)


def bold(text, close=True):
    """ Bolds text for terminal outputs

        @text: #str to bold
        @close: #bool whether or not to reset the bold flag

        -> #str bolded @text
        ..
            from redis_structures.debug import bold

            bold("Hello world")
            # -> '\x1b[1mHello world\x1b[1;m'

            bold("Hello world", close=False)
            # -> '\x1b[1mHello world'
        ..
    """
    return getattr(colors, "BOLD") + str(text) + (colors.RESET if close else "")


def cut(text, length=50, replace_with="…"):
    """ Shortens text to @length, appends @replace_with to end of string
        if the string length is > @length

        @text: #str text to shortens
        @length: #int max length of string
        @replace_with: #str to replace chars beyond @length with
        ..
            from redis_structures.debug import cut

            cut("Hello world", 8)
            # -> 'Hello w…'

            cut("Hello world", 15)
            # -> 'Hello world'
        ..
    """
    text_len = len(uncolorize(text))
    if text_len > length:
        replace_len = len(replace_with)
        color_spans = [
            _colors.span() for _colors in _find_colors.finditer(text)]
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
            chars += 1
            if chars <= _length:
                cutoff = i
            else:
                break
        if color_spans:
            return text[:cutoff] + replace_with + colors.RESET
        else:
            return text[:cutoff] + replace_with
    return text


def flag(text=None, color=None, padding=None, show=True):
    """ Wraps @text in parentheses (), optionally colors and pads and
        prints the text.

        @text: #str text to (flag)
        @color: #str color to :func:colorize the text within
        @padding: #str location of padding from :func:padd
        @show: #bool whether or not to print the text in addition to returning
            it

        -> #str (flagged) text
        ..
            from redis_structures.debug import flag

            flag("Hello world", "blue")
            # -> (Hello world)
            #    '(\x1b[0;34mHello world\x1b[1;m)'

            flag("Hello world", "blue", show=False)
            # -> '(\x1b[0;34mHello world\x1b[1;m)'

            flag("Hello world", color="blue", padding="all")
            # ->
            #    (Hello world)
            #
            #    '\\n(\x1b[0;34mHello world\x1b[1;m)\\n'
        ..
    """
    _flag = None
    if text:
        _flag = padd("({})".format(colorize(text, color)), padding)
        if not show:
            return _flag
        else:
            print(_flag)
    return _flag or text


def table_mapping(data, padding=1, separator=" "):
    """ Pretty prints a one-dimensional key: value mapping

        @data: #dict data to pretty print
        @padding: #int number of spaces to pad the left side of the key with
        @separator: #str chars to separate the key and value pair with

        -> #str pretty one dimensional table
        ..
            from redis_structures.debug import table_mapping

            print(table_mapping({"key1": "val1", "key2": "val2"}))
            # -> \x1b[1m  key1\x1b[1;m val1
            #    \x1b[1m  key2\x1b[1;m val2

            print(table_mapping({"key1": "val1", "key2": "val2"}, padding=4))
            # ->    \x1b[1m     key1\x1b[1;m val1
            #       \x1b[1m     key2\x1b[1;m val2

            print(table_mapping(
                {"key1": "val1", "key2": "val2"}, padding=4, separator=": "))
            # ->    \x1b[1m     key1\x1b[1;m: val1
            #       \x1b[1m     key2\x1b[1;m: val2
        ..
    """
    if data:
        ml = max(len(k) for k in data.keys())+1
        return "\n".join("{}{}{}".format(
            bold(k.rjust(ml+padding, " ")), separator, v)
            for k, v in data.items())
    return ""


def gen_rand_str(*size, use=None, keyspace=None):
    """ Generates a random string using random module specified in @use within
        the @keyspace

        @*size: #int size range for the length of the string
        @use: the random module to use
        @keyspace: #str chars allowed in the random string
        ..
            from redis_structures.debug import gen_rand_str

            gen_rand_str()
            # -> 'PRCpAq'

            gen_rand_str(1, 2)
            # -> 'Y'

            gen_rand_str(12, keyspace="abcdefg")
            # -> 'gaaacffbedf'
        ..
    """
    keyspace = keyspace or (string.ascii_letters + string.digits)
    keyspace = [char for char in keyspace]
    use = use or np.random
    if size:
        size = size if len(size) == 2 else (size[0], size[0] + 1)
    else:
        size = (6, 7)
    return ''.join(
        use.choice(keyspace)
        for _ in range(use.randint(*size)))


def rand_readable(*size, use=None, density=6):
    """ Generates a random string with readable characters using
        random module specified in @use

        @*size: #int size range for the length of the string
        @use: the random module to use
        @density: how often to include a vowel, you can expect a vowel about
            once every (density) nth character
        ..
            from redis_structures.debug import rand_readable

            rand_readable()
            # -> 'hyiaqk'

            rand_readable(15, 20)
            # -> 'oqspyywvhifsaikiaoi'

            rand_readable(15, 20, density=1)
            # -> 'oeuiueioieeioeeeue'

            rand_readable(15, 20, density=15)
            # -> 'ktgjabwdqhgeanh'
        ..

    """
    use = use or np.random
    keyspace = [c for c in string.ascii_lowercase if c != "l"]
    vowels = ("a", "e", "i", "o", "u")

    def use_vowel(density): not use.randint(0, density)
    if size:
        size = size if len(size) == 2 else (size[0]-1, size[0])
    else:
        size = (6, 7)
    return ''.join(
        use.choice(vowels if use_vowel(density) else keyspace)
        for _ in range(use.randint(*size)))


lambda_sub = re.compile(r"""([\w\d=\s]{0,}?)lambda([\s\w\d]{0,})([:]?)\s+""")\
    .sub
whitespace_sub = re.compile(r"""\s{2,}""").sub
def get_parent_name(obj):
    """ Gets the name of the object containing @obj and returns as a string

        @obj: any python object

        -> #str parent object name or None
        ..
            from redis_structures.debug import get_parent_name

            get_parent_name(get_parent_name)
            # -> 'redis_structures.debug'

            get_parent_name(redis_structures.debug)
            # -> 'vital'

            get_parent_name(str)
            # -> 'builtins'
        ..
    """
    parent_obj = get_parent_obj(obj)
    parent_name = get_obj_name(parent_obj) if parent_obj else None
    while parent_obj:
        parent_obj = get_parent_obj(parent_obj)
        if parent_obj:
            parent_name = "{}.{}".format(get_obj_name(parent_obj), parent_name)
    if not parent_name or not len(parent_name):
        parent_name = None
        objname = get_obj_name(obj)
        if objname and len(objname.split(".")) > 1:
            return ".".join(objname.split(".")[:-1])
        return None
    return parent_name


def get_class_that_defined_method(meth):
    """ Gets the class object which defined a given method

        @meth: a class method

        -> owner class object
    """
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return None


def get_parent_obj(obj):
    """ Gets the name of the object containing @obj and returns as a string

        @obj: any python object

        -> #str parent object name or None
        ..
            from redis_structures.debug import get_parent_obj

            get_parent_obj(get_parent_obj)
            # -> <module 'redis_structures.debug' from>
        ..
    """
    try:
        cls = get_class_that_defined_method(obj)
        if cls and cls != obj:
            return cls
    except AttributeError:
        pass
    if hasattr(obj, '__module__') and obj.__module__:
        try:
            module = importlib.import_module(obj.__module__)
            objname = get_obj_name(obj).split(".")
            owner = getattr(module, objname[-2])
            return getattr(owner, objname[-1])
        except Exception:
            try:
                return module
            except Exception:
                pass
    try:
        assert hasattr(obj, '__qualname__') or hasattr(obj, '__name__')
        objname = obj.__qualname__ if hasattr(obj, '__qualname__') \
            else obj.__name__
        objname = objname.split(".")
        assert len(objname) > 1
        return locate(".".join(objname[:-1]))
    except Exception:
        try:
            module = importlib.import_module(".".join(objname[:-1]))
            return module
        except Exception:
            pass
    return None


def get_obj_name(obj, full=True):
    """ Gets the #str name of @obj

        @obj: any python object
        @full: #bool returns with parent name as well if True

        -> #str object name
        ..
            from redis_structures.debug import get_parent_obj

            get_obj_name(get_obj_name)
            # -> 'get_obj_name'

            get_obj_name(redis_structures.debug.Timer)
            # -> 'Timer'
        ..
    """
    has_name_attr = hasattr(obj, '__name__')
    if has_name_attr and obj.__name__ == "<lambda>":
        try:
            src = whitespace_sub("", inspect.getsource(obj))\
                .replace("\n", "; ").strip(" <>")
        except OSError:
            src = obj.__name__
        return lambda_sub("", src)
    if hasattr(obj, '__qualname__') and obj.__qualname__:
        return obj.__qualname__.split(".")[-1]
    elif has_name_attr and obj.__name__:
        return obj.__name__.split(".")[-1]
    elif hasattr(obj, '__class__'):
        return str(obj.__class__.__name__).strip("<>")
    else:
        return str(obj.__repr__())


def format_obj_name(obj, delim="<>"):
    """ Formats the object name in a pretty way

        @obj: any python object
        @delim: the characters to wrap a parent object name in

        -> #str formatted name
        ..
            from redis_structures.debug import format_obj_name

            format_obj_name(redis_structures.debug.Timer)
            # -> 'Timer<redis_structures.debug>'

            format_obj_name(redis_structures.debug)
            # -> 'debug<vital>'

            format_obj_name(redis_structures.debug.Timer.time)
            # -> 'time<redis_structures.debug.Timer>'
        ..
    """
    pname = ""
    parent_name = get_parent_name(obj)
    if parent_name:
        pname = "{}{}{}".format(delim[0], get_parent_name(obj), delim[1])
    return "{}{}".format(get_obj_name(obj), pname)


class prepr(UserString):
    __slots__ = (
        'obj', 'data', 'options', 'outputs', 'line_break',
        'supplemental', 'hex', 'pretty')

    def __init__(self, *attrs, _self=None, _break=False, _doc=False,
                 _address=True, _pretty=False, **kwattrs):
        self.obj = _self
        self.line_break = _break
        self.data = ""
        self.doc = _doc
        self.address = _address
        self.attrs = OrderedDict()
        self.supplemental = None
        self.pretty = _pretty
        self.add_attrs(*attrs, **kwattrs)

    def __str__(self):
        return str(self.format())

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
        _bold = bold
        _colorize = colorize
        if not self.pretty:
            _bold = lambda x: x
            _colorize = lambda x, c: x
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
                value = _colorize(value, color) if color else value
                if value:
                    value = "`{}`".format(value) \
                        if isinstance(value, Look.str_) else value
                    add_attr("{}={}".format(_bold(key), value))
                else:
                    add_attr("{}={}".format(_bold(key), str(value)))
        if len(attrs):
            breaker = "\n    " if self.line_break and len(attrs) > 1 else ""
            return breaker + ((", "+breaker).join(attrs)) + breaker.strip(" ")
        else:
            return ""

    def format(self):
        """ Formats the __repr__ string
            -> #str containing __repr__ output
        """
        _bold = bold
        if not self.pretty:
            _bold = lambda x: x
        # Attach memory address and return
        _attrs = self._format_attrs()
        self.data = "<{}.{}({}){}>{}".format(
            self.obj.__module__ if hasattr(self.obj, "__module__") \
                else "__main__",
            _bold(self.obj.__class__.__name__),
            _attrs,
            ":{}".format(hex(id(self.obj))) if self.address else "",
            _break+self.supplemental if self.supplemental else "")
        return stdout_encode(self.data)


class RandData(object):
    """ ..
            from redis_structures.debug import RandData

            rd = RandData(str)

            rd.list(10)
            # -> [
            #   'nmeFFu', '4Ouonu5', 'HEb6OaujYL', 'C2KaV', 'CfYioZy',
            #   'i5PKqZ', 'nA', 'Upzyt', 'Wc', '252V']

            #: Changes the values to <int>
            rd.datatype = int

            rd.dict(10)
            # -> {
            #   'Lnhy6tcwY': 16440106327475681, 'fvKgj': 94196830283393128,
            #   'JP8l8': 78674425573407922, 'Gd22cjsKL': 58888721526521112,
            #   'H8dNss': 5741955182682407, 'WVs': 18667502416672836,
            #   'epW': 34582433811443162, 'AE': 70332483677259590,
            #   'Amfh81vB': 69006761006741551, 's1afta8tCg': 95049217390404053
            # }

            #: Generates random data for all sequence-like structures
            rd.sequence(list, 10)
            # -> [
            #    11012231953494111, 16269794115998776, 65722985758809749,
            #    77868898572532507, 98520928111804919, 80994560862734842,
            #    13185719941276731, 85143540729944251, 20857604948101100,
            #    71388371195677723]

            #: Generates random data for all mapping-like structures
            rd.mapping(dict, 10)
            # -> {
            #    '8CH8G5': 85696434945877667, '3WF': 45209983369688209,
            #    'YXdniVzf7v': 77685036519618428, 'ke2MPk': 14167846091729017,
            #    'sT3A': 76501719321948408, 'zaK9YYsup2': 70344281084943701,
            #    'YAz0': 35778426682427301, 'zd5oj': 95145008229111099,
            #    '0x20mL6': 57137525121733914, '2dzvKZQf': 71981907451087745
            # }
        ..
    """
    __slots__ = (
        'datatype', 'keyspace', 'str_keyspace', 'digits_keyspace',
        'random', 'tlds', 'typemap')
    randomType = "random"
    urlType = "url"
    generatorType = "generator"
    emailType = "email"
    hashType = "hash"

    def __init__(self, datatype=int, use=False):
        """ Fills data structures with random data

            @datatype: #builtin to use as the values for the random data.
                Supported types are in :prop:typemap
            @use: random module, :mod:numpy.random used by default
        """
        self.datatype = datatype
        self.keyspace = string.ascii_letters+string.digits
        self.str_keyspace = string.ascii_letters
        self.digits_keyspace = string.digits
        self.random = use or random
        self.tlds = []
        self.typemap = {
          int: lambda: self.randint,
          float: lambda: self.randfloat,
          list: lambda: self.randlist,
          dict: lambda: self.randdict,
          tuple: lambda: self.randtuple,
          set: lambda: self.randset,
          str: lambda: self.randstr,
          deque: lambda: self.randdeque,
          self.generatorType: lambda: self.randgenerator,
          self.urlType: lambda: self.randurl,
          self.emailType: lambda: self.randemail,
          self.hashType: lambda: self.randhash,
        }

    @prepr('random', 'datatype', _doc=True)
    def __repr__(self): return

    @property
    def randstr(self):
        """ -> #str result of :func:gen_rand_str """
        return gen_rand_str(
            2, 10, use=self.random, keyspace=list(self.keyspace))

    @property
    def randdomain(self):
        """ -> a randomized domain-like name """
        return '.'.join(
            rand_readable(3, 6, use=self.random, density=3)
            for _ in range(self.random.randint(1, 2))
        ).lower()

    @property
    def randpath(self):
        """ -> a random URI-like #str path """
        return '/'.join(
            gen_rand_str(3, 10, use=self.random, keyspace=list(self.keyspace))
            for _ in range(self.random.randint(0, 3)))

    @property
    def randtld(self):
        """ -> a random #str tld via :mod:tlds """
        self.tlds = tuple(tlds.tlds) if not self.tlds else self.tlds
        return self.random.choice(self.tlds)

    @property
    def randurl(self):
        """ -> a random url-like #str via :prop:randdomain, :prop:randtld,
                and :prop:randpath
        """
        return "{}://{}.{}/{}".format(
            self.random.choice(("http", "https")),
            self.randdomain, self.randtld, self.randpath)

    @property
    def randemail(self):
        """ -> a random email address-like #str via :prop:randdomain and
                :prop:randtld
        """
        return "{}@{}.{}".format(
            self.randdomain, self.randdomain, self.randtld)

    @property
    def randint(self):
        """ -> a random #int """
        return self.random.randint(1, 99999999999999999)

    @property
    def randfloat(self):
        """ -> a random #float """
        return self.random.random()

    @property
    def randlist(self):
        """ -> a #list of random #int """
        return [
            self.randint
            for x in range(0, self.random.randint(3, 10))]

    @property
    def randgenerator(self):
        """ -> a #generator of random #int """
        return (
            self.randint
            for x in range(0, self.random.randint(3, 10)))

    @property
    def randtuple(self):
        """ -> a #tuple of random #int """
        return tuple(
            self.randint
            for x in range(0, self.random.randint(3, 10)))

    @property
    def randdeque(self):
        """ -> a :class:collections.deque of random #int """
        return deque(
            self.randint
            for x in range(0, self.random.randint(3, 10)))

    @property
    def randdict(self):
        """ -> a #dict of |{random_string: random_int}| """
        return {
            self.randstr: self._map_type(int)
            for x in range(self.random.randint(3, 10))}

    @property
    def randset(self):
        """ -> a #set of random integers """
        return {
            self._map_type(int)
            for x in range(self.random.randint(3, 10))}

    @property
    def randhash(self):
        """ -> a random #hash using :func:os.urandom """
        _hash = os.urandom(24)
        return getencoder("hex")(_hash)[0]

    def _to_tuple(self, _list):
        """ Recursively converts lists to tuples """
        result = list()
        for l in _list:
            if isinstance(l, list):
                result.append(tuple(self._to_tuple(l)))
            else:
                result.append(l)
        return tuple(result)

    def _map_type(self, _type=None):
        _type = _type or self.datatype
        if _type == self.randomType:
            _type = random.choice(list(self.typemap.keys()))
        return self.typemap.get(_type, lambda: self.randint)()

    def dict(self, key_depth=1000, tree_depth=1):
        """ Creates a random #dict

            @key_depth: #int number of keys per @tree_depth to generate random
                values for
            @tree_depth: #int dict tree dimensions size, i.e.
                1=|{key: value}|
                2=|{key: {key: value}, key2: {key2: value2}}|

            -> random #dict
        """
        if not tree_depth:
            return self._map_type()
        return {
            self.randstr: self.dict(key_depth, tree_depth-1)
            for x in range(key_depth)}

    def defaultdict(self, key_depth=1000, tree_depth=1):
        """ Creates a random :class:collections.defaultdict

            @key_depth: #int number of keys per @tree_depth to generate random
                values for
            @tree_depth: #int dict tree dimensions size, i.e.
                1=|{key: value}|
                2=|{key: {key: value}, key2: {key2: value2}}|

            -> random :class:collections.defaultdict
        """
        if not tree_depth: return self._map_type()
        _dict = defaultdict()
        _dict.update({
            self.randstr: self.defaultdict(key_depth, tree_depth-1)
            for x in range(key_depth)})
        return _dict

    def tuple(self, size=1000, tree_depth=1):
        """ Creates a random #tuple

            @size: #int number of random values to include in each @tree_depth
            @tree_depth: #int dict tree dimensions size, i.e.
                1=|(value1, value2)|
                2=|((value1, value2), (value1, value2))|

            -> random #tuple
        """
        if not tree_depth: return self._map_type()
        return tuple(self.tuple(size, tree_depth-1) for x in range(size))

    def set(self, size=1000):
        """ Creates a random #set

            @size: #int number of random values to include in the set

            -> random #set
        """
        get_val = lambda: self._map_type()
        return set(get_val() for x in range(size))

    def list(self, size=1000, tree_depth=1):
        """ Creates a random #list

            @size: #int number of random values to include in each @tree_depth
            @tree_depth: #int dict tree dimensions size, i.e.
                1=|[value1, value2]|
                2=|[[value1, value2], [value1, value2]]|

            -> random #list
        """
        if not tree_depth: return self._map_type()
        return list(self.deque(size, tree_depth-1) for x in range(size))

    def deque(self, size=1000, tree_depth=1):
        """ Creates a random :class:collections.deque

            @size: #int number of random values to include in each @tree_depth
            @tree_depth: #int dict tree dimensions size, i.e.
                1=|deque([value1, value2])|
                2=|deque([[value1, value2], [value1, value2]])|

            -> random :class:collections.deque
        """
        if not tree_depth: return self._map_type()
        return deque([self.deque(size, tree_depth-1) for x in range(size)])

    def generator(self, size=1000, tree_depth=1):
        """ Creates a random #generator

            @size: #int number of random values to include in each @tree_depth
            @tree_depth: #int dict tree dimensions size, i.e.
                1=|(value1, value2)|
                2=|((value1, value2), (value1, value2))|

            -> random :class:collections.deque
        """
        if not tree_depth: return self._map_type()
        return (self.generator(size, tree_depth-1) for x in range(size))

    def sequence(self, struct, size=1000, tree_depth=1, append_callable=None):
        """ Generates random values for sequence-like objects

            @struct: the sequence-like structure you want to fill with random
                data
            @size: #int number of random values to include in each @tree_depth
            @tree_depth: #int dict tree dimensions size, i.e.
                1=|(value1, value2)|
                2=|((value1, value2), (value1, value2))|
            @append_callable: #callable method which appends/adds data to your
                sequence-like structure - e.g. :meth:list.append

            -> random @struct
            ..
                from collections import UserList
                from redis_structures.debug import RandData

                class MySequence(UserList):
                    pass

                rd = RandData(int)

                my_seq = MySequence()
                rd.sequence(my_seq, 3, 1, my_seq.append)
                # -> [88508293836062443, 49097807561770961, 55043550817099444]
            ..
        """
        if not tree_depth:
            return self._map_type()
        _struct = struct()
        add_struct = _struct.append if not append_callable \
            else getattr(_struct, append_callable)
        for x in range(size):
            add_struct(self.sequence(
                struct, size, tree_depth-1, append_callable))
        return _struct

    def mapping(self, struct, key_depth=1000, tree_depth=1,
                update_callable=None):
        """ Generates random values for dict-like objects

            @struct: the dict-like structure you want to fill with random data
            @size: #int number of random values to include in each @tree_depth
            @tree_depth: #int dict tree dimensions size, i.e.
                1=|{key: value}|
                2=|{key: {key: value}, key2: {key2: value2}}|
            @update_callable: #callable method which updates data in your
                dict-like structure - e.g. :meth:builtins.dict.update

            -> random @struct
            ..
                from collections import UserDict
                from redis_structures.debug import RandData

                class MyDict(UserDict):
                    pass

                rd = RandData(int)

                my_dict = MyDict()
                rd.dict(my_dict, 3, 1, my_dict.update)
                # -> {
                #   'SE0ZNy0F6O': 42078648993195761,
                #   'pbK': 70822820981335987,
                #   '0A5Aa7': 17503122029338459}
            ..
        """
        if not tree_depth:
            return self._map_type()
        _struct = struct()
        add_struct = _struct.update if not update_callable \
            else getattr(_struct, update_callable)
        for x in range(key_depth):
            add_struct({
                self.randstr: self.mapping(
                    struct, key_depth, tree_depth-1, update_callable)
            })
        return _struct


class Look(object):
    """ ..
            from redis_structures.debug import Look

            _dict = RandData(RandData.hashType).dict(3, 1)
            look = Look(_dict)
            look()
            '''
            qpqF8mrY: b'45670c323f72d67b49663c300c58249649fe0ed91495f1ca'
                  QN: b'047a9b1a27e4ac824091667c18cf5f75d4f0919d376bd41a'
             YLHoDKt: b'405dbbbcff75adde2b2d8a9bec13eaa8dc83bda2615ae70b'
            '''

            look = Look(["for", "the", "love", "of", ("the", "game")])
            look()
            '''
            0] for
            1] the
            2] love
            3] of
            4] 0) the
               1) game
            '''

            look(set(("penguin",)))
            # -> 1… penguin
        ..
    """
    __slots__ = ('obj', '_depth', '_justify', '_key_maxlen', '_dicts')
    str_ = (str, UserString)
    dict_ = (dict, defaultdict, OrderedDict, UserDict, Counter)
    list_ = (list, UserList)
    set_ = (set, frozenset)
    numeric_ = (int, float, complex)

    def __init__(self, obj=None):
        """ Formats/prettifies your data structures

            @obj: the object you wish to prettify
        """
        self.obj = obj
        self._depth = 0
        self._justify = 0
        self._key_maxlen = get_terminal_width()//2
        self._dicts = {}

    @prepr('_key_maxlen', _doc=True)
    def __repr__(self): return

    def __call__(self, obj=None):
        self.pretty_print(obj or self.obj)

    def _dict_prefix(self, key, value, i, dj=0, color=None, separator=":"):
        just = self._justify if i > 0 else dj
        key = cut(str(key), self._key_maxlen).rjust(just)
        key = colorize(key, color=color)
        pref = "{}{} {}".format(key, separator, value)
        """pref = "{}{} {}".format(colorize(str(key)[:self._key_maxlen]\
            .rjust(just), color=color), separator, value)"""
        return pref

    def _numeric_prefix(self, i, item, just=0, color=None, separator="]"):
        just = self._justify if i > 0 or self._depth == 1 else just
        return "{}{} {}".format(
            str(i).rjust(just),
            colorize(separator, color=color),
            item)

    def _prefix(self, i, item, just=0, color=None, separator="-"):
        just = self._justify if i > 0 else just
        return " {} {}".format(
            colorize(str(separator).rjust(just), color=color),
            item)

    def _incr_just_size(self, size):
        self._depth += 1
        self._justify += size

    def _decr_just_size(self, size):
        self._depth -= 1
        self._justify -= size

    def _format_numeric_sequence(self, _sequence, separator="."):
        """ Length of the highest index in chars = justification size """
        if not _sequence:
            return colorize(_sequence, "purple")
        _sequence = _sequence if _sequence is not None else self.obj
        minus = (2 if self._depth > 0 else 0)
        just_size = len(str(len(_sequence)))
        out = []
        add_out = out.append
        for i, item in enumerate(_sequence):
            self._incr_just_size(just_size+minus)
            add_out(self._numeric_prefix(
                i, self.pretty(item), just=just_size, color="blue",
                separator=separator))
            self._decr_just_size(just_size+minus)
        if not self._depth:
            return padd("\n".join(out) if out else str(out), padding="top")
        else:
            return "\n".join(out) if out else str(out)

    def _format_other_sequence(self, _sequence, separator="&"):
        """ Length of the separator = justification size """
        if not _sequence:
            return colorize(_sequence, "purple")
        minus = (2 if self._depth > 0 else 0)
        just_size = len(separator)
        _sequence = _sequence if _sequence is not None else self.obj
        out = []
        add_out = out.append
        for i, item in enumerate(_sequence):
            self._incr_just_size(just_size+minus)
            add_out(self._prefix(
                i, self.pretty(item), just=just_size, color="blue",
                separator=separator))
            self._decr_just_size(just_size + minus)
        if not self._depth:
            return padd("\n".join(out) if out else str(out), padding="top")
        else:
            return "\n".join(out) if out else str(out)

    def _recursion_sucks_sometimes(self, _dict):
        _dict_id = id(_dict)
        if _dict_id in self._dicts and self._dicts[_dict_id] < self._depth:
            """ Prevent perpetual recursion """
            return self.object(_dict)
        else:
            self._dicts[_dict_id] = self._depth
            return None

    def dict(self, _dict=None):
        #: (dict, defaultdict, OrderedDict, UserDict)
        _dict = _dict if _dict is not None else self.obj
        if not _dict:
            return colorize(_dict, "purple")
        stop = self._recursion_sucks_sometimes(_dict)
        if stop:
            return stop
        minus = (2 if self._depth > 0 else 0)
        just_size = max(len(uncolorize(str(k))) for k in _dict.keys())+minus
        just_size = just_size if just_size <= self._key_maxlen \
            else self._key_maxlen
        out = []
        add_out = out.append
        for i, (k, item) in enumerate(_dict.items()):
            self._incr_just_size(just_size)
            add_out(self._dict_prefix(
                k, self.pretty(item), i, dj=(just_size-minus), color="bold"))
            self._decr_just_size(just_size)
        if not self._depth:
            return padd("\n".join(out) if out else str(out), padding="top")
        else:
            return "\n".join(out) if out else str(out)

    def list(self, _list=None):
        #: (list, UserList)
        return self._format_numeric_sequence(_list, separator="]")

    def tuple(self, _tuple=None):
        #: (tuple)
        return self._format_numeric_sequence(_tuple, separator=")")

    def deque(self, _deque=None):
        #: (deque)
        return self._format_numeric_sequence(_deque, separator="|")

    def generator(self, _generator=None):
        #: (generator)
        return self._format_other_sequence(_generator, separator="*")

    def set(self, _set=None):
        #: (set, frozenset)
        return self._format_other_sequence(_set, separator="…")

    def sequence(self, _sequence=None):
        #: (set, frozenset)
        return self._format_numeric_sequence(_sequence, separator=".")

    def object(self, _obj=None):
        #: anything else
        _obj = str(_obj) + " "
        return _obj

    def bytes(self, _bytes=None):
        return colorize(str(_bytes) + " ", "purple")

    def number(self, _number=None):
        return colorize(str(_number) + " ", "purple")

    def objname(self, obj=None):
        """ Formats object names in a pretty fashion """
        obj = obj or self.obj
        _objname = self.pretty_objname(obj, color=None)
        _objname = "'{}'".format(colorize(_objname, "blue"))
        return _objname

    def pretty_print(self, obj=None):
        """ Formats and prints @obj or :prop:obj

            @obj: the object you'd like to prettify
        """
        print(self.pretty(obj if obj is not None else self.obj))

    def pretty(self, obj=None):
        """ Formats @obj or :prop:obj

            @obj: the object you'd like to prettify

            -> #str pretty object
        """
        return self._format_obj(obj if obj is not None else self.obj)

    def _format_obj(self, item=None):
        """ Determines the type of the object and maps it to the correct
            formatter
        """
        # Order here matters, odd behavior with tuples
        if item is None:
            return getattr(self, 'number')(item)
        elif isinstance(item, self.str_):
            #: String
            return item + " "
        elif isinstance(item, bytes):
            #: Bytes
            return getattr(self, 'bytes')(item)
        elif isinstance(item, self.numeric_):
            #: Float, int, etc.
            return getattr(self, 'number')(item)
        elif isinstance(item, self.dict_):
            #: Dict
            return getattr(self, 'dict')(item)
        elif isinstance(item, self.list_):
            #: List
            return getattr(self, 'list')(item)
        elif isinstance(item, tuple):
            #: Tuple
            return getattr(self, 'tuple')(item)
        elif isinstance(item, types.GeneratorType):
            #: Generator
            return getattr(self, 'generator')(item)
        elif isinstance(item, self.set_):
            #: Set
            return getattr(self, 'set')(item)
        elif isinstance(item, deque):
            #: Deque
            return getattr(self, 'deque')(item)
        elif isinstance(item, Sequence):
            #: Sequence
            return getattr(self, 'sequence')(item)
        #: Any other object
        return getattr(self, 'object')(item)

    @classmethod
    def pretty_objname(self, obj=None, maxlen=50, color="boldcyan"):
        """ Pretty prints object name

            @obj: the object whose name you want to pretty print
            @maxlen: #int maximum length of an object name to print
            @color: your choice of :mod:colors or |None|

            -> #str pretty object name
            ..
                from redis_structures.debug import Look
                print(Look.pretty_objname(dict))
                # -> 'dict\x1b[1;36m<builtins>\x1b[1;m'
            ..
        """
        parent_name = lambda_sub("", get_parent_name(obj) or "")
        objname = get_obj_name(obj)
        if color:
            objname += colorize("<{}>".format(parent_name), color, close=False)
        else:
            objname += "<{}>".format(parent_name)
        objname = objname if len(objname) < maxlen else \
            objname[:(maxlen-1)]+"…>"
        if color:
            objname += colors.RESET
        return objname


class Logg(object):
    """ ..
            from redis_structures.debug import logg

            logg.warning()
            # (Warning)

            logg.notice("Hello world")
            # (Hello world)

            logg("world").warning("Hello")
            # (Hello) world

            logg([780, 779, 778, 777]).success("Found IDs")
            # (Found IDs)
            # 0] 780
            # 1] 779
            # 2] 778
            # 3] 777

            logg("15 wasn't an", int, 12, 13, 14, "15").error()
            # (TypeError) '15 wasn't an integer' 12 13 14 '15'

            #: Changes the loglevel to 'notice'
            logg.set_level("n")

            logg({"hello": "world"}).error()
            # (Error)
            # hello: world

            logg.notice("Hello world")
            # (Hello world)

            logg.log("Hello world")
            #
        ..
    """
    __slots__ = ('message', 'levelmap', 'loglevel', 'pretty', 'include_time')
    SUCCESS = 0
    ERROR = 1
    WARNING = 2
    NOTICE = 3
    LOG = 4
    TIMING = 5
    COUNT = 6
    COMPLETE = 7
    levels = {
        # Verbose, print all
        'v': {SUCCESS, WARNING, NOTICE, LOG, TIMING, COUNT, ERROR, COMPLETE},
        # Print all log, notice, warning, timing, count and error types
        'l': {LOG, NOTICE, WARNING, ERROR, TIMING, COUNT},
        # Print all notices, warnings and errors
        'n': {NOTICE, WARNING, ERROR},
        # Print all warnings and errors
        'w': {WARNING, ERROR},
        # Diagnotics, print timing/count
        'd': {TIMING, COUNT},
        # Print all errors
        'e': {ERROR},
        # Print all successes
        's': {SUCCESS, COMPLETE},
        # Print all timings
        't': {TIMING},
        # Print all counts
        'c': {COUNT},
    }

    def __init__(self, *messages, loglevel=None, include_time=False,
                 pretty=True):
        """ A logger that also pretty prints

            @messages: you can pass any python object as an argument here
            @loglevel: #str or iterable combination of any of :attr:levels keys
            @include_time: #bool whether or not to include the current time in
                the log message
            @pretty: #bool whether or not to format @messages with :class:Look

            ``Log levels``
            - |v| Verbose, prints all messages
            - |l| Log, prints all log, notice, warning, error, timing and
                    count type messages
            - |n| Notice, prints all notice, warning, and error type messages
            - |w| Warning, prints all warning and error type messages
            - |d| Diagnostic, prints all timing and count type messages
            - |e| Error, prints all error type messages
            - |s| Success, prints all success and complete type messages
            - |t| Timing, prints all timing type messages
            - |c| Count, prints all count type messages

            These can be used together, a loglevel of "ts" for example
            would allow for both timing and success type messages.

            You may add your own level spec with :meth:add_level
        """
        self.message = list(messages)
        self.levelmap = {}
        self.loglevel = self.set_level(loglevel or "v")
        self.pretty = pretty
        self.include_time = include_time

    @prepr('loglevel', _doc=True)
    def __repr__(self): return

    def __call__(self, *messages, loglevel=None, include_time=None,
                 pretty=None):
        """ :see::meth:Logg.__init__

            -> self
        """
        self.message = list(messages)
        if pretty is not None:
            self.pretty = pretty
        if include_time is not None:
            self.include_time = include_time
        if loglevel:
            self.loglevel = self.set_level(loglevel)
        return self

    def add(self, *messages):
        """ Adds a message or messages to the log messages (:attr:message)
            stack
            @messages: log messages

            -> self
        """
        self.message.extend(messages)
        return self

    def add_level(self, name, *allowed_types):
        """ Adds a custom loglevel to :attr:levels

            @name: #str single-char name of the loglevel
            @allowed_types: #int one or more types,
                e.g. :attr:redis_structures.debug.Logg.SUCCESS
        """
        self.levels[name] = set(allowed_types)

    def set_level(self, level):
        """ Sets :attr:loglevel to @level

            @level: #str one or several :attr:levels
        """
        if not level:
            return None
        self.levelmap = set()
        for char in level:
            self.levelmap = self.levelmap.union(self.levels[char])
        self.loglevel = level
        return self.loglevel

    def should_log(self, type):
        """ Decides whether or not something should be logged
            @type: #int log type

            -> #bool True if @type is in :prop:levelmap
        """
        return type in self.levelmap

    def log(self, flag_message=None, padding=None, color=None, force=False):
        """ Log Level: :attr:LOG

            @flag_message: #str flags the message with the given text
                using :func:flag
            @padding: #str 'top', 'bottom' or 'all', adds a new line to the
                specified area with :func:padd
            @color: #str colorizes @flag_message using :func:colorize
            @force: #bool whether or not to force the message to log in spite
                of the assigned log level

            ..
                from redis_structures.debug import Logg
                logg = Logg(loglevel="v")

                logg("World").log("Hello")
                # (Hello) World

                logg("Hello world").log()
                # Hello world
            ..
        """
        if self.should_log(self.LOG) or force:
            self._print_message(
                flag_message=flag_message, color=color, padding=padding)

    def success(self, flag_message="Success", padding=None, force=False):
        """ Log Level: :attr:SUCCESS

            @flag_message: #str flags the message with the given text
                using :func:flag
            @padding: #str 'top', 'bottom' or 'all', adds a new line to the
                specified area with :func:padd
            @color: #str colorizes @flag_message using :func:colorize
            @force: #bool whether or not to force the message to log in spite
                of the assigned log level

            ..
                from redis_structures.debug import Logg
                logg = Logg(loglevel="v")

                logg("World").success("Hello")
                # (Hello) World

                logg("Hello world").success()
                # (Success) Hello world
            ..
        """
        if self.should_log(self.SUCCESS) or force:
            self._print_message(
                flag_message=flag_message, color=colors.success_color,
                padding=padding)

    def complete(self, flag_message="Complete", padding=None, force=False):
        """ Log Level: :attr:COMPLETE

            @flag_message: #str flags the message with the given text
                using :func:flag
            @padding: #str 'top', 'bottom' or 'all', adds a new line to the
                specified area with :func:padd
            @color: #str colorizes @flag_message using :func:colorize
            @force: #bool whether or not to force the message to log in spite
                of the assigned log level

            ..
                from redis_structures.debug import Logg
                logg = Logg(loglevel="v")

                logg("World").complete("Hello")
                # (Hello) World

                logg("Hello world").complete()
                # (Complete) Hello world
            ..
        """
        if self.should_log(self.COMPLETE) or force:
            self._print_message(
                flag_message=flag_message, color=colors.complete_color,
                padding=padding)

    def notice(self, flag_message="Notice", padding=None, force=False):
        """ Log Level: :attr:NOTICE

            @flag_message: #str flags the message with the given text
                using :func:flag
            @padding: #str 'top', 'bottom' or 'all', adds a new line to the
                specified area with :func:padd
            @color: #str colorizes @flag_message using :func:colorize
            @force: #bool whether or not to force the message to log in spite
                of the assigned log level

            ..
                from redis_structures.debug import Logg
                logg = Logg(loglevel="v")

                logg("World").notice("Hello")
                # (Hello) World

                logg("Hello world").notice()
                # (Notice) Hello world
            ..
        """
        if self.should_log(self.NOTICE) or force:
            self._print_message(
                flag_message=flag_message, color=colors.notice_color,
                padding=padding)

    def warning(self, flag_message="Warning", padding=None, force=False):
        """ Log Level: :attr:WARNING

            @flag_message: #str flags the message with the given text
                using :func:flag
            @padding: #str 'top', 'bottom' or 'all', adds a new line to the
                specified area with :func:padd
            @color: #str colorizes @flag_message using :func:colorize
            @force: #bool whether or not to force the message to log in spite
                of the assigned log level

            ..
                from redis_structures.debug import Logg
                logg = Logg(loglevel="v")

                logg("World").warning("Hello")
                # (Hello) World

                logg("Hello world").warning()
                # (Warning) Hello world
            ..
        """
        if self.should_log(self.WARNING) or force:
            self._print_message(
                flag_message=flag_message, color=colors.warning_color,
                padding=padding)

    def error(self, flag_message="Error", padding=None, force=False):
        """ Log Level: :attr:ERROR

            @flag_message: #str flags the message with the given text
                using :func:flag
            @padding: #str 'top', 'bottom' or 'all', adds a new line to the
                specified area with :func:padd
            @color: #str colorizes @flag_message using :func:colorize
            @force: #bool whether or not to force the message to log in spite
                of the assigned log level

            ..
                from redis_structures.debug import Logg
                logg = Logg(loglevel="v")

                logg("World").error("Hello")
                # (Hello) World

                logg("Hello world").error()
                # (Error) Hello world
            ..
        """
        if self.should_log(self.ERROR) or force:
            self._print_message(
                flag_message=flag_message, color=colors.error_color,
                padding=padding)

    def timing(self, flag_message, padding=None, force=False):
        """ Log Level: :attr:TIMING

            @flag_message: time-like #float
            @padding: #str 'top', 'bottom' or 'all', adds a new line to the
                specified area with :func:padd
            @force: #bool whether or not to force the message to log in spite
                of the assigned log level

            ..
                from redis_structures.debug import Logg
                logg = Logg(loglevel="v")

                logg("Finished in").timing(0.908)
                # Finished in (908.0ms)

                logg().timing(0.908)
                # (908.0ms)
            ..
        """
        if self.should_log(self.TIMING) or force:
            self._print_message(
                flag_message=Timer.format_time(flag_message), padding=padding,
                reverse=True, color=colors.timing_color)

    def count(self, flag_message, padding=None, force=False):
        """ Log Level: :attr:COUNT

            @flag_message: time-like #float
            @padding: #str 'top', 'bottom' or 'all', adds a new line to the
                specified area with :func:padd
            @force: #bool whether or not to force the message to log in spite
                of the assigned log level

            ..
                from redis_structures.debug import Logg
                logg = Logg(loglevel="v")

                logg("Total apps").count(3)
                # Total apps (3)

                logg().count([0, 1, 2, 3])
                # (4)
            ..
        """
        if self.should_log(self.COUNT) or force:
            flag_message = flag_message \
                if isinstance(flag_message, (int, float)) else \
                str(len(flag_message))
            self._print_message(
                flag_message=flag_message, padding=padding, reverse=True,
                color=colors.timing_color)

    #: Formatting
    def format_message(self, message):
        """ Formats a message with :class:Look """
        look = Look(message)
        return look.pretty()

    def format_messages(self, messages):
        """ Formats several messages with :class:Look, encodes them
            with :func:redis_structures.tools.encoding.stdout_encode """
        mess = ""
        for message in self.message:
            if self.pretty:
                mess = "{}{}".format(mess, self.format_message(message))
            else:
                mess += str(message)
        if self.include_time:
            return ": {} : {}".format(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), mess)
        return stdout_encode(mess)

    #: Message printing
    def _print_message(self, flag_message=None, color=None, padding=None,
                       reverse=False):
        """ Outputs the message to the terminal """
        if flag_message:
            flag_message = stdout_encode(flag(
                flag_message, color=color, show=False))
            if not reverse:
                print(
                    padd(flag_message, padding),
                    self.format_messages(self.message))
            else:
                print(
                    self.format_messages(self.message),
                    padd(flag_message, padding))
        else:
            print(self.format_messages(self.message))
        self.message = []


logg = Logg()


class ProgressBar(object):
    """ ..
            from redis_structures.debug import ProgressBar

            progress = ProgressBar()
            for x in progress(['hello', 0, 1]):
                print(x)
                progress.update()
            # 'hello'
            # 0
            # 1
            # Loading =‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒↦       ☉ (80%)

            for x in progress(500):
                p = ProgressBar(progress)
                for y in p(500):
                    p.update()
                progress.update()
            # Loading [405/5000] =‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒↦         ☉ (71%)
            # Loading [405/5000] =                                ↦ӿ (100%)
        ..
    """
    __slots__ = (
        'size', 'progress', 'terminal_width',
        '_barsize', 'parent_bar', 'visible', '_mod')

    def __init__(self, parent_bar=None, visible=True):
        """ |Loading [405/5000] =‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒↦         ☉ (71%)|
            A fun looking, performant progress bar for monitoring the progress
            of loops and tasks

            @parent_bar: another :class:ProgressBar which this progress bar
                is a child of
            @barsize: #int
            @visible: #bool whether or not to print the progress bar to the
                terminal
        """
        self.size = 0
        self._mod = 6
        self.progress = 0
        self._barsize = 33
        self.visible = visible
        self.parent_bar = parent_bar

    @prepr('parent_bar', 'formatter', _doc=True)
    def __repr__(self): return

    def __call__(self, size):
        """ @size: #int or iterable object with __len__ property

            -> #iter if @size is iterable or #range if @size is an #int
        """
        if isinstance(size, (int, float, complex)):
            self.size = size
            self._mod = floor(self.size*0.025) if size > 500 else 2
            return range(size)
        else:
            self.size = len(size)
            self._mod = floor(self.size*0.025) if self.size > 500 else 2
            return iter(size)

    def format_parent_bar(self):
        """ Formats the parent progress bar """
        return " [{}/{}]".format(
            self.parent_bar.progress+1,
            self.parent_bar.size)

    def format_bar(self):
        """ Builds the progress bar """
        pct = floor(round(self.progress/self.size, 2)*100)
        pr = floor(pct*.33)
        bar = "".join(
            ["‒" for x in range(pr)] + ["↦"] +
            [" " for o in range(self._barsize-pr-1)])
        subprogress = self.format_parent_bar() if self.parent_bar else ""
        message = "Loading{} ={}{} ({}%)".format(subprogress, bar, "☉", pct)
        return message.ljust(len(message)+5)

    def finish(self):
        """ Resets the progress bar and clears it from the terminal """
        pct = floor(round(self.progress/self.size, 2)*100)
        pr = floor(pct*.33)
        bar = "".join([" " for x in range(pr-1)] + ["↦"])
        subprogress = self.format_parent_bar() if self.parent_bar else ""
        fin = "Loading{} ={}{} ({}%)".format(subprogress, bar, "ӿ", pct)
        print(fin.ljust(len(fin)+5), end="\r")
        time.sleep(0.10)
        print("\033[K\033[1A")
        self.progress = 0

    def update(self, progress=0):
        """ Updates the progress bar with @progress if given, otherwise
            increments :prop:progress by 1. Also prints the progress bar.

            @progress: #int to assign to :prop:progress
        """
        self.progress += (progress or 1)
        if self.visible:
            if self.progress % self._mod == 1 or (self.progress == self.size-1):
                print(self.format_bar(), end="\r")
            if self.progress == (self.size):
                self.finish()


class NullIO(StringIO):
    def write(self, txt): pass


class Timer(object):
    """ ..
            from redis_structures.debug import Timer, RandData
            import json

            t1 = Timer()
            t1.start()

            # Generates a random dictionary with str values
            rd = RandData(str).dict(10, 2)

            # Passes rd to test_dumps inside Timer
            t2 = Timer(json.dumps, rd)
            t2.time(100)
            '''
                (dumps<json>)
                Intervals: 100
                     Mean: 80.48µs
                      Min: 72.0µs
                   Median: 79.0µs
                      Max: 187.0µs
                 St. Dev.: 12.75µs
                    Total: 8.05ms
            '''

            # Passes keyword arg sort_keys to json_dumps
            t2.time(100, sort_keys=True)
            '''
                (dumps<json>)
                Intervals: 100
                     Mean: 121.96µs
                      Min: 110.0µs
                   Median: 117.0µs
                      Max: 331.0µs
                 St. Dev.: 24.44µs
                    Total: 12.2ms
            '''

            print("Script execution time:", t1.stop())
            # Script execution time: 354.5ms
        ..
    """
    __slots__ = (
        '_start', '_callableargs', '_first_start', '_stop', 'intervals',
        '_callable', '_array', '_array_len', 'precision', 'progress',
        '_intervals_len', 'allocated_memory')

    def __init__(self, callable=None, *args, _precision=8, _start=0.0,
                 _parent_progressbar=None, **kwargs):
        """ A memory-efficient, performant and accurate timer for analyzing the
            performance of your python structures and scripts. Timer utilizes
            time.perf_counter() for the most accurate reading of time available
            within python scripts.

            @callable: the object you wish to time
            @*args: arguments you wish to pass to @callable
            @**kwargs: keyword arguments you wish to past to @callable
            @_precision: #int number of decimal places to round execution
                time to
            @_start: #float optional start time in time since epoch
            @_parent_progressbar: optional parent :class:ProgressBar
        """
        self._start = _start
        self._first_start = _start
        self._stop = time.perf_counter()
        self._callable = callable
        self._callableargs = (args, kwargs)
        self._array = None
        self._array_len = 0
        self.intervals = []
        self._intervals_len = 0
        self.precision = _precision
        self.progress = ProgressBar(parent_bar=_parent_progressbar)

    @prepr('precision', _doc=True)
    def __repr__(self): return

    @property
    def array(self):
        """ Returns :prop:intervals as a numpy array, caches

            -> :class:numpy.array
        """
        if self._intervals_len:
            if self._array_len != self._intervals_len:
                if not self._array_len:
                    self._array = np.array(self.intervals) \
                        if hasattr(np, 'array') else self.intervals
                else:
                    self._array = np.concatenate((
                        self._array, self.intervals), axis=0) \
                        if hasattr(np, 'concatenate') else \
                        (self._array + self.intervals)
                self._array_len += len(self.intervals)
                self.intervals = []
            return self._array
        return []

    def start(self):
        """ Starts the timer """
        if not self._start:
            self._first_start = time.perf_counter()
            self._start = self._first_start
        else:
            self._start = time.perf_counter()

    def stop(self, precision=0):
        """ Stops the timer, adds it as an interval to :prop:intervals
            @precision: #int number of decimal places to round to

            -> #str formatted interval time
        """
        self._stop = time.perf_counter()
        return self.add_interval(precision)

    @classmethod
    def format_time(self, sec):
        """ Pretty-formats a given time in a readable manner
            @sec: #int or #float seconds

            -> #str formatted time
        """
        # µsec
        if sec < 0.001:
            return "{}{}".format(
                colorize(round(sec*1000000, 2), "purple"), bold("µs"))
        # ms
        elif sec < 1.0:
            return "{}{}".format(
                colorize(round(sec*1000, 2), "purple"), bold("ms"))
        # s
        elif sec < 60.0:
            return "{}{}".format(
                colorize(round(sec, 2), "purple"), bold("s"))
        else:
            floored = floor(sec/60)
            return "{}{} {}{}".format(
                colorize(floored, "purple"),
                bold("m"),
                colorize(floor(sec-(floored*60)), "purple"),
                bold("s"))

    def format_size(self, bytes):
        """ Pretty-formats given bytes size in a readable manner
            @bytes: #int or #float bytes

            -> #str formatted bytes
        """
        # b
        if bytes < 1024:
            return "{}{}".format(colorize(round(
                bytes, 2), "purple"),
                bold("bytes"))
        # kb
        elif bytes < (1024*1000):
            return "{}{}".format(colorize(round(
                bytes/1024, 2), "purple"),
                bold("kB"))
        # mb
        elif bytes < (1024*1024):
            return "{}{}".format(colorize(round(
                bytes/1024, 2), "purple"),
                bold("MB"))

    def add_interval(self, precision=0):
        """ Adds an interval to :prop:intervals
            -> #str formatted time
        """
        precision = precision or self.precision
        interval = round((self._stop - self._start), precision)
        self.intervals.append(interval)
        self._intervals_len += 1
        self._start = time.perf_counter()
        return self.format_time(interval)

    def time(self, intervals=1, *args, _show_progress=True, _print=True,
             _collect_garbage=False, _quiet=True, **kwargs):
        """ Measures the execution time of :prop:_callable for @intervals

            @intervals: #int number of intervals to measure the execution time
                of the function for
            @*args: arguments to pass to the callable being timed
            @**kwargs: arguments to pass to the callable being timed
            @_show_progress: #bool whether or not to print a progress bar
            @_print: #bool whether or not to print the results of the timing
            @_collect_garbage: #bool whether or not to garbage collect
                while timing
            @_quiet: #bool whether or not to disable the print() function's
                ability to output to terminal during the timing

            -> :class:collections.OrderedDict of stats about the timing
        """
        self.reset()
        args = list(args) + list(self._callableargs[0])
        _kwargs = self._callableargs[1]
        _kwargs.update(kwargs)
        kwargs = _kwargs
        if not _collect_garbage:
            gc.disable()  # Garbage collection setting
        gc.collect()
        self.allocated_memory = 0
        for x in self.progress(intervals):
            if _quiet:  # Quiets print()s in the tested function
                sys.stdout = NullIO()
            try:
                self.start()  # Starts the timer
                self._callable(*args, **kwargs)
                self.stop()  # Stops the timer
            except Exception as e:
                if _quiet:  # Unquiets prints()
                    sys.stdout = sys.__stdout__
                raise e
            if _quiet:  # Unquiets prints()
                sys.stdout = sys.__stdout__
            self.progress.update()  # Updates the progress bar
        if not _collect_garbage:
            gc.enable()  # Garbage collection setting
        return self.info(_print=_print)

    @property
    def mean(self):
        """ -> #float :func:numpy.mean of the timing intervals """
        return np.mean(self.array) if self._array_len else None

    @property
    def median(self):
        """ -> #float :func:numpy.median of the timing intervals """
        return np.median(self.array) if self._array_len else None

    @property
    def max(self):
        """ -> #float :func:numpy.max of the timing intervals """
        return np.max(self.array) if self._array_len else None

    @property
    def min(self):
        """ -> #float :func:numpy.min of the timing intervals """
        return np.min(self.array) if self._array_len else None

    @property
    def stdev(self):
        """ -> #float :func:numpy.std of the timing intervals """
        return np.std(self.array) if self._array_len else None

    @property
    def exectime(self):
        """ -> #float :func:numpy.sum of the timing intervals """
        return round(np.sum(self.array), self.precision)

    @property
    def runtime(self):
        """ -> #float total time between the first start() and now """
        return round(time.perf_counter()-self._first_start, self.precision)

    @property
    def stats(self):
        """ -> :class:collections.OrderedDict of stats about the time intervals
        """
        return OrderedDict([
            ("Intervals", len(self.array)),
            ("Mean", self.format_time(self.mean or 0)),
            ("Min", self.format_time(self.min or 0)),
            ("Median", self.format_time(self.median or 0)),
            ("Max", self.format_time(self.max or 0)),
            ("St. Dev.", self.format_time(self.stdev or 0)),
            ("Total", self.format_time(self.exectime or 0)),
        ])

    def info(self, _print=True):
        if _print:
            logg(self.stats, loglevel="v").complete(
                Look.pretty_objname(self._callable))
        return self.stats

    def reset(self):
        """ Resets the time intervals """
        self._start = 0
        self._first_start = 0
        self._stop = time.perf_counter()
        self._array = None
        self._array_len = 0
        self.intervals = []
        self._intervals_len = 0


class Compare(object):
    """ ..
            from redis_structures.debug import Compare, RandData
            import json
            import ujson

            # Generates a random dictionary with str values
            rd = RandData(str).dict(10, 2)

            c = Compare(ujson.dumps, json.dumps)
            c.time(100, rd)
            '''
            (Results after 100 intervals)
            ‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒
            #1 ¦  55.58µs            'dumps<ujson>'
            #2 ¦  78.28µs    -40.84% 'dumps<json>'
            ‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒
            '''

            c = Compare(ujson.dumps, json.dumps)
            c.time(100, rd, indent=4)
            '''
            (Results after 100 intervals)
            ‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒
            #1 ¦   49.76µs            'dumps<ujson>'
            #2 ¦  294.94µs   -492.73% 'dumps<json>'
            ‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒
            '''

            c = Compare(ujson.loads, json.loads)
            c.time(100, ujson.dumps(rd))
            '''
            (Results after 100 intervals)
            ‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒
            #1 ¦  62.89µs            'loads<ujson>'
            #2 ¦  86.01µs    -36.76% 'loads<json>'
            ‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒
            '''
        ..
    """
    __slots__ = (
        '_callables', '_callable_results', 'precision', 'verbose',
        'progress', 'num_intervals')

    def __init__(self, *callables, precision=8, verbose=False):
        """ A memory-efficient, performant and accurate tool to compare the
            execution times of given @callables

            @callables: one or several #callable objects
            @precision: #int number of decimals to round time intervals to
            @verbose: prints the results with individual :props:Timer.stats
                included.

            |‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒|
            | (dumps<ujson>)                                  |
            | Intervals: 100                                  |
            |      Mean: 46.1µs                               |
            |       Min: 38.59µs                              |
            |    Median: 50.01µs                              |
            |       Max: 104.23µs                             |
            |  St. Dev.: 8.3µs                                |
            |     Total: 4.61ms                               |
            |-·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--|
            | (dumps<json>)                                   |
            | Intervals: 100                                  |
            |      Mean: 82.22µs                              |
            |       Min: 72.65µs                              |
            |    Median: 85.63µs                              |
            |       Max: 184.47µs                             |
            |  St. Dev.: 12.63µs                              |
            |     Total: 8.22ms                               |
            |-·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--|
            | #1 ¦   46.1µs            'dumps<ujson>'         |
            | #2 ¦  82.22µs    -78.37% 'dumps<json>'          |
            |‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒‒|
        """
        self._callables = []
        self._callable_results = []
        self.precision = precision
        self.verbose = verbose
        self.num_intervals = 0
        self.progress = ProgressBar(visible=False)
        self.add(*callables)

    @prepr('precision', _doc=True)
    def __repr__(self): return

    def add(self, *callables):
        """ Adds one or several @callables to the next timing """
        self._callables.extend(callables)

    def time(self, intervals=1, *args, _show_progress=True, _print=True,
             _collect_garbage=False, **kwargs):
        """ Measures the execution time of :prop:_callables for @intervals

            @intervals: #int number of intervals to measure the execution time
                of the function for
            @*args: arguments to pass to the callable being timed
            @**kwargs: arguments to pass to the callable being timed
            @_show_progress: #bool whether or not to print a progress bar
            @_print: #bool whether or not to print the results of the timing
            @_collect_garbage: #bool whether or not to garbage collect
                while timing
            @_quiet: #bool whether or not to disable the print() function's
                ability to output to terminal during the timing

            -> #tuple of :class:Timer :prop:results of timing
        """
        self.reset()
        self.num_intervals = intervals
        for func in self.progress(self._callables):
            try:
                #: Don't ruin all timings if just one doesn't work
                t = Timer(
                    func, _precision=self.precision,
                    _parent_progressbar=self.progress)
                t.time(
                    intervals, *args, _print=False,
                    _show_progress=_show_progress,
                    _collect_garbage=_collect_garbage,
                    **kwargs)
            except Exception as e:
                print(RuntimeWarning(
                    "{} with {}".format(colorize(
                        "{} failed".format(Look.pretty_objname(
                            func, color="yellow")), "yellow"), repr(e))))
            self._callable_results.append(t)
            self.progress.update()
        self.info(_print=_print)
        return self.results

    def _pct_diff(self, best, other):
        """ Calculates and colorizes the percent difference between @best
            and @other
        """
        return colorize("{}%".format(
            round(((best-other)/best)*100, 2)).rjust(10), "red")

    def info(self, _print=True, _verbose=None):
        """ Prints and formats the results of the timing
            @_print: #bool whether or not to print out to terminal
            @_verbose: #bool True if you'd like to print the individual timing
                results in additions to the comparison results
        """
        if _print:
            flag("Results after {} intervals".format(
                bold(self.num_intervals, close=False)),
                colors.notice_color, padding="top")
            line("‒")
            _verbose = _verbose if _verbose is not None else self.verbose
            if _verbose:
                for result in self._callable_results:
                    result.info()
                    line()
            diffs = [
                (i, result.mean)
                for i, result in enumerate(self._callable_results)
                if result.mean]
            ranking = [
                (i, self._callable_results[i].format_time(r))
                for i, r in sorted(diffs, key=lambda x: x[1])]
            max_rlen = len(str(len(ranking)))+2
            max_rlen2 = max(len(r) for i, r in ranking)+1
            best = self._callable_results[ranking[0][0]].mean
            for idx, (i, rank) in enumerate(ranking, 1):
                _obj_name = Look(self._callables[i]).objname()
                pct = "".rjust(10) if idx == 1 else \
                    self._pct_diff(best, self._callable_results[i].mean)
                print(
                    ("#"+str(idx)+" ¦").rjust(max_rlen), rank.rjust(max_rlen2),
                    pct, "{}".format(_obj_name))
            line("‒", padding="bottom")

    @property
    def results(self):
        """ -> #tuple of :class:Timer objects for each :prop:_callables """
        return tuple(self._callable_results)

    def reset(self):
        """ Resets the intervals """
        self.num_intervals = 0
        self._callable_results = []
