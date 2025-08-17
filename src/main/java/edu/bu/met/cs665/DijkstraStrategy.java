// Implements the Dijkstra algorithm for shortest path calculation in a graph.

package edu.bu.met.cs665;

import java.util.Collections;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.alg.shortestpath.DijkstraShortestPath;
import org.jgrapht.graph.DefaultWeightedEdge;

public class DijkstraStrategy implements RouteStrategy {

  @Override
  public List<Integer> calculateRoute(
      Graph<Integer, DefaultWeightedEdge> graph, int startVertex, int endVertex) {
    DijkstraShortestPath<Integer, DefaultWeightedEdge> dijkstra = new DijkstraShortestPath<>(graph);
    GraphPath<Integer, DefaultWeightedEdge> path = dijkstra.getPath(startVertex, endVertex);
    if (path != null) {
      return path.getVertexList();
    } else {
      return Collections.emptyList(); // Return an empty list if no path is found
    }
  }
}
