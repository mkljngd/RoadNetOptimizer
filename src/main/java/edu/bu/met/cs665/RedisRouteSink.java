package edu.bu.met.cs665;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;
import redis.clients.jedis.*;

public class RedisRouteSink implements RouteSink {
  private final JedisPool pool;
  private final String listKey;
  private final Integer ttlSeconds; // null = no TTL

  public RedisRouteSink(
      String host, int port, String password, String listKey, Integer ttlSeconds) {
    JedisPoolConfig cfg = new JedisPoolConfig();
    cfg.setMaxTotal(32);
    cfg.setMinIdle(2);
    cfg.setMaxIdle(8);
    if (password != null && !password.isEmpty()) {
      this.pool = new JedisPool(cfg, host, port, 2000, password);
    } else {
      this.pool = new JedisPool(cfg, host, port);
    }
    this.listKey = listKey;
    this.ttlSeconds = ttlSeconds;
  }

  @Override
  public void saveRoute(int startVertex, int endVertex, List<Integer> route) {
    String formatted =
        "Path: " + route.stream().map(String::valueOf).collect(Collectors.joining(" -> "));
    try (Jedis jedis = pool.getResource()) {
      // Append to a rolling list for recent routes
      jedis.lpush(listKey, formatted);
      // Also upsert a per-(start,end) record
      String key = String.format("route:%d:%d", startVertex, endVertex);
      jedis.hset(key, "path", formatted);
      jedis.hset(key, "ts", Long.toString(Instant.now().toEpochMilli()));
      if (ttlSeconds != null && ttlSeconds > 0) jedis.expire(key, ttlSeconds);
    }
  }

  @Override
  public void close() {
    pool.close();
  }
}
