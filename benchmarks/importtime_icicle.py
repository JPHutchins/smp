"""Render a ``python -X importtime`` log as an icicle graph (SVG).

Unlike a cProfile flame graph (which is dominated by ``importlib`` machinery),
this visualizes the *module import tree*: every block is a module, its width is
proportional to cumulative import time, and packages are colored so the cost of
a dependency such as ``pydantic`` is legible at a glance.

Usage::

    python -X importtime -c "from smp import image_management" 2> log.txt
    python benchmarks/importtime_icicle.py log.txt --root smp.image_management > out.svg
"""

from __future__ import annotations

import sys
from typing import NamedTuple


class Node(NamedTuple):
    name: str
    self_us: float
    cum_us: float
    children: tuple[Node, ...]


class Row(NamedTuple):
    depth: int
    self_us: float
    cum_us: float
    name: str


_PREFIX = "import time:"


def parse_rows(text: str) -> tuple[Row, ...]:
    def row(line: str) -> Row:
        self_str, cum_str, name_field = line[len(_PREFIX) :].split("|")
        depth = (len(name_field) - len(name_field.lstrip(" ")) - 1) // 2
        return Row(depth, float(self_str), float(cum_str), name_field.strip())

    return tuple(
        row(line)
        for line in text.splitlines()
        if line.startswith(_PREFIX) and "cumulative" not in line
    )


def build_forest(rows: tuple[Row, ...]) -> tuple[Node, ...]:
    """Reconstruct the import tree from post-order rows with depth indentation."""
    stack: list[tuple[int, Node]] = []
    for depth, self_us, cum_us, name in rows:
        kids: list[Node] = []
        while stack and stack[-1][0] > depth:
            kids.append(stack.pop()[1])
        stack.append((depth, Node(name, self_us, cum_us, tuple(reversed(kids)))))
    return tuple(node for _, node in stack)


def find(forest: tuple[Node, ...], name: str) -> Node | None:
    for node in forest:
        if node.name == name:
            return node
        if (hit := find(node.children, name)) is not None:
            return hit
    return None


_PALETTE: tuple[tuple[str, str], ...] = (
    ("pydantic", "#e74c3c"),
    ("annotated_types", "#e67e22"),
    ("msgspec", "#27ae60"),
    ("cbor2", "#8e44ad"),
    ("smp", "#2980b9"),
)


def color(name: str) -> str:
    return next((c for prefix, c in _PALETTE if name.split(".")[0] == prefix), "#95a5a6")


class Rect(NamedTuple):
    x: float
    y: float
    w: float
    h: float
    name: str
    cum_us: float


def layout(
    node: Node, x: float, y: float, w: float, scale: float, row_h: float
) -> tuple[Rect, ...]:
    here = Rect(x, y, w, row_h, node.name, node.cum_us)
    offset = x
    kids: list[Rect] = []
    for child in node.children:
        cw = child.cum_us * scale
        kids.extend(layout(child, offset, y + row_h, cw, scale, row_h))
        offset += cw
    return (here, *kids)


def render_svg(root: Node, width: float, row_h: float = 21.0) -> str:
    scale = width / root.cum_us
    rects = layout(root, 0.0, 0.0, width, scale, row_h)
    height = max(r.y for r in rects) + row_h + 4

    def label(r: Rect) -> str:
        budget = int(r.w // 6.2)
        if budget < 4:
            return ""
        short = r.name if len(r.name) <= budget else r.name[: budget - 1] + "…"
        return (
            f'<text x="{r.x + 3:.1f}" y="{r.y + row_h - 6:.1f}" '
            f'font-family="monospace" font-size="11" fill="#111">{_esc(short)}</text>'
        )

    body = "\n".join(
        f'<rect x="{r.x:.1f}" y="{r.y:.1f}" width="{max(r.w - 1, 0):.1f}" height="{row_h - 1:.1f}" '
        f'fill="{color(r.name)}" stroke="#fff" stroke-width="0.5">'
        f"<title>{_esc(r.name)} — {r.cum_us / 1000:.1f} ms</title></rect>\n{label(r)}"
        for r in rects
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}">\n'
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="#fff"/>\n{body}\n</svg>\n'
    )


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _rect_svg(r: Rect, row_h: float) -> str:
    budget = int(r.w // 6.2)
    short = "" if budget < 4 else (r.name if len(r.name) <= budget else r.name[: budget - 1] + "…")
    text = (
        ""
        if not short
        else f'<text x="{r.x + 3:.1f}" y="{r.y + row_h - 6:.1f}" '
        f'font-family="monospace" font-size="11" fill="#111">{_esc(short)}</text>'
    )
    return (
        f'<rect x="{r.x:.1f}" y="{r.y:.1f}" width="{max(r.w - 1, 0):.1f}" height="{row_h - 1:.1f}" '
        f'fill="{color(r.name)}" stroke="#fff" stroke-width="0.5">'
        f"<title>{_esc(r.name)} — {r.cum_us / 1000:.1f} ms</title></rect>\n{text}"
    )


def render_compare(
    panels: tuple[tuple[str, Node], ...], full_width: float = 1500.0, row_h: float = 20.0
) -> str:
    px_per_us = full_width / max(node.cum_us for _, node in panels)
    blocks: list[str] = []
    y = 0.0
    for title, node in panels:
        y += 26.0
        blocks.append(
            f'<text x="0" y="{y - 9:.1f}" font-family="sans-serif" font-size="15" '
            f'font-weight="bold" fill="#111">{_esc(title)} — {node.cum_us / 1000:.0f} ms</text>'
        )
        rects = layout(node, 0.0, y, node.cum_us * px_per_us, px_per_us, row_h)
        blocks.append("\n".join(_rect_svg(r, row_h) for r in rects))
        y = max(r.y for r in rects) + row_h + 18.0
    width = full_width + 20
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{y:.0f}" '
        f'viewBox="0 0 {width:.0f} {y:.0f}">\n'
        f'<rect width="{width:.0f}" height="{y:.0f}" fill="#fff"/>\n'
        + "\n".join(blocks)
        + "\n</svg>\n"
    )


def _opt(name: str, default: str | None = None) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def _root_of(path: str, root_name: str | None) -> Node:
    with open(path) as f:
        forest = build_forest(parse_rows(f.read()))
    root = find(forest, root_name) if root_name else (forest[-1] if forest else None)
    if root is None:
        raise SystemExit(f"root {root_name!r} not found in {path}")
    return root


def main() -> None:
    root_name = _opt("--root")
    if "--compare" in sys.argv:
        i = sys.argv.index("--compare")
        before, after = sys.argv[i + 1], sys.argv[i + 2]
        panels = (
            ("BEFORE (pydantic)", _root_of(before, root_name)),
            ("AFTER (msgspec)", _root_of(after, root_name)),
        )
        sys.stdout.write(render_compare(panels))
    else:
        sys.stdout.write(
            render_svg(_root_of(sys.argv[1], root_name), width=float(_opt("--width", "1600")))
        )


if __name__ == "__main__":
    main()
