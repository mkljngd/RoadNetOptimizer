// Implements the Bellman-Ford algorithm to calculate the shortest path in a graph.
package edu.bu.met.cs665;

import java.util.Collections;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.alg.shortestpath.BellmanFordShortestPath;
import org.jgrapht.graph.DefaultWeightedEdge;

public class BellmanFordStrategy implements RouteStrategy {

  @Override
  public List<Integer> calculateRoute(
      Graph<Integer, DefaultWeightedEdge> graph, int startVertex, int endVertex) {
    BellmanFordShortestPath<Integer, DefaultWeightedEdge> bellmanFord =
        new BellmanFordShortestPath<>(graph);
    GraphPath<Integer, DefaultWeightedEdge> path = bellmanFord.getPath(startVertex, endVertex);
    if (path != null) {
      return path.getVertexList();
    } else {
      return Collections.emptyList(); // Return an empty list if no path is found
    }
  }
}
