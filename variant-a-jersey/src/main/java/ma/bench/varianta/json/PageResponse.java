package ma.bench.varianta.json;

import java.util.List;

/** Enveloppe de pagination commune aux variantes A et C. */
public record PageResponse<T>(List<T> content, int page, int size, long total, int totalPages) {

    public static <T> PageResponse<T> of(List<T> content, int page, int size, long total) {
        int totalPages = size > 0 ? (int) Math.ceil((double) total / size) : 0;
        return new PageResponse<>(content, page, size, total, totalPages);
    }
}
