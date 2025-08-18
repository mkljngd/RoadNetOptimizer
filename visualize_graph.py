#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import redis
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

load_dotenv()
# ---------- Config ----------
REDIS_LIST_KEY = os.getenv("REDIS_LIST_KEY", "routes")  # list of "Path: 1 -> 2 -> 3"
REDIS_ADJ_PREFIX = os.getenv(
    "REDIS_ADJ_PREFIX", "adj:"
)  # sets: adj:<from> -> {to, to, ...}
MAX_EXTRA_EDGES_PER_SRC = 6  # cap to reduce clutter (tweak to taste)
PATH_LONG_SIMPLIFY_THRESHOLD = 50  # skip extra edges for very long paths
MAX_DISPLAY_ROUTES = int(
    os.getenv("MAX_DISPLAY_ROUTES", "200")
)  # safety cap for printing
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


# ---------- Load graph from Redis ----------


def load_graph_from_redis(r: redis.Redis, adj_prefix: str) -> Dict[str, List[str]]:
    """
    Build an adjacency dict by scanning Redis for keys like 'adj:<from>'.
    Each key is a SET of neighbors for the 'from' node.
    """
    graph: Dict[str, List[str]] = {}
    pattern = f"{adj_prefix}*"
    for key in r.scan_iter(match=pattern, count=1000):
        if not key.startswith(adj_prefix):
            continue
        from_node = key[len(adj_prefix) :]
        neighbors = sorted(r.smembers(key))  # stable output (optional)
        if neighbors:
            graph[from_node] = neighbors
    return graph


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


