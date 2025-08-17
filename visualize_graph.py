import csv
import networkx as nx
import matplotlib.pyplot as plt

FILE_PATH = "dataset/roadNet-CA.txt"


def parse_graph(file_path):
    """
    Parses a tab-delimited graph file into a dictionary where each key is a node and its value is a list of connected nodes.

    :param file_path: str - Path to the graph file.
    :return: dict - A dictionary representing the adjacency list of the graph.
    """
    graph = {}
    with open(file_path, "r") as file:
        reader = csv.reader(file, delimiter="\t")
        next(reader)  # Skip the header line
        for line in reader:
            if "#" in line[0]:  # Skip comment lines
                continue
            from_node, to_node = line
            if from_node not in graph:
                graph[from_node] = []
            graph[from_node].append(to_node)
    return graph


def extract_nodes(path):
    """
    Extracts nodes from a path string formatted as "Path: node1 -> node2 -> ...".

    :param path: str - Path string to extract nodes from.
    :return: list - List of nodes as strings.
    """
    return path.strip("Path: ").split(" -> ")


def get_subgraph_and_connections(graph, nodes):
    """
    Extracts a subgraph and additional connections from a graph based on a list of nodes.

    :param graph: dict - The full graph represented as an adjacency list.
    :param nodes: list - List of nodes for which the subgraph is extracted.
    :return: tuple - A tuple containing two dictionaries: subgraph and additional_edges.
    """
    subgraph = {}
    additional_edges = {}
    for node in nodes:
        connected_nodes = graph.get(node, [])
        for connected_node in connected_nodes:
            if node in nodes and connected_node in nodes:
                if node not in subgraph:
                    subgraph[node] = []
                subgraph[node].append(connected_node)
            elif node in nodes:
                if node not in additional_edges:
                    additional_edges[node] = []
                additional_edges[node].append(connected_node)
    return subgraph, additional_edges


def print_graph(subgraph):
    """
    Prints the subgraph as adjacency list.

    :param subgraph: dict - The subgraph to print.
    """
    for from_node, to_nodes in subgraph.items():
        for to_node in to_nodes:
            print(f"{from_node} -> {to_node}")


def visualize_subgraph(subgraph, additional_edges, nodes_in_path, simplify=False):
    """
    Visualizes the subgraph using NetworkX and Matplotlib, highlighting the main path and additional edges differently.

    :param subgraph: dict - The subgraph to visualize.
    :param additional_edges: dict - Additional edges to be visualized differently.
    :param nodes_in_path: list - List of nodes in the main path to highlight.
    :param simplify: bool - Whether to simplify the visualization (default is False).
    """
    G = nx.DiGraph()
    # Add main path edges with unidirectional arrows
    for from_node, to_nodes in subgraph.items():
        for to_node in to_nodes:
            G.add_edge(from_node, to_node, color="green")
    if not simplify:
        # Add additional connected edges
        for from_node, to_nodes in additional_edges.items():
            for to_node in to_nodes:
                G.add_edge(from_node, to_node, color="red")

    plt.figure(figsize=(15, 8))
    pos = nx.spring_layout(G, k=2)  # Layout for better visualization
    edges = G.edges(data=True)
    colors = [edge[2]["color"] for edge in edges]
    node_colors = {node: "skyblue" for node in G.nodes()}  # Default color
    if nodes_in_path:
        node_colors[nodes_in_path[0]] = "yellow"  # First node
        node_colors[nodes_in_path[-1]] = "green"  # Last node
    node_color_list = [
        node_colors[node] for node in G.nodes()
    ]  # Convert to list for nx.draw

    nx.draw(
        G,
        pos,
        with_labels=True,
        edge_color=colors,
        node_color=node_color_list,
        node_size=1200,
        font_size=12,
        width=3,
        arrowstyle="->",
    )
    plt.title("Visualized Subgraph with Additional Connections")
    plt.show()


if __name__ == "__main__":
    """
    Main execution block: Parses a graph, reads paths from a file, and visualizes each path with its context within the graph.
    """
    graph = parse_graph(FILE_PATH)  # Ensure to use the correct file path
    with open("output.txt", "r") as file:
        lines = file.readlines()
        for line in lines:
            path_query = line.strip()
            if path_query:
                nodes_in_path = extract_nodes(path_query)
                subgraph, additional_edges = get_subgraph_and_connections(
                    graph, nodes_in_path
                )
                print_graph(subgraph)
                # Simplify the visualization if the number of nodes in path exceeds 50
                simplify = len(nodes_in_path) > 50
                visualize_subgraph(
                    subgraph, additional_edges, nodes_in_path, simplify=simplify
                )
