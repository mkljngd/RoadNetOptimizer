package edu.bu.met.cs665;

import redis.clients.jedis.JedisPooled;

public final class RedisClient {
  private static JedisPooled INSTANCE;

  public static synchronized JedisPooled get() {
    if (INSTANCE == null) {
      String url = System.getenv("REDIS_URL");
      if (url != null && !url.isEmpty()) {
        INSTANCE = new JedisPooled(url);
      } else {
        String host = System.getenv().getOrDefault("REDIS_HOST", "localhost");
        int port = Integer.parseInt(System.getenv().getOrDefault("REDIS_PORT", "6379"));
        INSTANCE = new JedisPooled(host, port);
      }
    }
    return INSTANCE;
  }

  private RedisClient() {}
}
