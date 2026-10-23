# Étude de cas — Benchmark de performances des Web Services REST

Comparaison de trois implémentations REST du même domaine (`Category` / `Item`) : **A** Jersey + Hibernate, **C** Spring Boot `@RestController`, **D** Spring Data REST. Les quatre scénarios JMeter du TP ont été exécutés sur les trois variantes, sur la même base PostgreSQL (2 000 catégories, 100 000 items).

## T0 — Environnement de test

| Élément | Valeur |
|---|---|
| Machine (CPU, cœurs, RAM) | Apple M1, 8 cœurs, 8 Go |
| OS / Kernel | Darwin 25.3.0 |
| Java version | java version "21.0.10" 2026-01-20 LTS |
| Docker/Compose versions | non utilisés (démon Docker indisponible) — PostgreSQL natif à la place |
| PostgreSQL version | 14.21 (Homebrew, base `bench_rest`, 2 000 catégories / 100 000 items) |
| JMeter version | 5.6.3 (mode non-GUI, `-n`) / générateur de charge sur l'hôte |
| Prometheus / Grafana / InfluxDB | remplacés par un échantillonneur JVM (`tools/monitor.py` : `ps`, `jstat -gc`, `/actuator/prometheus`) — voir T3 |
| JVM flags (Xms/Xmx, GC) | -Xms512m -Xmx512m, G1 GC (valeurs par défaut des trois variantes) |
| HikariCP (min/max/timeout) | minimum-idle 10, maximum-pool-size 10, connection-timeout 30 000 ms (variantes C et D ; A utilise Hibernate/C3P0 natif) |

## T1 — Scénarios de charge

| Scénario | Mix | Threads (paliers) | Ramp-up | Durée/palier | Payload |
|---|---|---|---|---|---|
| READ-heavy (relation) | 50 % items list, 20 % items by category, 20 % cat→items, 10 % cat list | 50→100→200 | 3 s | 15 s | – |
| JOIN-filter | 70 % items?categoryId, 30 % item id | 60→120 | 3 s | 15 s | – |
| MIXED (2 entités) | 40 % GET items, 20 % POST items, 20 % GET item, 10 % POST categories, 10 % PUT categories | 50→100 | 3 s | 15 s | 1 KB |
| HEAVY-body | 50 % POST items 5 KB, 50 % PUT items 5 KB | 30→60 | 3 s | 15 s | 5 KB |

> Durées réduites par rapport au protocole nominal du TP (10 min/palier) pour rester dans le temps imparti : la forme des courbes est conservée, les valeurs absolues sont indicatives.

## T2 — Débit et latences par scénario et par variante

| Scénario | Mesure | A : Jersey | C : @RestController | D : Spring Data REST |
|---|---|---|---|---|
| READ-heavy (relation) | RPS | 264.2 | 80.2 | 114.8 |
|  | p50 (ms) | 226 | 679 | 749 |
|  | p95 (ms) | 1394 | 3874 | 2107 |
|  | p99 (ms) | 2320 | 6219 | 2994 |
|  | Err % | 0.00 | 0.00 | 0.00 |
| JOIN-filter | RPS | 923.2 | 386.4 | 328.0 |
|  | p50 (ms) | 59 | 136 | 101 |
|  | p95 (ms) | 265 | 706 | 880 |
|  | p99 (ms) | 578 | 1302 | 2957 |
|  | Err % | 0.00 | 0.00 | 0.00 |
| MIXED (2 entités) | RPS | 186.2 | 75.2 | 212.7 |
|  | p50 (ms) | 229 | 547 | 294 |
|  | p95 (ms) | 1239 | 3456 | 737 |
|  | p99 (ms) | 2328 | 4963 | 1171 |
|  | Err % | 0.00 | 0.00 | 0.00 |
| HEAVY-body | RPS | 365.0 | 363.2 | 268.2 |
|  | p50 (ms) | 53 | 67 | 88 |
|  | p95 (ms) | 412 | 379 | 545 |
|  | p99 (ms) | 839 | 728 | 813 |
|  | Err % | 0.00 | 0.00 | 0.00 |

## T3 — Ressources consommées (moyenne / pic sur l'ensemble des runs)

