/**
 * Name: Mukul Jangid Course: CS-665 Software Designs & Patterns Date: 05/02/2024 File Name:
 * RouteOptimizationFacade.java Description: Facade class to simplify interactions with the route
 * calculation components.
 */
package edu.bu.met.cs665;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultWeightedEdge;

public class RouteOptimizationFacade {
  private static final String DATA_FILE_PATH = "dataset/roadNet-CA.txt";
  private Graph<Integer, DefaultWeightedEdge> graph;
  private RouteCalculationExecutor executor;

  /**
   * Initializes the facade, loading a graph from a file and setting up an executor if successful.
   */
  public RouteOptimizationFacade() {
    System.out.println("Loading road network...");
    try {
      BufferedReader reader = new BufferedReader(new FileReader(DATA_FILE_PATH));
      graph = RoadNetworkLoader.loadGraph(reader);
    } catch (IOException e) {
      System.err.println("Error loading graph: " + e.getMessage());
      graph = null;
    }
    if (graph != null) {
      System.out.println("Graph loaded successfully.");
      executor = new RouteCalculationExecutor(graph, 10);
    } else {
      System.out.println("Failed to load graph.");
    }
  }

  public void optimizeRoute(int startVertex, int endVertex, String algorithmName) {
    RouteStrategy strategy = getRouteStrategy(algorithmName);
    executor.executeRouteCalculation(startVertex, endVertex, strategy);
  }

  private RouteStrategy getRouteStrategy(String algorithmName) {
    if ("BellmanFord".equalsIgnoreCase(algorithmName)) {
      return new BellmanFordStrategy();
    } else {
      return new DijkstraStrategy();
    }
  }

  public void shutdown() {
    executor.shutdown();
  }

  // Added method to return the graph
  public Graph<Integer, DefaultWeightedEdge> getGraph() {
    return graph;
  }
}
