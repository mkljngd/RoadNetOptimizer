// Utility class to load a graph representation of road networks from a file.

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
  public static Graph<Integer, DefaultWeightedEdge> loadGraph(BufferedReader reader)
      throws IOException {
    GraphBuilder<Integer, DefaultWeightedEdge> builder = new GraphBuilder<>();
    int linesProcessed = 0;
    String line;

    while ((line = reader.readLine()) != null) {
      line = line.trim();
      if (line.isEmpty() || line.startsWith("#")) continue;
      String[] parts = line.split("\t");
      if (parts.length < 2 || parts.length > 3) {
        throw new IllegalArgumentException("Invalid line:" + line);
      }

      int fromNodeId = Integer.parseInt(parts[0]);
      int toNodeId = Integer.parseInt(parts[1]);
      double weight = parts.length == 3 ? Double.parseDouble(parts[2]) : 1.0;
      builder.addEdge(fromNodeId, toNodeId, weight);
      linesProcessed++;
      if (linesProcessed % 1_000_000 == 0) {
        System.out.println("Processed " + linesProcessed + " lines...");
      }
    }

    return builder.build();
  }
}
