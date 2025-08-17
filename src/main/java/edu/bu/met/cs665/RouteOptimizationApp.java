// Description: Entry point for a console application that allows users to calculate routes using specified algorithms.

package edu.bu.met.cs665;

import java.util.Scanner;

public class RouteOptimizationApp {
  private static RouteOptimizationApp instance;
  private RouteOptimizationFacade facade;

  private RouteOptimizationApp() {
    facade = new RouteOptimizationFacade();
  }

  /**
   * Returns the singleton instance of RouteOptimizationApp, creating it if necessary.
   *
   * @return Singleton instance.
   */
  public static synchronized RouteOptimizationApp getInstance() {
    if (instance == null) {
      instance = new RouteOptimizationApp();
    }
    return instance;
  }

  /**
   * Operates the application interface, processing user inputs for route calculations until 'exit'.
   */
  public void run() {
    try (Scanner scanner = new Scanner(System.in)) {
      System.out.println(
          "Enter start and end vertices separated by space, choose algorithm: Dijkstra or"
              + " BellmanFord ('exit' to quit)");

      while (scanner.hasNextLine()) {
        String input = scanner.nextLine();
        if ("exit".equalsIgnoreCase(input)) {
          break;
        }
        String[] parts = input.split(" ");
        if (parts.length < 3) {
          System.out.println("Please enter start vertex, end vertex, and algorithm name.");
          continue;
        }
        int start = Integer.parseInt(parts[0]);
        int end = Integer.parseInt(parts[1]);
        String algorithm = parts[2];

        facade.optimizeRoute(start, end, algorithm);
      }

      facade.shutdown();
    }
  }

  public static void main(String[] args) {
    RouteOptimizationApp.getInstance().run();
  }
}
