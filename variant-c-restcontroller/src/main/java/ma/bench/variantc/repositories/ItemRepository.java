package ma.bench.variantc.repositories;

import ma.bench.variantc.entities.Item;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface ItemRepository extends JpaRepository<Item, Long> {

    /** Anti N+1 : la catégorie est ramenée dans la même requête. */
    @Query(value = "select i from Item i join fetch i.category order by i.id",
            countQuery = "select count(i) from Item i")
    Page<Item> findAllWithCategory(Pageable pageable);

    @Query(value = "select i from Item i join fetch i.category where i.category.id = :cid order by i.id",
            countQuery = "select count(i) from Item i where i.category.id = :cid")
    Page<Item> findAllWithCategoryByCategoryId(@Param("cid") Long categoryId, Pageable pageable);

    @Query("select i from Item i join fetch i.category where i.id = :id")
    Optional<Item> findByIdWithCategory(@Param("id") Long id);
}
