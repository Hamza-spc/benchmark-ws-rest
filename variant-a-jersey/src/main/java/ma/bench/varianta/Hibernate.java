package ma.bench.varianta;

import ma.bench.varianta.entities.Category;
import ma.bench.varianta.entities.Item;
import org.hibernate.Session;
import org.hibernate.SessionFactory;
import org.hibernate.cfg.Configuration;

/** Bootstrap Hibernate (variante A : pas de conteneur Spring). */
public final class Hibernate {

    private static final SessionFactory SESSION_FACTORY = build();

    private Hibernate() {
    }

    private static SessionFactory build() {
        String url = System.getProperty("db.url", "jdbc:postgresql://localhost:5432/bench_rest");
        String user = System.getProperty("db.user", System.getenv().getOrDefault("USER", "hamza"));
        String password = System.getProperty("db.password", "");

        Configuration cfg = new Configuration();
        cfg.addAnnotatedClass(Category.class);
        cfg.addAnnotatedClass(Item.class);
        cfg.setProperty("hibernate.connection.provider_class",
                "org.hibernate.hikaricp.internal.HikariCPConnectionProvider");
        cfg.setProperty("hibernate.hikari.jdbcUrl", url);
        cfg.setProperty("hibernate.hikari.username", user);
        cfg.setProperty("hibernate.hikari.password", password);
        cfg.setProperty("hibernate.hikari.maximumPoolSize", "10");
        cfg.setProperty("hibernate.hikari.minimumIdle", "10");
        cfg.setProperty("hibernate.dialect", "org.hibernate.dialect.PostgreSQLDialect");
        cfg.setProperty("hibernate.show_sql", "false");
        cfg.setProperty("hibernate.jdbc.fetch_size", "100");
        return cfg.buildSessionFactory();
    }

    public static Session open() {
        return SESSION_FACTORY.openSession();
    }

    public static SessionFactory sessionFactory() {
        return SESSION_FACTORY;
    }
}
