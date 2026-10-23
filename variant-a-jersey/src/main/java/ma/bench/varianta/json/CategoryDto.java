package ma.bench.varianta.json;

import ma.bench.varianta.entities.Category;

import java.time.LocalDateTime;

public record CategoryDto(Long id, String code, String name, LocalDateTime updatedAt) {

    public static CategoryDto of(Category c) {
        return new CategoryDto(c.getId(), c.getCode(), c.getName(), c.getUpdatedAt());
    }
}
