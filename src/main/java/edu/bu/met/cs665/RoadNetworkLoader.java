/**
 * Name: Mukul Jangid
 * Course: CS-665 Software Designs & Patterns
 * Date: 05/02/2024
 * File Name: RoadNetworkLoader.java
 * Description: Utility class to load a graph representation of road networks from a file.
 */

package edu.bu.met.cs665;

import java.io.BufferedReader;
import java.io.IOException;
import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultWeightedEdge;

public class RoadNetworkLoader {

  /**
   * Loads a graph from input data, parsing edges with weights from a BufferedReader. Skips lines
   * prefixed with '#'.
   *
   * @param reader The BufferedReader source.
   * @return The loaded graph or null on error.
   */
  public static Graph<Integer, DefaultWeightedEdge> loadGraph(BufferedReader reader) {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    int linesProcessed = 0;

    try {
      String line;
      while ((line = reader.readLine()) != null) {
        if (!line.startsWith("#")) {
          linesProcessed++;
          if (linesProcessed % 1_000_000 == 0) {
            System.out.println("Processed " + linesProcessed + " lines...");
          }
          String[] parts = line.split("\t");
          if (parts.length == 2) {
            int fromNodeId = Integer.parseInt(parts[0]);
            int toNodeId = Integer.parseInt(parts[1]);
            builder.addEdge(fromNodeId, toNodeId, 1.0);
          } else if (parts.length == 3) {
            int fromNodeId = Integer.parseInt(parts[0]);
            int toNodeId = Integer.parseInt(parts[1]);
            double weight = Double.parseDouble(parts[2]);
            builder.addEdge(fromNodeId, toNodeId, weight);
          }
        }
      }
    } catch (IOException e) {
      System.err.println("Failed to read the file: " + e.getMessage());
      return null;
    }
    return builder.build();
  }
}
