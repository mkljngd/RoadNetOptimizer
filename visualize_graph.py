"""
Interactive path visualizer (Plotly) for routes stored in Redis.

- Reads "Path: A -> B -> C" entries from a Redis list (default key: routes)
- Lets you pick a route
- Lays it out in a straight line or multi-row "snake"
- Saves an interactive HTML with pan/zoom & hover
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import webbrowser
from dataclasses import dataclass
from typing import Dict, List, Tuple

import plotly.graph_objects as go
import redis
from dotenv import load_dotenv


# Configuration helpers
def env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val.strip())
    except (TypeError, ValueError):
        return default


def env_float(name: str, default: float) -> float:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return float(val.strip())
    except (TypeError, ValueError):
        return default


def env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() not in ("0", "false", "no")


def env_str(name: str, default: str) -> str:
    val = os.getenv(name)
    return default if val is None else val


@dataclass
class Config:
    # Redis
    redis_url: str | None
    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str | None
    redis_list_key: str

    # Layout / visuals
    layout: str  # "snake" | "single"
    cols_per_row: int  # used for "snake"
    max_display_routes: int
    label_every: int | None  # None => auto
    node_size: int
    edge_width: float
    save_dir: str
    open_in_browser: bool

    @staticmethod
    def from_env() -> "Config":
        return Config(
            redis_url=env_str("REDIS_URL", None),
            redis_host=env_str("REDIS_HOST", "localhost"),
            redis_port=env_int("REDIS_PORT", 6379),
            redis_db=env_int("REDIS_DB", 0),
            redis_password=env_str("REDIS_PASSWORD", None),
            redis_list_key=env_str("REDIS_LIST_KEY", "routes"),
            layout=env_str("LAYOUT", "snake").lower(),
            cols_per_row=max(2, env_int("COLS_PER_ROW", 25)),
            max_display_routes=env_int("MAX_DISPLAY_ROUTES", 200),
            label_every=(
                (env_int("LABEL_EVERY", -1) or None)
                if os.getenv("LABEL_EVERY") is not None
                else None
            ),
            node_size=max(2, env_int("NODE_SIZE", 12)),
            edge_width=max(0.5, env_float("EDGE_WIDTH", 2.5)),
            save_dir=env_str("SAVE_DIR", "."),
            open_in_browser=env_bool("OPEN_IN_BROWSER", True),
        )


# Redis
def connect_redis(cfg: Config) -> redis.Redis:
    """
    Connect via REDIS_URL or host/port/db/password env vars.
    """
    if cfg.redis_url:
        return redis.from_url(cfg.redis_url, decode_responses=True)

    return redis.Redis(
        host=cfg.redis_host,
        port=cfg.redis_port,
        db=cfg.redis_db,
        password=cfg.redis_password or None,
        decode_responses=True,
    )


# Route list handling
def extract_nodes(path_line: str) -> List[str]:
    """
    Accepts 'Path: 1 -> 2 -> 3' and returns ['1','2','3'].
    Tolerant of extra spaces; ignores empty tokens.
    """
    prefix = "Path:"
    s = path_line.strip()
    if s.lower().startswith(prefix.lower()):
        s = s[len(prefix) :].strip()
    parts = [p.strip() for p in s.split("->")]
    return [p for p in parts if p]


def choose_single_route(route_lines: List[str], redis_list_key: str, cap: int) -> str:
    """
    Show the first 'cap' routes and prompt for one.
    Returns the chosen raw route string or '' if cancelled.
    """
    total = len(route_lines)
    shown = min(total, cap)

    print(f"\nFound {total} route(s) in Redis list '{redis_list_key}'.")
    if total > cap:
        print(f"Showing first {cap} for selection (set MAX_DISPLAY_ROUTES to change).")

    for idx, line in enumerate(route_lines[:shown], start=1):
        # Extract nodes from "Path: x -> y -> z"
        parts = line.replace("Path:", "").strip().split("->")
        if len(parts) >= 2:
            start = parts[0].strip()
            end = parts[-1].strip()
            display = f"Path: {start} ---> {end}"
        else:
            display = line  # fallback if malformed
        print(f"{idx:3d}. {display}")

    if total == 0:
        return ""

    while True:
        choice = input(
            f"\nEnter the index (1-{shown}) of the route to visualize (or 'q' to quit): "
        ).strip()
        if choice.lower() in ("q", "quit", "exit"):
            return ""
        if not choice.isdigit():
            print("Please enter a valid number.")
            continue
        i = int(choice)
        if 1 <= i <= shown:
            return route_lines[i - 1]
        print(f"Please enter a number between 1 and {shown}.")


# Layouts for longer paths
def layout_single_row(nodes: List[str]) -> Dict[str, Tuple[float, float]]:
    """Place nodes left-to-right on a straight line."""
    spacing = 1.0
    return {n: (i * spacing, 0.0) for i, n in enumerate(nodes)}


def layout_snake(nodes: List[str], cols: int) -> Dict[str, Tuple[float, float]]:
    """
    Place nodes in multiple rows ("snake" pattern):
      row0 -> left-to-right,
      row1 -> right-to-left, etc.
    """
    pos: Dict[str, Tuple[float, float]] = {}
    spacing_x = 1.0
    spacing_y = 1.2

    for i, n in enumerate(nodes):
        row = i // cols
        col = i % cols
        x = col * spacing_x if row % 2 == 0 else (cols - 1 - col) * spacing_x
        y = -(row * spacing_y)
        pos[n] = (x, y)
    return pos


def compute_pos(
    nodes: List[str], layout: str, cols_per_row: int
) -> Dict[str, Tuple[float, float]]:
    return (
        layout_single_row(nodes)
        if layout == "single"
        else layout_snake(nodes, cols_per_row)
    )


def label_every_auto(n: int) -> int:
    """Label ~20 nodes max; all if <= 25."""
    if n <= 25:
        return 1
    target = 20
    return max(1, n // target)


# Plotly drawing
def draw_path_interactive(
    nodes: List[str],
    pos: Dict[str, Tuple[float, float]],
    node_size: int,
    edge_width: float,
    label_every: int | None,
    save_dir: str,
    layout_name: str,
) -> str:
    """
    Build the interactive figure with pan/zoom & hover. Returns path to saved HTML.
    """
    if len(nodes) < 2:
        raise ValueError("Path must contain at least 2 nodes.")

    # Edge polyline (one trace with 'None' separators)
    xs, ys = [], []
    for i in range(len(nodes) - 1):
        a, b = nodes[i], nodes[i + 1]
        xa, ya = pos[a]
        xb, yb = pos[b]
        xs += [xa, xb, None]
        ys += [ya, yb, None]

    edge_trace = go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line=dict(width=edge_width, color="#1E88E5"),
        hoverinfo="skip",
        name="Path edges",
    )

    # Node trace with hover + throttled text labels
    node_x = [pos[n][0] for n in nodes]
    node_y = [pos[n][1] for n in nodes]
    hover_text = [f"Index: {i+1}<br>Node: {n}" for i, n in enumerate(nodes)]

    colors = []
    for i in range(len(nodes)):
        if i == 0:
            colors.append("#FFD54F")  # start
        elif i == len(nodes) - 1:
            colors.append("#66BB6A")  # end
        else:
            colors.append("#90CAF9")  # on-path

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_size, color=colors, line=dict(width=1.2, color="#37474F")
        ),
        textposition="top center",
        hoverinfo="text",
        hovertext=hover_text,
        name="Nodes",
        text=[],  # filled below
    )

    step = (
        label_every
        if (label_every and label_every > 0)
        else label_every_auto(len(nodes))
    )
    labels = []
    for i, n in enumerate(nodes):
        if i == 0 or i == len(nodes) - 1 or (i % step == 0):
            labels.append(str(n))
        else:
            labels.append("")
    node_trace.text = labels

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=f"Route {nodes[0]} → {nodes[-1]}  (|path|={len(nodes)})",
        showlegend=True,
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.6)"),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=30, r=30, t=60, b=30),
        dragmode="pan",
    )

    # Save self-contained HTML
    os.makedirs(save_dir, exist_ok=True)
    safe_start = re.sub(r"[^\w\-]+", "_", str(nodes[0]))
    safe_end = re.sub(r"[^\w\-]+", "_", str(nodes[-1]))
    out_name = f"route_{safe_start}_{safe_end}_{len(nodes)}_{layout_name}.html"
    out_path = os.path.join(save_dir, out_name)
    fig.write_html(out_path, include_plotlyjs="cdn", full_html=True)
    return out_path


# Top-level flow
def visualize_once(cfg: Config) -> None:
    try:
        r = connect_redis(cfg)
    except Exception as e:
        print(f"[Error] Could not connect to Redis: {e}")
        return

    try:
        total = r.llen(cfg.redis_list_key) or 0
        route_lines = r.lrange(
            cfg.redis_list_key, 0, max(0, cfg.max_display_routes - 1)
        )
    except Exception as e:
        print(f"[Error] Redis error while reading list '{cfg.redis_list_key}': {e}")
        return

    print(
        f"\n[Info] Loaded {total} route(s) from list '{cfg.redis_list_key}'. "
        f"Showing up to {cfg.max_display_routes}."
    )
    if not route_lines:
        print(f"No routes found in Redis list '{cfg.redis_list_key}'.")
        return

    chosen = choose_single_route(
        route_lines, cfg.redis_list_key, cfg.max_display_routes
    )
    if not chosen:
        print("No route selected. Goodbye.")
        return

    nodes = extract_nodes(chosen)
    if len(nodes) < 2:
        print(f"[Warn] Selected route is invalid/too short: '{chosen}'")
        return

    pos = compute_pos(nodes, cfg.layout, cfg.cols_per_row)

    try:
        out_html = draw_path_interactive(
            nodes=nodes,
            pos=pos,
            node_size=cfg.node_size,
            edge_width=cfg.edge_width,
            label_every=cfg.label_every,
            save_dir=cfg.save_dir,
            layout_name=cfg.layout,
        )
    except Exception as e:
        print(f"[Error] Failed to render/save visualization: {e}")
        return

    print(f"[Saved] {out_html}")
    if cfg.open_in_browser:
        try:
            webbrowser.open(f"file://{os.path.abspath(out_html)}", new=2)
        except Exception as e:
            print(f"[Warn] Could not open browser automatically: {e}")


def repl(cfg: Config) -> None:
    """Run app in a loop until user types 'exit'."""
    try:
        visualize_once(cfg)
        while True:
            cmd = (
                input(
                    "\nPress Enter to visualize another route, or type 'exit' to quit: "
                )
                .strip()
                .lower()
            )
            if cmd == "exit":
                break
            visualize_once(cfg)
    except (KeyboardInterrupt, EOFError):
        pass


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Interactive path visualizer (Plotly) for routes in Redis."
    )
    p.add_argument(
        "--layout",
        choices=["snake", "single"],
        help="Layout style (overrides LAYOUT env).",
    )
    p.add_argument(
        "--cols",
        type=int,
        help="Columns per row in 'snake' layout (overrides COLS_PER_ROW).",
    )
    p.add_argument(
        "--label-every",
        type=int,
        help="Label every Nth node; 1=all (overrides LABEL_EVERY).",
    )
    p.add_argument("--save-dir", help="Directory to save HTML (overrides SAVE_DIR).")
    p.add_argument(
        "--no-browser", action="store_true", help="Do not auto-open the HTML."
    )
    return p.parse_args()


def apply_cli_overrides(cfg: Config, args: argparse.Namespace) -> Config:
    if args.layout:
        cfg.layout = args.layout
    if args.cols and args.cols > 1:
        cfg.cols_per_row = args.cols
    if args.label_every and args.label_every > 0:
        cfg.label_every = args.label_every
    if args.save_dir:
        cfg.save_dir = args.save_dir
    if args.no_browser:
        cfg.open_in_browser = False
    return cfg


def main() -> None:
    load_dotenv()
    cfg = Config.from_env()
    args = parse_args()
    cfg = apply_cli_overrides(cfg, args)
    repl(cfg)


if __name__ == "__main__":
    main()
