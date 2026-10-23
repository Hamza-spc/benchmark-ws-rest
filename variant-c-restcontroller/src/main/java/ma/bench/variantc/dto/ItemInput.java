package ma.bench.variantc.dto;

import java.math.BigDecimal;

public record ItemInput(String sku, String name, BigDecimal price, Integer stock, Long categoryId) {
}
