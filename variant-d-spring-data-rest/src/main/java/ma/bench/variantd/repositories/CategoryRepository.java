package ma.bench.variantd.repositories;

import ma.bench.variantd.entities.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.rest.core.annotation.RepositoryRestResource;

@RepositoryRestResource(collectionResourceRel = "categories", itemResourceRel = "category")
public interface CategoryRepository extends JpaRepository<Category, Long> {
}
