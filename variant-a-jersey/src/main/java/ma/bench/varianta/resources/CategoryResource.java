package ma.bench.varianta.resources;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import ma.bench.varianta.Hibernate;
import ma.bench.varianta.entities.Category;
import ma.bench.varianta.entities.Item;
import ma.bench.varianta.json.CategoryDto;
import ma.bench.varianta.json.CategoryInput;
import ma.bench.varianta.json.ItemDto;
import ma.bench.varianta.json.PageResponse;
import org.hibernate.Session;

import java.util.List;

/** Contrôleur JAX-RS écrit à la main (variante A). */
@Path("/categories")
@Produces(MediaType.APPLICATION_JSON)
public class CategoryResource {

    @GET
    public PageResponse<CategoryDto> list(@QueryParam("page") @DefaultValue("0") int page,
                                          @QueryParam("size") @DefaultValue("50") int size) {
        try (Session s = Hibernate.open()) {
            List<Category> rows = s.createQuery("select c from Category c order by c.id", Category.class)
                    .setFirstResult(page * size)
                    .setMaxResults(size)
                    .getResultList();
            long total = s.createQuery("select count(c) from Category c", Long.class).getSingleResult();
            return PageResponse.of(rows.stream().map(CategoryDto::of).toList(), page, size, total);
        }
    }

    @GET
    @Path("/{id}")
    public Response get(@PathParam("id") long id) {
        try (Session s = Hibernate.open()) {
            Category c = s.find(Category.class, id);
            return c == null ? Response.status(Response.Status.NOT_FOUND).build()
                    : Response.ok(CategoryDto.of(c)).build();
        }
    }

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    public Response create(CategoryInput in) {
        try (Session s = Hibernate.open()) {
            s.beginTransaction();
            Category c = new Category();
            c.setCode(in.code());
            c.setName(in.name());
            s.persist(c);
            s.getTransaction().commit();
            return Response.ok(CategoryDto.of(c)).build();
        }
    }

    @PUT
    @Path("/{id}")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response update(@PathParam("id") long id, CategoryInput in) {
        try (Session s = Hibernate.open()) {
            s.beginTransaction();
            Category c = s.find(Category.class, id);
            if (c == null) {
                s.getTransaction().rollback();
                return Response.status(Response.Status.NOT_FOUND).build();
            }
            c.setCode(in.code());
            c.setName(in.name());
            s.getTransaction().commit();
            return Response.ok(CategoryDto.of(c)).build();
        }
    }

    @DELETE
    @Path("/{id}")
    public Response delete(@PathParam("id") long id) {
        try (Session s = Hibernate.open()) {
            s.beginTransaction();
            Category c = s.find(Category.class, id);
            if (c == null) {
                s.getTransaction().rollback();
                return Response.status(Response.Status.NOT_FOUND).build();
            }
            s.remove(c);
            s.getTransaction().commit();
            return Response.noContent().build();
        }
    }

    /** Association inverse : produits d'une catégorie. */
    @GET
    @Path("/{id}/items")
    public PageResponse<ItemDto> items(@PathParam("id") long id,
                                       @QueryParam("page") @DefaultValue("0") int page,
                                       @QueryParam("size") @DefaultValue("50") int size) {
        try (Session s = Hibernate.open()) {
            List<Item> rows = s.createQuery(
                            "select i from Item i join fetch i.category where i.category.id = :cid order by i.id", Item.class)
                    .setParameter("cid", id)
                    .setFirstResult(page * size)
                    .setMaxResults(size)
                    .getResultList();
            long total = s.createQuery("select count(i) from Item i where i.category.id = :cid", Long.class)
                    .setParameter("cid", id)
                    .getSingleResult();
            return PageResponse.of(rows.stream().map(ItemDto::of).toList(), page, size, total);
        }
    }
}
