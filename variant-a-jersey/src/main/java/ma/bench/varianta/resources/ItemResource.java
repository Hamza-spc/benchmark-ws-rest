package ma.bench.varianta.resources;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import ma.bench.varianta.Hibernate;
import ma.bench.varianta.entities.Category;
import ma.bench.varianta.entities.Item;
import ma.bench.varianta.json.ItemDto;
import ma.bench.varianta.json.ItemInput;
import ma.bench.varianta.json.PageResponse;
import org.hibernate.Session;

import java.util.List;

/** Contrôleur JAX-RS écrit à la main (variante A). */
@Path("/items")
@Produces(MediaType.APPLICATION_JSON)
public class ItemResource {

    @GET
    public PageResponse<ItemDto> list(@QueryParam("page") @DefaultValue("0") int page,
                                      @QueryParam("size") @DefaultValue("50") int size,
                                      @QueryParam("categoryId") Long categoryId) {
        try (Session s = Hibernate.open()) {
            String where = categoryId == null ? "" : " where i.category.id = :cid";
            var query = s.createQuery(
                            "select i from Item i join fetch i.category" + where + " order by i.id", Item.class)
                    .setFirstResult(page * size)
                    .setMaxResults(size);
            var countQuery = s.createQuery("select count(i) from Item i" + where, Long.class);
            if (categoryId != null) {
                query.setParameter("cid", categoryId);
                countQuery.setParameter("cid", categoryId);
            }
            List<Item> rows = query.getResultList();
            long total = countQuery.getSingleResult();
            return PageResponse.of(rows.stream().map(ItemDto::of).toList(), page, size, total);
        }
    }

    @GET
    @Path("/{id}")
    public Response get(@PathParam("id") long id) {
        try (Session s = Hibernate.open()) {
            List<Item> rows = s.createQuery(
                            "select i from Item i join fetch i.category where i.id = :id", Item.class)
                    .setParameter("id", id)
                    .getResultList();
            return rows.isEmpty() ? Response.status(Response.Status.NOT_FOUND).build()
                    : Response.ok(ItemDto.of(rows.get(0))).build();
        }
    }

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    public Response create(ItemInput in) {
        try (Session s = Hibernate.open()) {
            s.beginTransaction();
            Category c = s.find(Category.class, in.categoryId());
            if (c == null) {
                s.getTransaction().rollback();
                return Response.status(Response.Status.BAD_REQUEST).build();
            }
            Item i = new Item();
            i.setSku(in.sku());
            i.setName(in.name());
            i.setPrice(in.price());
            i.setStock(in.stock());
            i.setCategory(c);
            s.persist(i);
            s.getTransaction().commit();
            return Response.ok(ItemDto.of(i)).build();
        }
    }

    @PUT
    @Path("/{id}")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response update(@PathParam("id") long id, ItemInput in) {
        try (Session s = Hibernate.open()) {
            s.beginTransaction();
            Item i = s.find(Item.class, id);
            if (i == null) {
                s.getTransaction().rollback();
                return Response.status(Response.Status.NOT_FOUND).build();
            }
            i.setSku(in.sku());
            i.setName(in.name());
            i.setPrice(in.price());
            i.setStock(in.stock());
            if (in.categoryId() != null) {
                Category c = s.find(Category.class, in.categoryId());
                if (c != null) {
                    i.setCategory(c);
                }
            }
            s.getTransaction().commit();
            return Response.ok(ItemDto.of(i)).build();
        }
    }

    @DELETE
    @Path("/{id}")
    public Response delete(@PathParam("id") long id) {
        try (Session s = Hibernate.open()) {
            s.beginTransaction();
            Item i = s.find(Item.class, id);
            if (i == null) {
                s.getTransaction().rollback();
                return Response.status(Response.Status.NOT_FOUND).build();
            }
            s.remove(i);
            s.getTransaction().commit();
            return Response.noContent().build();
        }
    }
}
