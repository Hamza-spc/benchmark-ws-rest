#!/usr/bin/env python3
"""Échantillonne les ressources des trois variantes pendant les runs JMeter (tableau T3).

Sortie : report/results/metrics.csv (une ligne par échantillon et par variante).
Mesures : CPU % (ps), RSS (ps), tas utilisé (jstat), temps GC cumulé (jstat),
threads actifs / connexions Hikari actives (actuator Prometheus, variantes C et D).
"""
import json
import os
import re
import subprocess
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "report", "results", "metrics.csv")
JSTAT = "/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home/bin/jstat"
PORTS = {"A": 8081, "C": 8082, "D": 8083}
INTERVAL = 3.0


PATTERNS = {
    "A": "ma.bench.varianta.VariantAApp",
    "C": "variant-c-restcontroller.jar",
    "D": "variant-d-spring-data-rest.jar",
}


def pids():
    """PID des JVM Java (et non des shells qui les ont lancées)."""
    out = subprocess.run(["ps", "-Ao", "pid=,comm=,args="], capture_output=True, text=True, check=False).stdout
    found = {}
    for line in out.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 3 or not parts[2].split()[0].endswith("/java"):
            continue
        for variant, pattern in PATTERNS.items():
            if pattern in parts[2] and variant not in found:
                found[variant] = int(parts[0])
    return found


def ps_usage(pid):
    out = subprocess.run(["ps", "-o", "%cpu=,rss=", "-p", str(pid)],
                         capture_output=True, text=True, check=False).stdout.split()
    if len(out) < 2:
        return None, None
    return float(out[0]), int(out[1]) / 1024.0


def jstat_heap(pid):
    out = subprocess.run([JSTAT, "-gc", str(pid)], capture_output=True, text=True, check=False).stdout.splitlines()
    if len(out) < 2:
        return None, None
    head, row = out[0].split(), out[1].split()
    values = dict(zip(head, row))
    used = sum(float(values[k]) for k in ("S0U", "S1U", "EU", "OU") if k in values) / 1024.0
    gc_time = float(values.get("GCT", 0))
    return used, gc_time


def prometheus(port):
    try:
        raw = urllib.request.urlopen("http://localhost:%d/actuator/prometheus" % port, timeout=2).read().decode()
    except Exception:
        return {}
    wanted = {
        "process_cpu_usage": "cpu",
        "jvm_threads_live_threads": "threads",
        "hikaricp_connections_active": "hikari_active",
        "hikaricp_connections_max": "hikari_max",
    }
    result = {}
    for line in raw.splitlines():
        if line.startswith("#"):
            continue
        for metric, key in wanted.items():
            if line.startswith(metric + "{"):
                try:
                    result.setdefault(key, float(line.rsplit(" ", 1)[1]))
                except ValueError:
                    pass
    return result


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    columns = ["ts", "variant", "cpu_pct", "rss_mb", "heap_mb", "gc_time_s", "threads",
               "hikari_active", "hikari_max", "cpu_actuator"]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(",".join(columns) + "\n")
        while not os.path.exists(os.path.join(ROOT, "report", "results", ".stop-monitor")):
            table = pids()
            for variant, pid in table.items():
                cpu, rss = ps_usage(pid)
                heap, gc_time = jstat_heap(pid)
                extra = prometheus(PORTS[variant])
                fh.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                    time.strftime("%Y-%m-%dT%H:%M:%S"), variant,
                    cpu if cpu is not None else "", rss if rss is not None else "",
                    round(heap, 1) if heap is not None else "",
                    gc_time if gc_time is not None else "",
                    extra.get("threads", ""), extra.get("hikari_active", ""), extra.get("hikari_max", ""),
                    extra.get("cpu", "")))
            fh.flush()
            time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
