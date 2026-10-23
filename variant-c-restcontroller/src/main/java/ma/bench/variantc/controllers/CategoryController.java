package ma.bench.variantc.controllers;

import ma.bench.variantc.dto.CategoryDto;
import ma.bench.variantc.dto.CategoryInput;
import ma.bench.variantc.dto.ItemDto;
import ma.bench.variantc.dto.PageResponse;
import ma.bench.variantc.entities.Category;
import ma.bench.variantc.repositories.CategoryRepository;
import ma.bench.variantc.repositories.ItemRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/categories")
public class CategoryController {

    private final CategoryRepository categories;
    private final ItemRepository items;

    public CategoryController(CategoryRepository categories, ItemRepository items) {
        this.categories = categories;
        this.items = items;
    }

    @GetMapping
    public PageResponse<CategoryDto> list(@RequestParam(defaultValue = "0") int page,
                                          @RequestParam(defaultValue = "50") int size) {
        return PageResponse.of(categories.findAll(PageRequest.of(page, size)), CategoryDto::of);
    }

    @GetMapping("/{id}")
    public ResponseEntity<CategoryDto> get(@PathVariable long id) {
        return categories.findById(id)
                .map(c -> ResponseEntity.ok(CategoryDto.of(c)))
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<CategoryDto> create(@RequestBody CategoryInput in) {
        Category c = new Category();
        c.setCode(in.code());
        c.setName(in.name());
        categories.save(c);
        return ResponseEntity.ok(CategoryDto.of(c));
    }

    @PutMapping("/{id}")
    public ResponseEntity<CategoryDto> update(@PathVariable long id, @RequestBody CategoryInput in) {
        return categories.findById(id)
                .map(c -> {
                    c.setCode(in.code());
                    c.setName(in.name());
                    categories.save(c);
                    return ResponseEntity.ok(CategoryDto.of(c));
                })
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable long id) {
        if (!categories.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        categories.deleteById(id);
        return ResponseEntity.noContent().build();
    }

    /** Association inverse : produits d'une catégorie. */
    @GetMapping("/{id}/items")
    public PageResponse<ItemDto> items(@PathVariable long id,
                                       @RequestParam(defaultValue = "0") int page,
                                       @RequestParam(defaultValue = "50") int size) {
        return PageResponse.of(
                items.findAllWithCategoryByCategoryId(id, PageRequest.of(page, size)), ItemDto::of);
    }
}
