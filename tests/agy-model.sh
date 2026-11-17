#!/bin/bash
# The model allpapers-search names for --gemini-backend agy is the one it passed to agy, on success
# and on failure. A failed agy run used to be headed with GEMINI_MODEL, the API backend's default,
# whatever ALLPAPERS_AGY_MODEL was. agy is replaced by tests/stub-agy/agy, so no search runs.
# Usage: tests/agy-model.sh   (exit 0 when every case passes)
here=$(dirname "$(realpath "$0")")
search=$here/../scripts/allpapers-search
export PATH=$here/stub-agy:$PATH
fails=0

# expect <case> <text> <output>: the output holds the text.
expect() {
  if [[ $3 == *"$2"* ]]; then
    echo "ok   $1: $2"
  else
    echo "FAIL $1: no \"$2\" in:"$'\n'"$3"
    fails=$((fails + 1))
  fi
}

run() { "$search" --gemini-only --gemini-backend agy "$@" "a query" 2>&1; }

out=$(ALLPAPERS_AGY_MODEL=other-model run)
expect "other model, success" "--- Gemini grounded web search (other-model) ---" "$out"
expect "other model, success" "Stub answer from model other-model" "$out"

out=$(ALLPAPERS_AGY_MODEL=other-model STUB_AGY_FAIL=1 run)
expect "other model, agy fails" "--- Gemini grounded web search (other-model) ---" "$out"
expect "other model, agy fails" '--model "other-model"' "$out"

out=$(ALLPAPERS_AGY_MODEL=other-model STUB_AGY_FAIL=1 run --json)
expect "other model, agy fails, --json" '"model": "other-model"' "$out"

out=$(env -u ALLPAPERS_AGY_MODEL STUB_AGY_FAIL=1 "$search" --gemini-only --gemini-backend agy "a query" 2>&1)
expect "default model, agy fails" "--- Gemini grounded web search (gemini-4-carbon-medium) ---" "$out"

echo "failed: $fails"
[ "$fails" -eq 0 ]