def get_subgraph_and_connections(
    graph: Dict[str, List[str]], nodes: List[str]
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Build a subgraph (edges with both endpoints in 'nodes') and collect
    'additional_edges' where src in 'nodes' but dst not in 'nodes'.
    """
    subgraph: Dict[str, List[str]] = {}
    additional_edges: Dict[str, List[str]] = {}
    node_set = set(nodes)
    for node in nodes:
        for cn in graph.get(node, []):
            if cn in node_set:
                subgraph.setdefault(node, []).append(cn)
            else:
                additional_edges.setdefault(node, []).append(cn)
    return subgraph, additional_edges


# ---------- Structured layout helpers ----------


def compute_positions(
    nodes_in_path: List[str],
    subgraph: Dict[str, List[str]],
    additional_edges: Dict[str, List[str]],
) -> Dict[str, Tuple[float, float]]:
    """
    Deterministic left-to-right coordinates:
    - Main path nodes on y=0, evenly spaced.
    - Extra neighbors placed above/below the line near their source.
    """
    pos: Dict[str, Tuple[float, float]] = {}

    # main line
    spacing = 2.0
    for i, n in enumerate(nodes_in_path):
        pos[n] = (i * spacing, 0.0)

    # neighbors
    above_y, below_y = +1.5, -1.5
    offsets: Dict[Tuple[str, float], int] = {}

    def place_neighbor(src: str, dst: str, above: bool = True):
        y = above_y if above else below_y
        key = (src, y)
        idx = offsets.get(key, 0)
        offsets[key] = idx + 1
        step = 0.8
        dx = (idx // 2 + 1) * step
        dx = dx if idx % 2 == 0 else -dx
        sx, _ = pos.get(src, (0.0, 0.0))
        pos[dst] = (sx + dx, y)

    toggle = True
    for src, neighbors in additional_edges.items():
        for dst in neighbors:
            if dst not in pos:  # don't overwrite path nodes
                place_neighbor(src, dst, above=toggle)
                toggle = not toggle

    # ensure every subgraph node has a position
    for src, tos in subgraph.items():
        pos.setdefault(src, pos.get(src, (0.0, 0.0)))
        for dst in tos:
            pos.setdefault(dst, pos.get(dst, (0.0, 0.0)))

    return pos


def visualize_subgraph(
    subgraph: Dict[str, List[str]],
    additional_edges: Dict[str, List[str]],
    nodes_in_path: List[str],
    simplify: bool = False,
    max_extra_per_src: int = MAX_EXTRA_EDGES_PER_SRC,
):
    """
    Draw a clean, structured visualization:
    - Main path straight line (left→right), thicker blue edges
    - Start/end highlighted
    - Other outgoing edges in soft gray, placed above/below the line near the source
    """
    G = nx.DiGraph()

    # main edges
    main_edges = []
    for src, tos in subgraph.items():
        for dst in tos:
            G.add_edge(src, dst)
            main_edges.append((src, dst))

    # extra edges
    extra_edges = []
    if not simplify:
        for src, tos in additional_edges.items():
            if max_extra_per_src is not None and max_extra_per_src >= 0:
                tos = tos[:max_extra_per_src]
            for dst in tos:
                G.add_edge(src, dst)
                extra_edges.append((src, dst))

    pos = compute_positions(
        nodes_in_path, subgraph, additional_edges if not simplify else {}
    )

    # figure size scales with path length
    path_len = max(len(nodes_in_path), 2)
    width = min(max(8, path_len * 0.6), 24)
    height = 6 if not extra_edges else 8

    plt.figure(figsize=(width, height))

    # node colors
    node_color_map = []
    path_set = set(nodes_in_path)
    for n in G.nodes():
        if nodes_in_path:
            if n == nodes_in_path[0]:
                node_color_map.append("#FFD54F")  # start (amber)
            elif n == nodes_in_path[-1]:
                node_color_map.append("#66BB6A")  # end (green)
            elif n in path_set:
                node_color_map.append("#90CAF9")  # on-path (light blue)
            else:
                node_color_map.append("#CFD8DC")  # off-path (grey-blue)
        else:
            node_color_map.append("#CFD8DC")

    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=node_color_map,
        node_size=900,
        linewidths=1.5,
        edgecolors="#37474F",
    )

    # edges
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=main_edges,
        arrows=True,
        arrowstyle="->",
        arrowsize=16,
        width=3.0,
        edge_color="#1E88E5",
        connectionstyle="arc3,rad=0.0",
    )
    if extra_edges:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=extra_edges,
            arrows=True,
            arrowstyle="->",
            arrowsize=12,
            width=1.5,
            edge_color="#B0BEC5",
            alpha=0.95,
            connectionstyle="arc3,rad=0.0",
        )

    # labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_color="#263238")

    # annotate path order
    for i, n in enumerate(nodes_in_path):
        x, y = pos[n]
        plt.text(
            x, y + 0.28, f"{i+1}", fontsize=9, ha="center", va="bottom", color="#37474F"
        )

    # legend
    legend_elems = [
        Line2D([0], [0], color="#1E88E5", lw=3, label="Main path"),
        Line2D([0], [0], color="#B0BEC5", lw=2, label="Other outgoing edges"),
    ]
    plt.legend(handles=legend_elems, loc="upper left")

    # title
    if nodes_in_path:
        plt.title(
            f"Route {nodes_in_path[0]} \u2192 {nodes_in_path[-1]}  (|path|={len(nodes_in_path)})"
        )
    else:
        plt.title("Route")

    plt.axis("off")
    plt.tight_layout()
    plt.show()


# ---------- User selection ----------


def choose_single_route(route_lines: List[str]) -> str:
    """
    Print a numbered list of routes and prompt the user to choose ONE by index.
    Returns the chosen route string (e.g., 'Path: 1 -> 2 -> 3') or '' if none chosen.
    """
    total = len(route_lines)
    cap = min(total, MAX_DISPLAY_ROUTES)

    print(f"\nFound {total} route(s) in Redis list '{REDIS_LIST_KEY}'.")
    if total > MAX_DISPLAY_ROUTES:
        print(
            f"Showing first {MAX_DISPLAY_ROUTES} for selection (set MAX_DISPLAY_ROUTES to change)."
        )

    # show routes (trim long ones for readability)
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


# ---------- Main ----------


def main():
    r = connect_redis()

    # 1) Build the full graph from Redis adjacency sets
    graph = load_graph_from_redis(r, REDIS_ADJ_PREFIX)
    if not graph:
        print(
            f"ERROR: No adjacency found in Redis with prefix '{REDIS_ADJ_PREFIX}'. "
            f"Ensure your Java loader is writing 'SADD {REDIS_ADJ_PREFIX}<from> <to>'.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2) Pull route lines from Redis (list 'routes' by default)
    route_lines = r.lrange(REDIS_LIST_KEY, 0, -1)
    if not route_lines:
        print(f"No routes found in Redis list '{REDIS_LIST_KEY}'.")
        return

    # 3) Ask the user which single route to visualize
    chosen = choose_single_route(route_lines)
    if not chosen:
        print("No route selected. Goodbye.")
        return

    # 4) Visualize the selected route
    nodes_in_path = extract_nodes(chosen)
    if len(nodes_in_path) < 2:
        print(f"Selected route is invalid/too short: '{chosen}'")
        return

    subgraph, additional_edges = get_subgraph_and_connections(graph, nodes_in_path)
    simplify = len(nodes_in_path) >= PATH_LONG_SIMPLIFY_THRESHOLD

    visualize_subgraph(
        subgraph,
        additional_edges,
        nodes_in_path,
        simplify=simplify,
        max_extra_per_src=MAX_EXTRA_EDGES_PER_SRC,
    )


if __name__ == "__main__":
    main()
