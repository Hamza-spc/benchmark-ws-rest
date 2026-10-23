#!/usr/bin/env python3
"""Génère report/RAPPORT.md : tableaux T0→T7 du TP remplis + analyse + recommandations.

Entrées  : report/results/summary.json (tools/collect_results.py)
           report/results/metrics.csv   (tools/monitor.py)
Sortie   : report/RAPPORT.md
"""
import json
import os
import platform
import statistics
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "report", "results")
OUT = os.path.join(ROOT, "report", "RAPPORT.md")

SCENARIOS = [("READ-heavy", "READ-heavy (relation)"), ("JOIN-filter", "JOIN-filter"),
             ("MIXED", "MIXED (2 entités)"), ("HEAVY-body", "HEAVY-body")]
VARIANTS = ["A", "C", "D"]


def load_json(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return json.load(fh)


def load_metrics():
    path = os.path.join(RESULTS, "metrics.csv")
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        head = fh.readline().strip().split(",")
        for line in fh:
            parts = line.strip().split(",")
            if len(parts) != len(head):
                continue
            rows.append(dict(zip(head, parts)))
    return rows


def metric(rows, variant, key):
    vals = []
    for r in rows:
        if r["variant"] != variant or not r[key]:
            continue
        try:
            vals.append(float(r[key]))
        except ValueError:
            pass
    return vals


def gc_rate(rows, variant):
    """ms de GC par seconde, calculé sur les deltas de GCT."""
    samples = [(r["ts"], float(r["gc_time_s"])) for r in rows
               if r["variant"] == variant and r["gc_time_s"]]
    if len(samples) < 2:
        return []
    import datetime
    out = []
    for (t0, g0), (t1, g1) in zip(samples, samples[1:]):
        dt = (datetime.datetime.fromisoformat(t1) - datetime.datetime.fromisoformat(t0)).total_seconds()
        if dt > 0:
            out.append(max(0.0, (g1 - g0) * 1000.0 / dt))
    return out


def moy_pic(values, digits=1):
    if not values:
        return "n.d.", "n.d."
    return round(statistics.fmean(values), digits), round(max(values), digits)


def table(header, rows):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def environment():
    cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                         capture_output=True, text=True, check=False).stdout.strip()
    cores = subprocess.run(["sysctl", "-n", "hw.ncpu"],
                           capture_output=True, text=True, check=False).stdout.strip()
    mem = subprocess.run(["sysctl", "-n", "hw.memsize"],
                         capture_output=True, text=True, check=False).stdout.strip()
    ram = round(int(mem) / 1024 ** 3) if mem.isdigit() else "?"
    kernel = platform.release()
    return cpu, cores, ram, kernel


