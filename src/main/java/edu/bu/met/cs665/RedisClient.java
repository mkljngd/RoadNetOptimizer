package edu.bu.met.cs665;

import io.github.cdimascio.dotenv.Dotenv;
import redis.clients.jedis.JedisPooled;

public final class RedisClient {
  private static JedisPooled INSTANCE;

  public static synchronized JedisPooled get() {
    if (INSTANCE == null) {
      Dotenv dotenv = Dotenv.load();
      String url = dotenv.get("REDIS_URL");
      if (url != null && !url.isEmpty()) {
        INSTANCE = new JedisPooled(url);
      } else {
        String host = dotenv.get("REDIS_HOST", "localhost");
        int port = Integer.parseInt(dotenv.get("REDIS_PORT", "6379"));
        int db = Integer.parseInt(dotenv.get("REDIS_DB", "4"));
        INSTANCE = new JedisPooled("redis://" + host + ":" + port + "/" + db);
      }
    }
    return INSTANCE;
  }

  private RedisClient() {}
}
