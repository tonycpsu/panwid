# Mixin class for mapping keyboard input to widget methods.

import logging
logger = logging.getLogger(__name__)
# import os
# if os.environ.get("DEBUG"):
#     logger.setLevel(logging.DEBUG)
#     formatter = logging.Formatter("%(asctime)s [%(levelname)8s] %(message)s",
#                                   datefmt='%Y-%m-%d %H:%M:%S')
#     fh = logging.FileHandler("keymap.log")
#     fh.setFormatter(formatter)
#     logger.addHandler(fh)
# else:
#     logger.addHandler(logging.NullHandler())

import six
import urwid
import re

_camel_snake_re_1 = re.compile(r'(.)([A-Z][a-z]+)')
_camel_snake_re_2 = re.compile('([a-z0-9])([A-Z])')

def camel_to_snake(s):
    s = _camel_snake_re_1.sub(r'\1_\2', s)
    return _camel_snake_re_2.sub(r'\1_\2', s).lower()


def optional_arg_decorator(fn):
    def wrapped_decorator(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return fn(args[0])
        else:
            def real_decorator(decoratee):
                return fn(decoratee, *args, **kwargs)
            return real_decorator
    return wrapped_decorator


@optional_arg_decorator
def keymap_command(f, command=None):
    f._keymap = True
    f._keymap_command = command
    return f


def keymapped():

    def wrapper(cls):

        def keypress_decorator(func):

            def keypress(self, size, key):
                key = super(cls, self).keypress(size, key)
                if not key:
                    return
                logger.debug("%s wrapped keypress: %s" %(self.__class__.__name__, key))
                # logger.debug("%s scope: %s, keymap: %s" %(self.__class__.__name__, self.KEYMAP_SCOPE, getattr(self, "KEYMAP", None)))
                for scope in [cls.KEYMAP_SCOPE, "any"]:
                    # logger.debug("key: %s, scope: %s, %s, %s" %(key, scope, self.KEYMAP_SCOPE, self.KEYMAP))
                    if not scope in self.KEYMAP.keys():
                        continue
                    if key in self.KEYMAP[scope]:
                        val = self.KEYMAP[scope][key]
                        if not isinstance(val, list):
                            val = [val]
                        for cmd in val:
                            command = cmd.replace(" ", "_")
                            if not command in self.KEYMAP_MAPPING:
                                logger.debug("%s: %s not in mapping %s" %(cls, key, self.KEYMAP_MAPPING))
                                continue
                            if hasattr(self, command):
                                fn_name = command
                            else:
                                fn_name = self.KEYMAP_MAPPING[command]
                            getattr(self, fn_name)()
                    return key
                else:
                    return key

                return key

            return keypress

        def default_keypress(self, size, key):
            logger.debug("default keypress: %s" %(key))
            key = super(cls, self).keypress(size, key)
            return key

        if not hasattr(cls, "KEYMAP"):
            cls.KEYMAP = {}
        scope = camel_to_snake(cls.__name__)
        cls.KEYMAP_SCOPE = scope
        func = getattr(cls, "keypress", None)
        logger.debug("func class: %s" %(cls.__name__))
        if not func:
            logger.debug("setting default keypress for %s" %(cls.__name__))
            cls.keypress = default_keypress
        else:
            cls.keypress = keypress_decorator(func)
        if not hasattr(cls, "KEYMAP_MAPPING"):
            cls.KEYMAP_MAPPING = {}
        cls.KEYMAP_MAPPING.update({
            (getattr(getattr(cls, k), "_keymap_command", k) or k).replace(" ", "_"): k
            for k in cls.__dict__.keys()
            if hasattr(getattr(cls, k), '_keymap')
        })
        return cls
    return wrapper


@keymapped()
class KeymapMovementMixin(object):

    def cycle_position(self, n):

        if len(self):
            pos = self.focus_position + n
            if pos > len(self) - 1:
                pos = len(self) - 1
            elif pos < 0:
                pos = 0
            self.focus_position = pos

    @keymap_command("up")
    def keymap_up(self): self.cycle_position(-1)

    @keymap_command("down")
    def keymap_down(self): self.cycle_position(1)

    @keymap_command("page up")
    def keymap_page_up(self): self.cycle_position(-self.page_size)

    @keymap_command("page down")
    def keymap_page_down(self): self.cycle_position(self.page_size)

    @keymap_command("home")
    def keymap_home(self): self.focus_position = 0

    @keymap_command("end")
    def keymap_end(self): self.focus_position = len(self)-1

__all__ = [
    "keymapped",
    "keymap_command",
    "KeymapMovementMixin"
]
