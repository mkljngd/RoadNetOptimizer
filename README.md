# Route Optimization & Visualization

## Project Overview
This project develops a **route optimization system** that integrates **Java** and **Python** to efficiently compute and visualize routes on California’s road network.

- **Java Backend**
  - Builds the graph (`GraphBuilder` — *Builder Pattern*).
  - Loads road network dataset (`RoadNetworkLoader`).
  - Computes routes using interchangeable algorithms (`DijkstraStrategy`, `BellmanFordStrategy` — *Strategy Pattern*).
  - Executes computations concurrently (`RouteCalculationExecutor` — *Thread Pool*).
  - Provides a simplified interface (`RouteOptimizationFacade` — *Facade Pattern*).

- **Python Frontend**
  - Visualizes routes with **NetworkX** and **Matplotlib**.
  - Connects to Redis to fetch stored paths.
  - Provides structured visualizations of chosen routes.

This dual approach ensures **robust route optimization** and **clear visual insights**, making it useful for urban planning, logistics, and transportation systems.

---

- **Dataset**: [Stanford roadNet-CA](https://snap.stanford.edu/data/roadNet-CA.html)  
  - Directed graph with ~2M edges and ~1.9M nodes representing California roads.

---

## 🎯 Design Patterns Used
- **Builder** → step-by-step graph construction.  
- **Strategy** → interchangeable routing algorithms.  
- **Facade** → simple interface to complex backend.  
- **Singleton** → application lifecycle management.  
- **Thread Pool** → efficient concurrent route computations.  

---

## Setup & Installation

### 1. Prerequisites
- **Java 17+**
- **Python 3.10+**
- **Redis Server** (running locally or remote)
- **Apache Maven** (for Java build)

---

### 2. Clone the Repository
```bash
git clone <repo_url>
cd <repo_name>
```
⸻

3. Configure Environment Variables

Create a .env file in the root directory:
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=4
REDIS_PASSWORD=
REDIS_LIST_KEY=routes
REDIS_ADJ_PREFIX=adj:
```

⸻

4. Install Dependencies

Java (via Maven):

```bash
mvn clean compile
```

Python:

```bash
pip install -r requirements.txt
```

⸻

Usage

1. Run Java Backend (Compute & Store Routes in Redis)

```bash
mvn exec:java -Dexec.mainClass="edu.bu.met.cs665.RouteOptimizationApp"
```

This will:
	•	Load the roadNet dataset.
	•	Compute routes using selected strategy.
	•	Store paths and adjacency in Redis.

⸻

2. Run Python Visualization
```bash
python visualize_graph.py
```
	•	Lists all stored routes (StartNode ---> EndNode format).
	•	Prompts you to select one by index.
	•	Generates a structured visualization.

Example Visualization:
(Insert screenshot of plotted graph here)

⸻

Testing & Quality Tools

Compile
```bash
mvn clean compile
```
Run Unit Tests
```bash
mvn clean test
```
Static Analysis

SpotBugs:
```bash
mvn spotbugs:gui
```
Checkstyle:
```bash
mvn checkstyle:checkstyle
open target/site/checkstyle.html
```

⸻

Future Improvements
	•	Add more routing algorithms (e.g., A*, Floyd-Warshall).
	•	Optimize Redis schema for very large graphs.
	•	Improve Python visualization for extremely long paths.
	•	Provide a web dashboard for interactive route analysis.

---
