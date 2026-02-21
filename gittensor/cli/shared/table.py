# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Reusable Rich table presets."""

from dataclasses import dataclass

from rich import box
from rich.table import Table


@dataclass(frozen=True)
class TableTheme:
    box_style: box.Box
    header_style: str
    border_style: str
    show_lines: bool
    pad_edge: bool


TABLE_THEMES = {
    # Full wrapped grid
    'square': TableTheme(
        box_style=box.SQUARE,
        header_style='bold magenta',
        border_style='grey35',
        show_lines=True,
        pad_edge=True,
    ),

    # Minimal separators with a heavier header rule
    'minimal': TableTheme(
        box_style=box.MINIMAL_HEAVY_HEAD,
        header_style='bold white',
        border_style='grey50',
        show_lines=False,
        pad_edge=False,
    ),
}

DEFAULT_TABLE_THEME = 'minimal'

def build_table(theme: str = DEFAULT_TABLE_THEME, **kwargs) -> Table:
    """Create a Rich table using a named visual theme."""
    preset = TABLE_THEMES.get(theme, TABLE_THEMES[DEFAULT_TABLE_THEME])
    return Table(
        box=preset.box_style,
        header_style=preset.header_style,
        border_style=preset.border_style,
        show_lines=preset.show_lines,
        pad_edge=preset.pad_edge,
        **kwargs,
    )
