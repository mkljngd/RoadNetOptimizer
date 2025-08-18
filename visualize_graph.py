#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import webbrowser
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import redis
import plotly.graph_objects as go

load_dotenv()

# ---------- Config ----------
REDIS_LIST_KEY = os.getenv(
    "REDIS_LIST_KEY", "routes"
)  # list entries: "Path: 1 -> 2 -> 3"

# Layout controls
LAYOUT = os.getenv("LAYOUT", "snake").lower()  # "snake" or "single"
COLS_PER_ROW = int(os.getenv("COLS_PER_ROW", "25"))  # for "snake" layout

# Label density (None/auto or a positive int)
LABEL_EVERY_ENV = os.getenv("LABEL_EVERY")  # "1" to label all nodes
MAX_DISPLAY_ROUTES = int(os.getenv("MAX_DISPLAY_ROUTES", "200"))

# Styling
NODE_SIZE = int(os.getenv("NODE_SIZE", "12"))  # marker size in px
EDGE_WIDTH = float(os.getenv("EDGE_WIDTH", "2.5"))  # path edge width
SAVE_DIR = os.getenv("SAVE_DIR", ".")

# Open the saved HTML in your default browser
OPEN_IN_BROWSER = os.getenv("OPEN_IN_BROWSER", "1") not in ("0", "false", "False")
# ----------------------------


def connect_redis() -> redis.Redis:
    """Connect via REDIS_URL or fall back to host/port/db/password env vars."""
    url = os.getenv("REDIS_URL")
    if url:
        return redis.from_url(url, decode_responses=True)
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    password = os.getenv("REDIS_PASSWORD")
    return redis.Redis(
        host=host, port=port, db=db, password=password, decode_responses=True
    )


# ---------- Utils ----------


def extract_nodes(path_line: str) -> List[str]:
    """Accepts 'Path: 1 -> 2 -> 3' and returns ['1','2','3']."""
    prefix = "Path: "
    s = (
        path_line[len(prefix) :].strip()
        if path_line.startswith(prefix)
        else path_line.strip()
    )
    return [p.strip() for p in s.split(" -> ") if p.strip()]


def choose_single_route(route_lines: List[str]) -> str:
    """Show routes and prompt for one."""
    total = len(route_lines)
    cap = min(total, MAX_DISPLAY_ROUTES)
    print(f"\nFound {total} route(s) in Redis list '{REDIS_LIST_KEY}'.")
    if total > MAX_DISPLAY_ROUTES:
        print(
            f"Showing first {MAX_DISPLAY_ROUTES} for selection (set MAX_DISPLAY_ROUTES to change)."
        )

    def trim(s: str, maxlen: int = 120) -> str:
        return s if len(s) <= maxlen else s[: maxlen - 3] + "..."

    for idx, line in enumerate(route_lines[:cap], start=1):
        print(f"{idx:3d}. {trim(line)}")

    if total == 0:
        return ""

    while True:
        choice = input(
            f"\nEnter the index (1-{cap}) of the route to visualize (or 'q' to quit): "
        ).strip()
        if choice.lower() in ("q", "quit", "exit"):
            return ""
        if not choice.isdigit():
            print("Please enter a valid number.")
            continue
        i = int(choice)
        if 1 <= i <= cap:
            return route_lines[i - 1]
        else:
            print(f"Please enter a number between 1 and {cap}.")


# ---------- Layouts for a long path ----------


def layout_single_row(nodes: List[str]) -> Dict[str, Tuple[float, float]]:
    """Place nodes left-to-right on a straight line."""
    pos: Dict[str, Tuple[float, float]] = {}
    spacing = 1.0
    for i, n in enumerate(nodes):
        pos[n] = (i * spacing, 0.0)
    return pos


def layout_snake(nodes: List[str], cols: int) -> Dict[str, Tuple[float, float]]:
    """
    Place nodes in multiple rows ("snake" pattern):
      row0 -> left-to-right,
      row1 -> right-to-left, etc.
    """
    pos: Dict[str, Tuple[float, float]] = {}
    spacing_x = 1.0
    spacing_y = 1.2

    cols = max(2, cols)
    for i, n in enumerate(nodes):
        row = i // cols
        col = i % cols
        if row % 2 == 0:
            x = col * spacing_x  # L->R
        else:
            x = (cols - 1 - col) * spacing_x  # R->L
        y = -(row * spacing_y)
        pos[n] = (x, y)
    return pos