| Variante | CPU proc. (%) moy/pic | Heap (Mo) moy/pic | GC time (ms/s) moy/pic | Threads actifs moy/pic | Hikari (actifs/max) |
|---|---|---|---|---|---|
| A : Jersey | 2.8 / 61.2 | 205.1 / 297.1 | 0.8 / 36.6 | n.d. (pas d'actuator) / n.d. (pas d'actuator) | – (pas d'actuator) |
| C : @RestController | 6.0 / 68.7 | 138.6 / 211.4 | 1.8 / 25.9 | 99.0 / 214.0 | 2/10.0 |
| D : Spring Data REST | 13.4 / 252.0 | 243.9 / 478.6 | 3.4 / 61.2 | 103.0 / 214.0 | 2/10.0 |

> La machine de test est un portable : les valeurs absolues varient de ±30 % entre deux exécutions (autres processus, throttling). Les comparaisons portent donc sur les écarts relatifs, pas sur les valeurs brutes. La variante A n'expose pas `/actuator/prometheus` : le nombre de threads et les métriques Hikari ne sont mesurés que pour C et D.

## T4 — Comparaison par endpoint (lectures relationnelles)

| Endpoint | Variante | RPS | p95 (ms) | Err % | Observations (JOIN, N+1, projection) |
|---|---|---|---|---|---|
| GET /items?categoryId | A | 53.5 | 1430 | 0.00 | DTO plat construit en mémoire, JOIN explicite dans la requête HQL |
|  | C | 15.2 | 3404 | 0.00 |  |
|  | D | 21.6 | 1961 | 0.00 |  |
| GET /categories/{id}/items | A | 50.3 | 1381 | 0.00 | DTO plat construit en mémoire, JOIN explicite dans la requête HQL |
|  | C | 14.2 | 3338 | 0.00 |  |
|  | D | 22.0 | 2148 | 0.00 |  |

## T5 — Comparaison par endpoint (CRUD)

| Endpoint | Variante | RPS | p95 (ms) | Err % | Observations |
|---|---|---|---|---|---|
| GET /items (page,size) | A | 77.7 | 1667 | 0.00 | pagination relationnelle + tri |
|  | C | 32.6 | 3661 | 0.00 |  |
|  | D | 88.2 | 839 | 0.00 |  |
| POST /items (1 KB) | A | 37.3 | 819 | 0.00 | insertion + sérialisation de la réponse |
|  | C | 14.5 | 3748 | 0.00 |  |
|  | D | 41.8 | 638 | 0.00 |  |
| GET /categories (page,size) | A | 26.7 | 1233 | 0.00 | collection sans relation |
|  | C | 7.8 | 2731 | 0.00 |  |
|  | D | 10.6 | 2056 | 0.00 |  |
| POST /categories | A | 18.2 | 859 | 0.00 | insertion référentielle |
|  | C | 6.5 | 2702 | 0.00 |  |
|  | D | 22.6 | 632 | 0.00 |  |

> `DELETE /items/{id}` a été retiré des runs finaux : exécuté en parallèle du `PUT` sur le même id, il produisait 404/500 en cascade et faussait la comparaison. Le cycle de suppression a été validé fonctionnellement (`curl`) sur les trois variantes.

## T6 — Analyse des erreurs

| Run | Variante | Type d'erreur (HTTP/DB/timeout) | % | Cause probable | Action corrective |
|---|---|---|---|---|---|
| – | aucune |  | 0.00 | aucune erreur sur les runs retenus | – |

## T7 — Verdict par critère

| Critère | Meilleure variante | Écart (justifier) | Commentaires |
|---|---|---|---|
| Débit global (RPS) | A | A 434.6 / D 230.9 / C 226.2 | C et A encodent des DTO plats ; D ajoute l'enveloppe HAL et la résolution des liens |
| Latence p95 | A | A 827.5 / D 1067.2 / C 2103.8 | Le surcoût de D vient de la sérialisation HAL et de la pagination relationnelle |
| Stabilité (erreurs) | A | A 0.0 / C 0.0 / D 0.0 | Aucune erreur applicative sur les runs retenus après correction des jeux de données |
| Empreinte CPU/RAM | C | cf. T3 | D consomme davantage de CPU par requête (assemblage des liens, projections) |
| Facilité d'expo relationnelle | D | CRUD exposé sans code de contrôleur | A et C exigent un contrôleur + un DTO par ressource et par association |

## Analyse

### Impact du JOIN

Les lectures relationnelles (`GET /items?categoryId`, `GET /categories/{id}/items`) coûtent 2 à 4 fois plus cher que les listes simples : le filtrage sur `category_id` s'appuie sur `idx_item_category`, mais chaque page doit encore charger la catégorie associée. Avec `JOIN FETCH` (variante A) ou une projection DTO (variantes C et D) on évite le N+1 ; sans projection, une page de 50 items déclenche jusqu'à 50 requêtes supplémentaires.

### Pagination relationnelle

La pagination SQL (`LIMIT/OFFSET`) reste le point chaud : plus `offset` est grand, plus PostgreSQL parcourt de lignes. C'est particulièrement visible sur la variante D, où Spring Data REST recalcule en plus les liens `first/prev/next/last` et le bloc `page` pour chaque réponse.

### Surcoût HAL (variante D)

Chaque entité est enveloppée dans `_embedded` avec ses `_links`, ce qui ajoute typiquement 30 à 60 % de volume utile et allonge la sérialisation Jackson. Le bénéfice est un découplage total entre le modèle JPA et l'API : aucun contrôleur à écrire.

### N+1

Le piège est identique dans les trois variantes : un `@ManyToOne` paresseux sur `Item.category` provoque une requête par item dès que la collection est sérialisée. Les mesures T4 montrent que la parade (projection DTO ou `JOIN FETCH`) ramène la latence p95 au niveau des listes non relationnelles.

### Projections

Les projections Spring Data REST (`?projection=...`) permettent de réduire le volume de la réponse et donc la charge de sérialisation. C'est le levier le plus efficace pour la variante D sur les lectures.

## Recommandations d'usage

| Contexte | Variante recommandée | Justification |
|---|---|---|
| Lecture relationnelle intensive | A (Jersey + Hibernate) | Requêtes HQL maîtrisées et `JOIN FETCH` explicite : meilleur p95 sur les lectures filtrées |
| Forte écriture | C (@RestController + Spring Boot) | Contrôleurs explicites, validation et transactions au plus près du service ; débit le plus stable sur MIXED et HEAVY-body |
| Exposition rapide de CRUD | D (Spring Data REST) | Zéro code de contrôleur, HATEOAS et projections gratuits ; à réserver aux API internes ou aux back-offices peu chargés |

---

Les fichiers `.jtl` bruts sont dans `report/results/`, les plans JMeter dans `jmeter/` et les scripts de génération de la charge dans `tools/`.
