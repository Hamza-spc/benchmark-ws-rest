-- Jeu de données : 2 000 catégories / 100 000 produits
INSERT INTO category (code, name, updated_at)
SELECT 'CAT' || g, 'Category ' || g, NOW()
FROM generate_series(1, 2000) g;

INSERT INTO item (sku, name, price, stock, category_id, updated_at)
SELECT 'SKU' || g,
       'Item ' || g,
       ROUND((RANDOM() * 990 + 10)::numeric, 2),
       (RANDOM() * 500)::int,
       1 + (RANDOM() * 1999)::int,
       NOW() - ((RANDOM() * 365)::int || ' days')::interval
FROM generate_series(1, 100000) g;

ANALYZE category;
ANALYZE item;
