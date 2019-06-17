__all__ = [
    "is_running_in_ipython", "Beep", "Version", "Counter", "EnVars", "WhoCalledMe", "NameSpace",
    "SysTrayApp", "Beep", "Timer", "Supressor", "PrintRedirector", "NullContext",
    "Serializer", "ByteSerializer", "Secrets",
    "ScriptBase",
    "CommandLine",
    "Log", "PrintLog"
]

from pathmagic import File

resources = File(__file__).dir.newdir("res")

if True:
    from .misc import is_running_in_ipython, Beep, Version, Counter, EnVars, WhoCalledMe, NameSpace
    from .context import SysTrayApp, Timer, Supressor, PrintRedirector, NullContext
    from .serializer import Serializer, ByteSerializer, Secrets
    from .script import ScriptBase
    from .commandline import CommandLine
    from .log import Log, PrintLog
