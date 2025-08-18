package edu.bu.met.cs665;

import java.util.List;

public interface RouteSink extends AutoCloseable {
  void saveRoute(int startVertex, int endVertex, List<Integer> route);

  @Override
  void close();
}
