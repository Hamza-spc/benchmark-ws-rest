package ma.bench.variantc.dto;

import org.springframework.data.domain.Page;

import java.util.List;
import java.util.function.Function;

/** Enveloppe de pagination commune aux variantes A et C. */
public record PageResponse<T>(List<T> content, int page, int size, long total, int totalPages) {

    public static <E, T> PageResponse<T> of(Page<E> page, Function<E, T> mapper) {
        return new PageResponse<>(page.getContent().stream().map(mapper).toList(),
                page.getNumber(), page.getSize(), page.getTotalElements(), page.getTotalPages());
    }
}
