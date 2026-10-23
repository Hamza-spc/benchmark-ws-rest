package ma.bench.variantc.controllers;

import ma.bench.variantc.dto.ItemDto;
import ma.bench.variantc.dto.ItemInput;
import ma.bench.variantc.dto.PageResponse;
import ma.bench.variantc.entities.Category;
import ma.bench.variantc.entities.Item;
import ma.bench.variantc.repositories.CategoryRepository;
import ma.bench.variantc.repositories.ItemRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/items")
public class ItemController {

    private final ItemRepository items;
    private final CategoryRepository categories;

    public ItemController(ItemRepository items, CategoryRepository categories) {
        this.items = items;
        this.categories = categories;
    }

    @GetMapping
    public PageResponse<ItemDto> list(@RequestParam(defaultValue = "0") int page,
                                      @RequestParam(defaultValue = "50") int size,
                                      @RequestParam(required = false) Long categoryId) {
        PageRequest pageable = PageRequest.of(page, size);
        Page<Item> result = categoryId == null
                ? items.findAllWithCategory(pageable)
                : items.findAllWithCategoryByCategoryId(categoryId, pageable);
        return PageResponse.of(result, ItemDto::of);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ItemDto> get(@PathVariable long id) {
        return items.findByIdWithCategory(id)
                .map(i -> ResponseEntity.ok(ItemDto.of(i)))
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<ItemDto> create(@RequestBody ItemInput in) {
        Category category = categories.findById(in.categoryId()).orElse(null);
        if (category == null) {
            return ResponseEntity.badRequest().build();
        }
        Item item = new Item();
        item.setSku(in.sku());
        item.setName(in.name());
        item.setPrice(in.price());
        item.setStock(in.stock());
        item.setCategory(category);
        items.save(item);
        return ResponseEntity.ok(ItemDto.of(item));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ItemDto> update(@PathVariable long id, @RequestBody ItemInput in) {
        return items.findById(id)
                .map(item -> {
                    item.setSku(in.sku());
                    item.setName(in.name());
                    item.setPrice(in.price());
                    item.setStock(in.stock());
                    if (in.categoryId() != null) {
                        categories.findById(in.categoryId()).ifPresent(item::setCategory);
                    }
                    items.save(item);
                    return ResponseEntity.ok(ItemDto.of(item));
                })
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable long id) {
        if (!items.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        items.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
