package ma.bench.variantc.dto;

import ma.bench.variantc.entities.Item;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record ItemDto(Long id, String sku, String name, BigDecimal price, Integer stock,
                      Long categoryId, String categoryCode, String categoryName,
                      LocalDateTime updatedAt) {

    public static ItemDto of(Item i) {
        return new ItemDto(i.getId(), i.getSku(), i.getName(), i.getPrice(), i.getStock(),
                i.getCategory().getId(), i.getCategory().getCode(), i.getCategory().getName(),
                i.getUpdatedAt());
    }
}
