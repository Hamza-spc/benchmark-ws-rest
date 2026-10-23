package ma.bench.varianta.json;

import java.math.BigDecimal;

public record ItemInput(String sku, String name, BigDecimal price, Integer stock, Long categoryId) {
}