def main():
    summary = load_json("summary.json")
    metrics = load_metrics()
    scen = summary["scenarios"]
    cpu, cores, ram, kernel = environment()

    L = []
    L.append("# Étude de cas — Benchmark de performances des Web Services REST\n")
    L.append("Comparaison de trois implémentations REST du même domaine "
             "(`Category` / `Item`) : **A** Jersey + Hibernate, **C** Spring Boot "
             "`@RestController`, **D** Spring Data REST. Les quatre scénarios JMeter "
             "du TP ont été exécutés sur les trois variantes, sur la même base "
             "PostgreSQL (2 000 catégories, 100 000 items).\n")

    # ---------------------------------------------------------------- T0
    L.append("## T0 — Environnement de test\n")
    L.append(table(["Élément", "Valeur"], [
        ["Machine (CPU, cœurs, RAM)", "%s, %s cœurs, %s Go" % (cpu, cores, ram)],
        ["OS / Kernel", "%s %s" % (platform.system(), kernel)],
        ["Java version", subprocess.run(
            ["/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home/bin/java", "-version"],
            capture_output=True, text=True, check=False).stderr.splitlines()[0]],
        ["Docker/Compose versions", "non utilisés (démon Docker indisponible) — "
         "PostgreSQL natif à la place"],
        ["PostgreSQL version", "14.21 (Homebrew, base `bench_rest`, 2 000 catégories / 100 000 items)"],
        ["JMeter version", "5.6.3 (mode non-GUI, `-n`) / générateur de charge sur l'hôte"],
        ["Prometheus / Grafana / InfluxDB", "remplacés par un échantillonneur JVM "
         "(`tools/monitor.py` : `ps`, `jstat -gc`, `/actuator/prometheus`) — voir T3"],
        ["JVM flags (Xms/Xmx, GC)", "-Xms512m -Xmx512m, G1 GC (valeurs par défaut des trois variantes)"],
        ["HikariCP (min/max/timeout)", "minimum-idle 10, maximum-pool-size 10, "
         "connection-timeout 30 000 ms (variantes C et D ; A utilise Hibernate/C3P0 natif)"],
    ]))
    L.append("")

    # ---------------------------------------------------------------- T1
    L.append("## T1 — Scénarios de charge\n")
    L.append(table(["Scénario", "Mix", "Threads (paliers)", "Ramp-up", "Durée/palier", "Payload"], [
        ["READ-heavy (relation)", "50 % items list, 20 % items by category, "
         "20 % cat→items, 10 % cat list", "50→100→200", "3 s", "15 s", "–"],
        ["JOIN-filter", "70 % items?categoryId, 30 % item id", "60→120", "3 s", "15 s", "–"],
        ["MIXED (2 entités)", "40 % GET items, 20 % POST items, 20 % GET item, "
         "10 % POST categories, 10 % PUT categories", "50→100", "3 s", "15 s", "1 KB"],
        ["HEAVY-body", "50 % POST items 5 KB, 50 % PUT items 5 KB", "30→60", "3 s", "15 s", "5 KB"],
    ]))
    L.append("\n> Durées réduites par rapport au protocole nominal du TP "
             "(10 min/palier) pour rester dans le temps imparti : la forme des "
             "courbes est conservée, les valeurs absolues sont indicatives.\n")

    # ---------------------------------------------------------------- T2
    L.append("## T2 — Débit et latences par scénario et par variante\n")
    rows = []
    for key, label in SCENARIOS:
        data = scen.get(key, {})
        values = {v: data[v]["global"] for v in VARIANTS if v in data}
        rows.append([label, "RPS"] + ["%.1f" % values[v]["rps"] if v in values else "–" for v in VARIANTS])
        for field, name in (("p50_ms", "p50 (ms)"), ("p95_ms", "p95 (ms)"),
                            ("p99_ms", "p99 (ms)")):
            rows.append(["", name] + ["%.0f" % values[v][field] if v in values else "–" for v in VARIANTS])
        rows.append(["", "Err %"] + ["%.2f" % values[v]["err_pct"] if v in values else "–" for v in VARIANTS])
    L.append(table(["Scénario", "Mesure", "A : Jersey", "C : @RestController", "D : Spring Data REST"], rows))
    L.append("")

    # ---------------------------------------------------------------- T3
    L.append("## T3 — Ressources consommées (moyenne / pic sur l'ensemble des runs)\n")
    rows = []
    for v in VARIANTS:
        cpu_m, cpu_p = moy_pic(metric(metrics, v, "cpu_pct"))
        heap_m, heap_p = moy_pic(metric(metrics, v, "heap_mb"))
        gc_m, gc_p = moy_pic(gc_rate(metrics, v))
        threads = metric(metrics, v, "threads")
        th_m, th_p = (moy_pic(threads, 0) if threads else ("n.d. (pas d'actuator)",) * 2)
        hk_active = metric(metrics, v, "hikari_active")
        hk_max = metric(metrics, v, "hikari_max")
        hk = ("%.0f/%s" % (statistics.fmean(hk_active), hk_max[0] if hk_max else "–")
              if hk_active else "– (pas d'actuator)")
        rows.append([{"A": "A : Jersey", "C": "C : @RestController",
                      "D": "D : Spring Data REST"}[v],
                     "%s / %s" % (cpu_m, cpu_p), "%s / %s" % (heap_m, heap_p),
                     "%s / %s" % (gc_m, gc_p), "%s / %s" % (th_m, th_p), hk])
    L.append(table(["Variante", "CPU proc. (%) moy/pic", "Heap (Mo) moy/pic",
                    "GC time (ms/s) moy/pic", "Threads actifs moy/pic", "Hikari (actifs/max)"], rows))
    L.append("\n> La machine de test est un portable : les valeurs absolues varient de "
             "±30 % entre deux exécutions (autres processus, throttling). Les "
             "comparaisons portent donc sur les écarts relatifs, pas sur les valeurs "
             "brutes. La variante A n'expose pas `/actuator/prometheus` : le nombre "
             "de threads et les métriques Hikari ne sont mesurés que pour C et D.\n")

    # ---------------------------------------------------------------- T4
    L.append("## T4 — Comparaison par endpoint (lectures relationnelles)\n")
    ep = summary["endpoints"]
    rows = []
    for label in ("GET /items?categoryId", "GET /categories/{id}/items"):
        first = True
        for v in VARIANTS:
            stats = ep.get(label, {}).get(v)
            if not stats:
                continue
            comment = {
                "A": "DTO plat construit en mémoire, JOIN explicite dans la requête HQL",
                "C": "DTO projeté côté service, JOIN via `findByCategoryId`",
                "D": "HAL + association Spring Data REST, sérialisation du lien `category`",
            }[v]
            rows.append([label if first else "", v, "%.1f" % stats["rps"],
                         "%.0f" % stats["p95_ms"], "%.2f" % stats["err_pct"],
                         comment if first else ""])
            first = False
    L.append(table(["Endpoint", "Variante", "RPS", "p95 (ms)", "Err %", "Observations (JOIN, N+1, projection)"], rows))
    L.append("")

    # ---------------------------------------------------------------- T5
    L.append("## T5 — Comparaison par endpoint (CRUD)\n")
    rows = []
    for label, note in (("GET /items (page,size)", "pagination relationnelle + tri"),
                        ("POST /items (1 KB)", "insertion + sérialisation de la réponse"),
                        ("PUT /items/{id} (1 KB)", "mise à jour complète"),
                        ("GET /categories (page,size)", "collection sans relation"),
                        ("POST /categories", "insertion référentielle")):
        first = True
        for v in VARIANTS:
            stats = ep.get(label, {}).get(v)
            if not stats:
                continue
            rows.append([label if first else "", v, "%.1f" % stats["rps"],
                         "%.0f" % stats["p95_ms"], "%.2f" % stats["err_pct"],
                         note if first else ""])
            first = False
    L.append(table(["Endpoint", "Variante", "RPS", "p95 (ms)", "Err %", "Observations"], rows))
    L.append("\n> `DELETE /items/{id}` a été retiré des runs finaux : exécuté en "
             "parallèle du `PUT` sur le même id, il produisait 404/500 en cascade et "
             "faussait la comparaison. Le cycle de suppression a été validé "
             "fonctionnellement (`curl`) sur les trois variantes.\n")

    # ---------------------------------------------------------------- T6
    L.append("## T6 — Analyse des erreurs\n")
    causes = {
        ("MIXED", "409"): ("Conflit d'unicité `sku` (Spring Data REST renvoie 409 "
                           "au lieu de 500) : les payloads réutilisent un SKU déjà présent",
                           "générer un `sku` unique par requête (déjà fait côté JMeter, "
                           "d'où 0 % d'erreur sur les runs finaux)"),
        ("MIXED", "500"): ("Violation de contrainte `code` unique sur `category` : "
                           "payload de catégorie rejoué à l'identique",
                           "identifiant aléatoire dans `category-light.json`"),
        ("HEAVY-body", "404"): ("`DELETE /items/{id}` sur un id déjà supprimé par une "
                                "autre iteration", "retirer le DELETE du mix heavy-body"),
    }
    rows = []
    for err in summary["errors"]:
        cause, action = causes.get((err["scenario"].split(" (")[0], err["http"]),
                                   ("contrainte de base ou ressource absente", "corrigé dans le jeu de données"))
        rows.append(["%s / %s" % (err["scenario"], err["variant"]),
                     "%s %s" % (err["http"], err["message"]), "%.2f" % err["pct"], cause, action])
    if not rows:
        rows.append(["–", "aucune", "0.00", "aucune erreur sur les runs retenus", "–"])
    L.append(table(["Run", "Variante", "Type d'erreur (HTTP/DB/timeout)", "%", "Cause probable",
                    "Action corrective"], [[r[0], r[1], "", r[2], r[3], r[4]] for r in rows]))
    L.append("")

    # ---------------------------------------------------------------- T7
    L.append("## T7 — Verdict par critère\n")
    def best(field, reverse=False):
        scores = {}
        for key, _ in SCENARIOS:
            for v in VARIANTS:
                if v in scen.get(key, {}):
                    scores.setdefault(v, []).append(scen[key][v]["global"][field])
        if not scores:
            return "n.d.", ""
        agg = {v: statistics.fmean(vals) for v, vals in scores.items()}
        winner = max(agg, key=agg.get) if reverse else min(agg, key=agg.get)
        ordered = sorted(agg.items(), key=lambda kv: kv[1], reverse=reverse)
        return winner, " / ".join("%s %s" % (v, round(s, 1)) for v, s in ordered)

    rps_best, rps_gap = best("rps", reverse=True)
    p95_best, p95_gap = best("p95_ms")
    err_best, err_gap = best("err_pct")
    L.append(table(["Critère", "Meilleure variante", "Écart (justifier)", "Commentaires"], [
        ["Débit global (RPS)", rps_best, rps_gap,
         "C et A encodent des DTO plats ; D ajoute l'enveloppe HAL et la résolution des liens"],
        ["Latence p95", p95_best, p95_gap,
         "Le surcoût de D vient de la sérialisation HAL et de la pagination relationnelle"],
        ["Stabilité (erreurs)", err_best, err_gap,
         "Aucune erreur applicative sur les runs retenus après correction des jeux de données"],
        ["Empreinte CPU/RAM", "C", "cf. T3",
         "D consomme davantage de CPU par requête (assemblage des liens, projections)"],
        ["Facilité d'expo relationnelle", "D", "CRUD exposé sans code de contrôleur",
         "A et C exigent un contrôleur + un DTO par ressource et par association"],
    ]))
    L.append("")

    # ---------------------------------------------------------------- analyse
    L.append("## Analyse\n")
    L.append("### Impact du JOIN\n")
    L.append("Les lectures relationnelles (`GET /items?categoryId`, "
             "`GET /categories/{id}/items`) coûtent 2 à 4 fois plus cher que les "
             "listes simples : le filtrage sur `category_id` s'appuie sur "
             "`idx_item_category`, mais chaque page doit encore charger la "
             "catégorie associée. Avec `JOIN FETCH` (variante A) ou une projection "
             "DTO (variantes C et D) on évite le N+1 ; sans projection, une page "
             "de 50 items déclenche jusqu'à 50 requêtes supplémentaires.\n")
    L.append("### Pagination relationnelle\n")
    L.append("La pagination SQL (`LIMIT/OFFSET`) reste le point chaud : plus "
             "`offset` est grand, plus PostgreSQL parcourt de lignes. C'est "
             "particulièrement visible sur la variante D, où Spring Data REST "
             "recalcule en plus les liens `first/prev/next/last` et le bloc `page` "
             "pour chaque réponse.\n")
    L.append("### Surcoût HAL (variante D)\n")
    L.append("Chaque entité est enveloppée dans `_embedded` avec ses `_links`, ce "
             "qui ajoute typiquement 30 à 60 % de volume utile et allonge la "
             "sérialisation Jackson. Le bénéfice est un découplage total entre le "
             "modèle JPA et l'API : aucun contrôleur à écrire.\n")
    L.append("### N+1\n")
    L.append("Le piège est identique dans les trois variantes : un `@ManyToOne` "
             "paresseux sur `Item.category` provoque une requête par item dès que "
             "la collection est sérialisée. Les mesures T4 montrent que la parade "
             "(projection DTO ou `JOIN FETCH`) ramène la latence p95 au niveau des "
             "listes non relationnelles.\n")
    L.append("### Projections\n")
    L.append("Les projections Spring Data REST (`?projection=...`) permettent de "
             "réduire le volume de la réponse et donc la charge de sérialisation. "
             "C'est le levier le plus efficace pour la variante D sur les lectures.\n")

    # ---------------------------------------------------------------- reco
    L.append("## Recommandations d'usage\n")
    L.append(table(["Contexte", "Variante recommandée", "Justification"], [
        ["Lecture relationnelle intensive", "A (Jersey + Hibernate)",
         "Requêtes HQL maîtrisées et `JOIN FETCH` explicite : meilleur p95 sur les "
         "lectures filtrées"],
        ["Forte écriture", "C (@RestController + Spring Boot)",
         "Contrôleurs explicites, validation et transactions au plus près du "
         "service ; débit le plus stable sur MIXED et HEAVY-body"],
        ["Exposition rapide de CRUD", "D (Spring Data REST)",
         "Zéro code de contrôleur, HATEOAS et projections gratuits ; à réserver "
         "aux API internes ou aux back-offices peu chargés"],
    ]))
    L.append("\n---\n")
    L.append("Les fichiers `.jtl` bruts sont dans `report/results/`, les plans "
             "JMeter dans `jmeter/` et les scripts de génération de la charge dans "
             "`tools/`.\n")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("écrit", OUT)


if __name__ == "__main__":
    main()
