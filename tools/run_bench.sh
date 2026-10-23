#!/usr/bin/env bash
# Lance les 4 scénarios JMeter du TP 204 sur une variante REST.
#   usage : tools/run_bench.sh <A|C|D> [C D ...]
# Variables : RAMP (défaut 3) et HOLD (défaut 15) = durée d'un palier en secondes,
#             SCENARIOS (défaut « read-heavy join-filter mixed heavy-body »).
set -eo pipefail

VARIANTS=("$@")
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JMETER="${JMETER:-/opt/homebrew/Cellar/jmeter/5.6.3/bin/jmeter}"
RAMP="${RAMP:-3}"
HOLD="${HOLD:-15}"
OUT="$ROOT/report/results"
mkdir -p "$OUT"

for VARIANT in "${VARIANTS[@]}"; do
case "$VARIANT" in
  A) PORT=8081; OPTS=() ;;
  C) PORT=8082; OPTS=() ;;
  D) PORT=8083
     OPTS=(-JbycatPath=/items/search/byCategory?categoryId=
           -JitemBody=item-light-d.json -JheavyBody=item-heavy-d.json) ;;
  *) echo "variante inconnue : $VARIANT" >&2; exit 1 ;;
esac

common=(-Jport="$PORT" -Jbase="http://localhost:$PORT" -Jramp="$RAMP" -Jhold="$HOLD" "${OPTS[@]}")

# état initial identique pour chaque variante
( cd "$ROOT/db" && psql -q -d bench_rest -f reset.sql >/dev/null )

for scenario in ${SCENARIOS:-read-heavy join-filter mixed heavy-body}; do
  echo ">>> variante $VARIANT / $scenario"
  rm -f "$OUT/$scenario-$(echo "$VARIANT" | tr 'A-Z' 'a-z').jtl"
  "$JMETER" -n -t "$ROOT/jmeter/$scenario.jmx" \
    -l "$OUT/$scenario-$(echo "$VARIANT" | tr 'A-Z' 'a-z').jtl" \
    -j "/tmp/bench/jmeter-$scenario-$(echo "$VARIANT" | tr 'A-Z' 'a-z').log" \
    "${common[@]}" 2>&1 | grep -E '^summary =' || true
done

( cd "$ROOT/db" && psql -q -d bench_rest -f reset.sql >/dev/null )
echo ">>> variante $VARIANT terminée"
done
