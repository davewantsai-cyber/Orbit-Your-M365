from orbit.core.tools.base import STATUS_GLYPH, LaunchSpec, Tool, ToolStatus
from orbit.core.tools.hawk import Hawk
from orbit.core.tools.maester import Maester
from orbit.core.tools.monkey365 import Monkey365
from orbit.core.tools.roadtools import ROADtools
from orbit.core.tools.scubagear import ScubaGear


def all_tools() -> list[Tool]:
    return [ScubaGear(), Maester(), Monkey365(), ROADtools(), Hawk()]


def get_tool(name: str) -> Tool:
    for t in all_tools():
        if t.name == name:
            return t
    raise KeyError(name)


__all__ = ["STATUS_GLYPH", "LaunchSpec", "Tool", "ToolStatus", "all_tools", "get_tool"]
