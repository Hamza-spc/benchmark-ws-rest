#!/usr/bin/env python3
"""Agrège les fichiers .jtl de JMeter en indicateurs exploitables (tableaux T2, T4, T5).

Sortie :
  - report/results/summary.json  : statistiques par scénario / palier et par endpoint
  - affichage d'un condensé lisible pour remplir les tableaux du TP
"""
import csv
import json
import os
import re
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "report", "results")
SCENARIOS = [("read-heavy", "READ-heavy"), ("join-filter", "JOIN-filter"),
             ("mixed", "MIXED"), ("heavy-body", "HEAVY-body")]
VARIANTS = ["a", "c", "d"]


def percentile(values, pct):
    if not values:
        return 0.0
    data = sorted(values)
    k = max(0, min(len(data) - 1, int(round((pct / 100.0) * (len(data) - 1)))))
    return float(data[k])


def stats(rows):
    if not rows:
        return None
    elapsed = [float(r["elapsed"]) for r in rows]
    start = min(int(r["timeStamp"]) for r in rows)
    end = max(int(r["timeStamp"]) + int(float(r["elapsed"])) for r in rows)
    duration = max((end - start) / 1000.0, 0.001)
    errors = sum(1 for r in rows if r["success"] != "true")
    return {
        "samples": len(rows),
        "duration_s": round(duration, 1),
        "rps": round(len(rows) / duration, 1),
        "avg_ms": round(statistics.fmean(elapsed), 1),
        "p50_ms": round(percentile(elapsed, 50), 1),
        "p95_ms": round(percentile(elapsed, 95), 1),
        "p99_ms": round(percentile(elapsed, 99), 1),
        "err_pct": round(100.0 * errors / len(rows), 2),
        "errors": errors,
    }


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    summary = {"scenarios": {}, "endpoints": {}, "errors": []}
    for scenario, label in SCENARIOS:
        per_variant = {}
        for variant in VARIANTS:
            path = os.path.join(RESULTS, "%s-%s.jtl" % (scenario, variant))
            if not os.path.exists(path):
                continue
            rows = load(path)
            tiers = {}
            for row in rows:
                tier = re.sub(r"\s+\d+-\d+$", "", row["threadName"])
                tiers.setdefault(tier, []).append(row)
            per_variant[variant.upper()] = {
                "global": stats(rows),
                "paliers": {name: stats(sub) for name, sub in sorted(tiers.items())},
            }
            # endpoints : agrégation par label sur l'ensemble des paliers
            by_label = {}
            for row in rows:
                by_label.setdefault(row["label"], []).append(row)
            for name, sub in by_label.items():
                summary["endpoints"].setdefault(name, {})[variant.upper()] = stats(sub)
            # erreurs : on conserve les codes HTTP en échec
            codes = {}
            for row in rows:
                if row["success"] != "true":
                    key = (row["responseCode"], row["responseMessage"])
                    codes[key] = codes.get(key, 0) + 1
            for (code, message), count in codes.items():
                summary["errors"].append({
                    "scenario": label, "variant": variant.upper(),
                    "http": code, "message": message, "count": count,
                    "pct": round(100.0 * count / len(rows), 2),
                })
        summary["scenarios"][label] = per_variant

    out = os.path.join(RESULTS, "summary.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print("écrit", out)

    for label, per_variant in summary["scenarios"].items():
        print("\n== %s" % label)
        for variant, data in per_variant.items():
            g = data["global"]
            print("  %s : %6.1f req/s  p50 %6.1f  p95 %7.1f  p99 %7.1f  err %5.2f%%  (%d éch.)"
                  % (variant, g["rps"], g["p50_ms"], g["p95_ms"], g["p99_ms"], g["err_pct"], g["errors"]))
            for tier, s in data["paliers"].items():
                print("      %-22s %6.1f req/s  p95 %7.1f  err %5.2f%%"
                      % (tier, s["rps"], s["p95_ms"], s["err_pct"]))
    if summary["errors"]:
        print("\n== erreurs")
        for e in summary["errors"]:
            print("  %-10s %s %s %s : %d (%.2f%%)"
                  % (e["scenario"], e["variant"], e["http"], e["message"], e["count"], e["pct"]))


if __name__ == "__main__":
    main()
