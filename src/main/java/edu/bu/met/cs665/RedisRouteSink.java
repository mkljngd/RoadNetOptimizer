package edu.bu.met.cs665;

import io.github.cdimascio.dotenv.Dotenv;
import java.net.URI;
import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;
import redis.clients.jedis.*;

public class RedisRouteSink implements RouteSink {
  private final JedisPool pool;
  private final String listKey;
  private final Integer ttlSeconds;

  public RedisRouteSink(
      String host, int port, String password, String listKey, Integer ttlSeconds) {
    Dotenv dotenv = Dotenv.load();

    int db = Integer.parseInt(dotenv.get("REDIS_DB", "0"));
    String uri =
        (password == null || password.isEmpty())
            ? String.format("redis://%s:%d/%d", host, port, db)
            : String.format("redis://:%s@%s:%d/%d", password, host, port, db);

    this.pool = new JedisPool(new JedisPoolConfig(), URI.create(uri));
    this.listKey = listKey;
    this.ttlSeconds = ttlSeconds;
  }

  @Override
  public void saveRoute(int startVertex, int endVertex, List<Integer> route) {
    String formatted =
        "Path: " + route.stream().map(String::valueOf).collect(Collectors.joining(" -> "));
    try (Jedis jedis = pool.getResource()) {
      jedis.lpush(listKey, formatted);
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
