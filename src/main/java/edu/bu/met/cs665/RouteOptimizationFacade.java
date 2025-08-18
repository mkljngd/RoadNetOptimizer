// Facade class to simplify interactions with the route calculation components.
package edu.bu.met.cs665;

import io.github.cdimascio.dotenv.Dotenv;
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
    Dotenv dotenv = Dotenv.load();

    System.out.println("Loading road network...");
    try (BufferedReader reader = new BufferedReader(new FileReader(DATA_FILE_PATH))) {
      graph = RoadNetworkLoader.loadGraph(reader);
    } catch (IOException | RuntimeException e) {
      System.err.println("Error loading graph: " + e.getMessage());
      graph = null;
    }
    if (graph != null) {
      System.out.println("Graph loaded successfully.");
      // Redis config: system props override env, with sensible defaults
      String host = dotenv.get("REDIS_HOST", "localhost");
      int port = Integer.parseInt(dotenv.get("REDIS_PORT", "6379"));
      String password = dotenv.get("REDIS_PASSWORD", "");
      String listKey = dotenv.get("REDIS_LIST_KEY", "routes");
      Integer ttlSeconds = null; // or Integer.valueOf(86400);

      RouteSink sink = new RedisRouteSink(host, port, password, listKey, ttlSeconds);
      executor = new RouteCalculationExecutor(graph, 10, sink);
    } else {
      System.out.println("Failed to load graph.");
    }
  }

  public void optimizeRoute(int startVertex, int endVertex, String algorithmName) {
    if (executor == null) {
      System.out.println("Executor unavailable: Graph not loaded!");
      return;
    }
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
    if (executor == null) return;
    executor.shutdown();
  }

  // Added method to return the graph
  public Graph<Integer, DefaultWeightedEdge> getGraph() {
    return graph;
  }
}
