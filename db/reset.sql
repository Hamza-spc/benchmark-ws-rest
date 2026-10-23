-- Remise à l'état initial (après les scénarios d'écriture)
TRUNCATE item RESTART IDENTITY CASCADE;
TRUNCATE category RESTART IDENTITY CASCADE;
\i seed.sql
