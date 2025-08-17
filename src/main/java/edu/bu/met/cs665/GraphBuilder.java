/**
 * Name: Mukul Jangid
 * Course: CS-665 Software Designs & Patterns
 * Date: 05/02/2024
 * File Name: GraphBuilder.java
 * Description: Provides a builder pattern for constructing graphs with weighted edges.
 */

package edu.bu.met.cs665;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultDirectedWeightedGraph;
import org.jgrapht.graph.DefaultWeightedEdge;

public class GraphBuilder<V, E> {
  private Graph<V, E> graph;

  public GraphBuilder() {
    this.graph = (Graph<V, E>) new DefaultDirectedWeightedGraph<>(DefaultWeightedEdge.class);
  }

  public GraphBuilder<V, E> addVertex(V vertex) {
    graph.addVertex(vertex);
    return this;
  }

  /**
   * Adds an edge with a specified weight between two vertices, adding vertices if necessary.
   *
   * @param sourceVertex Source vertex.
   * @param targetVertex Target vertex.
   * @param weight Edge weight.
   * @return this GraphBuilder instance.
   */
  public GraphBuilder<V, E> addEdge(V sourceVertex, V targetVertex, double weight) {
    graph.addVertex(sourceVertex);
    graph.addVertex(targetVertex);
    E edge = graph.addEdge(sourceVertex, targetVertex);
    graph.setEdgeWeight(edge, weight);
    return this;
  }

  public Graph<V, E> build() {
    return graph;
  }
}
