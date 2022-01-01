# Mixin class for mapping keyboard input to widget methods.

import logging
logger = logging.getLogger(__name__)

import six
import asyncio
import urwid
import re

KEYMAP_GLOBAL = {}

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
def keymap_command(f, command=None, *args, **kwargs):
    f._keymap = True
    f._keymap_command = command
    f._keymap_args = args
    f._keymap_kwargs = kwargs
    return f


def keymapped():

    def wrapper(cls):

        cls.KEYMAP_MERGED = {}

        if not hasattr(cls, "KEYMAP_SCOPE"):
            cls.KEYMAP_SCOPE = classmethod(lambda cls: camel_to_snake(cls.__name__))
        elif isinstance(cls.KEYMAP_SCOPE, str):
            cls.KEYMAP_SCOPE = classmethod(lambda cls: cls.KEYMAP_SCOPE)

        if not cls.KEYMAP_SCOPE() in cls.KEYMAP_MERGED:
            cls.KEYMAP_MERGED[cls.KEYMAP_SCOPE()] = {}
        if getattr(cls, "KEYMAP", False):
            cls.KEYMAP_MERGED[cls.KEYMAP_SCOPE()].update(**cls.KEYMAP)


        for base in cls.mro():
            if hasattr(base, "KEYMAP"):
                if not base.KEYMAP_SCOPE() in cls.KEYMAP_MERGED:
                    cls.KEYMAP_MERGED[base.KEYMAP_SCOPE()] = {}
                cls.KEYMAP_MERGED[base.KEYMAP_SCOPE()].update(**base.KEYMAP)

        # from pprint import pprint; print(cls.KEYMAP_MERGED)
        if not hasattr(cls, "KEYMAP_MAPPING"):
            cls.KEYMAP_MAPPING = {}

        cls.KEYMAP_MAPPING.update(**getattr(cls.__base__, "KEYMAP_MAPPING", {}))

        cls.KEYMAP_MAPPING.update({
            (getattr(getattr(cls, k), "_keymap_command", k) or k).replace(" ", "_"): k
            for k in cls.__dict__.keys()
            if hasattr(getattr(cls, k), '_keymap')
        })

        def keymap_command(self, cmd):
            logger.debug(f"keymap_command: {cmd}")
            args = []
            kwargs = {}

            if callable(cmd):
                f = cmd
            else:
                if isinstance(cmd, tuple):
                    if len(cmd) == 3:
                        (cmd, args, kwargs) = cmd
                    elif len(cmd) == 2:
                        if isinstance(cmd[1], dict):
                            (cmd, kwargs) = cmd
                        else:
                            (cmd, args) = cmd
                    else:
                        raise Exception
                elif isinstance(cmd, str):
                    cmd = cmd.replace(" ", "_")
                else:
                    logger.debug(f"keymap command {cmd} not valid")
                    return None

                if hasattr(self, cmd):
                    fn_name = cmd
                else:
                    try:
                        fn_name = self.KEYMAP_MAPPING[cmd]
                    except KeyError:
                        raise KeyError(cmd, self.KEYMAP_MAPPING, type(self))

                f = getattr(self, fn_name)

            ret = f(*args, **kwargs)
            if asyncio.iscoroutine(ret):
                asyncio.get_event_loop().create_task(ret)
            return None

        cls._keymap_command = keymap_command

        def keymap_register(self, key, cmd):
            self.KEYMAP_MERGED[cls.KEYMAP_SCOPE()][key] = cmd

        cls.keymap_register = keymap_register

        def keypress_decorator(func):


            def keypress(self, size, key):
                # logger.debug(f"{cls} wrapped keypress: {key}, {cls.KEYMAP_SCOPE()}, {self.KEYMAP_MERGED.get(cls.KEYMAP_SCOPE(), {}).keys()}")

                if key and callable(func):
                    # logger.debug(f"{cls} wrapped keypress, key: {key}, calling orig: {func}")
                    key = func(self, size, key)
                if key:
                    # logger.debug(f"{cls} wrapped keypress, key: {key}, calling super: {super(cls, self).keypress}")
                    key = super(cls, self).keypress(size, key)
                keymap_combined = dict(self.KEYMAP_MERGED, **KEYMAP_GLOBAL)
                if key and keymap_combined.get(cls.KEYMAP_SCOPE(), {}).get(key, None):
                    cmd = keymap_combined[cls.KEYMAP_SCOPE()][key]
                    if isinstance(cmd, str) and cmd.startswith("keypress "):
                        new_key = cmd.replace("keypress ", "").strip()
                        # logger.debug(f"{cls} remap {key} => {new_key}")
                        key = new_key
                    else:
                        # logger.debug(f"{cls} wrapped keypress, key: {key}, calling keymap command")
                        key = self._keymap_command(cmd)
                return key

            return keypress

        cls.keypress = keypress_decorator(getattr(cls, "keypress", None))
        return cls

    return wrapper




@keymapped()
class KeymapMovementMixin(object):

    @classmethod
    def KEYMAP_SCOPE(cls):
        return "movement"

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
