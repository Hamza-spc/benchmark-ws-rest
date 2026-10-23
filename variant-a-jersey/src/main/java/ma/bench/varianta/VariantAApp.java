package ma.bench.varianta;

import ma.bench.varianta.json.ObjectMapperProvider;
import org.glassfish.grizzly.http.server.HttpServer;
import org.glassfish.grizzly.threadpool.ThreadPoolConfig;
import org.glassfish.jersey.grizzly2.httpserver.GrizzlyHttpServerFactory;
import org.glassfish.jersey.jackson.JacksonFeature;
import org.glassfish.jersey.server.ResourceConfig;

import java.net.URI;

/**
 * Variante A : Jersey (JAX-RS) + Hibernate, serveur Grizzly embarqué.
 * Threads HTTP et pool JDBC alignés sur les variantes Spring (200 / 10).
 */
public final class VariantAApp {

    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(System.getProperty("server.port", "8081"));

        ResourceConfig config = new ResourceConfig()
                .packages("ma.bench.varianta.resources")
                .register(JacksonFeature.class)
                .register(ObjectMapperProvider.class);

        HttpServer server = GrizzlyHttpServerFactory.createHttpServer(
                URI.create("http://0.0.0.0:" + port + "/"), config, false);

        ThreadPoolConfig workers = ThreadPoolConfig.defaultConfig()
                .setPoolName("grizzly-worker")
                .setCorePoolSize(50)
                .setMaxPoolSize(200);
        server.getListener("grizzly").getTransport().setWorkerThreadPoolConfig(workers);

        // force l'initialisation Hibernate avant la première requête
        Hibernate.sessionFactory();
        server.start();

        System.out.println("Variant A (Jersey + Hibernate) started on http://localhost:" + port);

        // Grizzly n'expose que des threads démons : on bloque le thread principal
        Thread.currentThread().join();
    }
}
