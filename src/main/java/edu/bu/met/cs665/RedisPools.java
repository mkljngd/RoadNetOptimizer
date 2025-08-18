// src/main/java/edu/bu/met/cs665/RedisPools.java
package edu.bu.met.cs665;

import io.github.cdimascio.dotenv.Dotenv;
import java.net.URI;
import redis.clients.jedis.*;

public final class RedisPools {
  private static JedisPool POOL;

  public static synchronized JedisPool get() {
    if (POOL != null) return POOL;
    Dotenv dotenv = Dotenv.load();

    String url = dotenv.get("REDIS_URL");
    if (url != null && !url.isEmpty()) {
      // Expect url like redis://[:password@]host:port/4
      POOL = new JedisPool(new JedisPoolConfig(), URI.create(url));
      return POOL;
    }
    String host = dotenv.get("REDIS_HOST", "localhost");
    int port = Integer.parseInt(dotenv.get("REDIS_PORT", "6379"));
    String password = dotenv.get("REDIS_PASSWORD", "");
    int db = Integer.parseInt(dotenv.get("REDIS_DB", "0"));

    String uri =
        (password == null || password.isEmpty())
            ? String.format("redis://%s:%d/%d", host, port, db)
            : String.format("redis://:%s@%s:%d/%d", password, host, port, db);
    POOL = new JedisPool(new JedisPoolConfig(), URI.create(uri));
    return POOL;
  }

  private RedisPools() {}
}
