// Test cases for the project.

package edu.bu.met.cs665;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.io.BufferedReader;
import java.io.StringReader;
import java.util.Arrays;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.junit.Test;

public class RouteOptimizationTests {

  @Test
  public void testGraphBuilding() {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    builder.addVertex(1).addVertex(2).addEdge(1, 2, 5.0);
    Graph<Integer, DefaultWeightedEdge> graph = builder.build();

    assertTrue(graph.containsVertex(1));
    assertTrue(graph.containsVertex(2));
    assertTrue(graph.containsEdge(1, 2));
    assertEquals(5.0, graph.getEdgeWeight(graph.getEdge(1, 2)), 0.01);
  }

  @Test
  public void testDijkstraAlgorithm() {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    builder.addVertex(1).addVertex(2).addVertex(3);
    builder.addEdge(1, 2, 1.0).addEdge(2, 3, 2.0).addEdge(1, 3, 4.0);
    Graph<Integer, DefaultWeightedEdge> graph = builder.build();
    DijkstraStrategy strategy = new DijkstraStrategy();

    List<Integer> path = strategy.calculateRoute(graph, 1, 3);

    assertEquals(Arrays.asList(1, 2, 3), path);
  }

  @Test
  public void testBellmanFordAlgorithm() {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    builder.addVertex(1).addVertex(2).addVertex(3);
    builder.addEdge(1, 2, -1.0).addEdge(2, 3, 2.0).addEdge(1, 3, 2.0);
    Graph<Integer, DefaultWeightedEdge> graph = builder.build();
    BellmanFordStrategy strategy = new BellmanFordStrategy();

    List<Integer> path = strategy.calculateRoute(graph, 1, 3);

    assertEquals(Arrays.asList(1, 2, 3), path);
  }

  @Test
  public void testGraphSelfLoops() {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    builder.addVertex(1).addEdge(1, 1, 3.0);
    Graph<Integer, DefaultWeightedEdge> graph = builder.build();
    assertTrue(graph.containsEdge(1, 1));
    assertEquals(3.0, graph.getEdgeWeight(graph.getEdge(1, 1)), 0.01);
  }

  @Test
  public void testGraphLoadingFromFile() throws Exception {
    // Prepare the data as a string and pass it to a BufferedReader
    String data = "1\t2\t1.0\n2\t3\t2.0";
    BufferedReader reader = new BufferedReader(new StringReader(data));

    // Pass the BufferedReader directly to the loadGraph method
    Graph<Integer, DefaultWeightedEdge> graph = RoadNetworkLoader.loadGraph(reader);

    assertNotNull(graph);
    assertTrue(graph.containsVertex(1));
    assertTrue(graph.containsVertex(2));
    assertTrue(graph.containsVertex(3));
    assertTrue(graph.containsEdge(1, 2));
    assertTrue(graph.containsEdge(2, 3));
    assertEquals(1.0, graph.getEdgeWeight(graph.getEdge(1, 2)), 0.01);
    assertEquals(2.0, graph.getEdgeWeight(graph.getEdge(2, 3)), 0.01);
  }

  @Test
  public void testDijkstraNoPath() {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    builder.addVertex(1).addVertex(2);
    Graph<Integer, DefaultWeightedEdge> graph = builder.build();
    DijkstraStrategy strategy = new DijkstraStrategy();

    List<Integer> path = strategy.calculateRoute(graph, 1, 2);
    assertTrue("Path should be empty when no direct route exists", path.isEmpty());
  }

  @Test
  public void testBellmanFordNoPath() {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    builder.addVertex(1).addVertex(2);
    Graph<Integer, DefaultWeightedEdge> graph = builder.build();
    BellmanFordStrategy strategy = new BellmanFordStrategy();

    List<Integer> path = strategy.calculateRoute(graph, 1, 2);
    assertTrue("Path should be empty when no direct route exists", path.isEmpty());
  }

  @Test
  public void testGraphLoadingErrorHandling() throws Exception {
    String data = "1\t2\n2\t3\tcorrupt";
    BufferedReader reader = new BufferedReader(new StringReader(data));
    try {
      Graph<Integer, DefaultWeightedEdge> graph = RoadNetworkLoader.loadGraph(reader);
      fail("Should have thrown an exception due to corrupted data.");
    } catch (NumberFormatException e) {
      assertNotNull(e);
    }
  }

  @Test
  public void testEmptyGraph() {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    Graph<Integer, DefaultWeightedEdge> graph = builder.build();
    assertTrue(graph.vertexSet().isEmpty());
    assertTrue(graph.edgeSet().isEmpty());
  }
}
