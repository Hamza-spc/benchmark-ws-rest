package ma.bench.variantd.repositories;

import ma.bench.variantd.entities.Item;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.data.rest.core.annotation.RepositoryRestResource;
import org.springframework.data.rest.core.annotation.RestResource;

@RepositoryRestResource(collectionResourceRel = "items", itemResourceRel = "item")
public interface ItemRepository extends JpaRepository<Item, Long> {

    /** GET /items/search/byCategory?categoryId=... */
    @RestResource(path = "byCategory")
    Page<Item> findByCategoryId(@Param("categoryId") Long categoryId, Pageable pageable);
}