def compute_pos(nodes: List[str]) -> Dict[str, Tuple[float, float]]:
    if LAYOUT == "single":
        return layout_single_row(nodes)
    return layout_snake(nodes, COLS_PER_ROW)


def label_every_auto(n: int) -> int:
    """Label ~20 nodes max, all if <= 25."""
    if n <= 25:
        return 1
    target = 20
    return max(1, n // target)


# ---------- Interactive drawing (Plotly) ----------


def draw_path_interactive(nodes: List[str]) -> str:
    """
    Build an interactive figure with pan/zoom & hover.
    Returns path to saved HTML.
    """
    pos = compute_pos(nodes)
    xs, ys = [], []

    # Edge polyline (one big trace with 'None' breaks)
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
        line=dict(width=EDGE_WIDTH, color="#1E88E5"),
        hoverinfo="skip",
        name="Path edges",
    )

    # Node trace with hover
    node_x = [pos[n][0] for n in nodes]
    node_y = [pos[n][1] for n in nodes]
    hover_text = [f"Index: {i+1}<br>Node: {n}" for i, n in enumerate(nodes)]

    # Color start/end differently
    colors = []
    for i, _ in enumerate(nodes):
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
            size=NODE_SIZE, color=colors, line=dict(width=1.2, color="#37474F")
        ),
        textposition="top center",
        hoverinfo="text",
        hovertext=hover_text,
        name="Nodes",
        text=[],
    )

    # Throttle labels (text) for readability
    if LABEL_EVERY_ENV and LABEL_EVERY_ENV.isdigit():
        step = max(1, int(LABEL_EVERY_ENV))
    else:
        step = label_every_auto(len(nodes))

    labels = []
    for i, n in enumerate(nodes):
        if i == 0 or i == len(nodes) - 1 or (i % step == 0):
            labels.append(str(n))
        else:
            labels.append("")  # no label
    node_trace.text = labels

    fig = go.Figure(data=[edge_trace, node_trace])

    fig.update_layout(
        title=f"Route {nodes[0]} → {nodes[-1]}  (|path|={len(nodes)})",
        showlegend=True,
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.6)"),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=30, r=30, t=60, b=30),
        dragmode="pan",  # pan by default; scroll wheel zooms
    )

    # Save self-contained HTML
    os.makedirs(SAVE_DIR, exist_ok=True)
    out_name = f"route_{nodes[0]}_{nodes[-1]}_{len(nodes)}_{LAYOUT}.html"
    out_path = os.path.join(SAVE_DIR, out_name)
    fig.write_html(out_path, include_plotlyjs="cdn", full_html=True)
    return out_path


# ---------- Main / REPL ----------


def visualize_once():
    r = connect_redis()

    cap = MAX_DISPLAY_ROUTES
    total = r.llen(REDIS_LIST_KEY) or 0
    route_lines = r.lrange(REDIS_LIST_KEY, 0, max(0, cap - 1))

    print(
        f"\n[Info] Loaded {total} route(s) from list '{REDIS_LIST_KEY}'. Showing up to {cap}."
    )
    if not route_lines:
        print(f"No routes found in Redis list '{REDIS_LIST_KEY}'.")
        return

    chosen = choose_single_route(route_lines)
    if not chosen:
        print("No route selected. Goodbye.")
        return

    nodes_in_path = extract_nodes(chosen)
    if len(nodes_in_path) < 2:
        print(f"Selected route is invalid/too short: '{chosen}'")
        return

    out_html = draw_path_interactive(nodes_in_path)
    print(f"[Saved] {out_html}")
    if OPEN_IN_BROWSER:
        try:
            webbrowser.open(f"file://{os.path.abspath(out_html)}", new=2)
        except Exception as e:
            print(f"[Warn] Could not open browser: {e}")


def repl():
    """Run app in a loop until user types 'exit'."""
    try:
        visualize_once()
        while True:
            cmd = (
                input(
                    "\nType 'exit' to quit or press Enter to visualize another route: "
                )
                .strip()
                .lower()
            )
            if cmd == "exit":
                break
            visualize_once()
    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == "__main__":
    repl()
