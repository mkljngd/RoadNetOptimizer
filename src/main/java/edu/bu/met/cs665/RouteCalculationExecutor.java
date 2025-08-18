// Description: Manages the execution of route calculations using different strategies on a
// multi-threaded environment.

package edu.bu.met.cs665;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;
import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultWeightedEdge;

public class RouteCalculationExecutor {

  private static final Logger LOGGER = Logger.getLogger(RouteCalculationExecutor.class.getName());
  private ExecutorService executor;
  private Graph<Integer, DefaultWeightedEdge> graph;
  private final RouteSink sink;

  /**
   * Constructs a RouteCalculationExecutor with a graph and specified thread pool size.
   *
   * @param graph Graph to calculate routes on.
   * @param threadCount Number of threads in the pool.
   */
  public RouteCalculationExecutor(
      Graph<Integer, DefaultWeightedEdge> graph, int threadCount, RouteSink sink) {
    this.graph = graph;
    this.executor = Executors.newFixedThreadPool(threadCount);
    this.sink = sink;
  }

  /**
   * Calculates the shortest path between two vertices using a given strategy, logging and storing
   * the result.
   *
   * @param startVertex Start vertex of the route.
   * @param endVertex End vertex of the route.
   * @param strategy Strategy for pathfinding.
   */
  public void executeRouteCalculation(int startVertex, int endVertex, RouteStrategy strategy) {
    executor.submit(
        () -> {
          try {
            List<Integer> route = strategy.calculateRoute(graph, startVertex, endVertex);
            if (route != null && !route.isEmpty()) {
              String formattedRoute = formatRoute(route);
              LOGGER.info(
                  "Route from " + startVertex + " to " + endVertex + ":\n" + formattedRoute);
              sink.saveRoute(startVertex, endVertex, route);
            } else {
              LOGGER.info("No available route from " + startVertex + " to " + endVertex);
            }
          } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Error calculating route", e);
          }
        });
  }

  private String formatRoute(List<Integer> route) {
    return "Path: " + route.stream().map(Object::toString).collect(Collectors.joining(" -> "));
  }

  /** Terminates the executor, ensuring active tasks complete before shutdown. */
  public void shutdown() {
    executor.shutdown();
    try {
      if (!executor.awaitTermination(60, TimeUnit.SECONDS)) executor.shutdownNow();
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      LOGGER.log(Level.SEVERE, "Thread was interrupted", e);
    } finally {
      try {
        sink.close();
      } catch (Exception ignore) {
      }
    }
  }
}
