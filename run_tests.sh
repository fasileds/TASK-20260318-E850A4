#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PYTHONPATH="$BACKEND_DIR"

echo "== Installing backend test dependencies =="
python -m pip install -r "$BACKEND_DIR/requirements.txt" -r "$BACKEND_DIR/requirements-test.txt"

run_req() {
  local marker="$1"
  local title="$2"
  if PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest "$BACKEND_DIR/tests" -m "$marker" -p no:pytest_asyncio; then
    echo "[PASS] $title"
    RESULTS+=("PASS|$title")
  else
    echo "[FAIL] $title"
    RESULTS+=("FAIL|$title")
    FAILURES=$((FAILURES + 1))
  fi
}

FAILURES=0
RESULTS=()

echo "== Running backend compliance checks =="
run_req "req1_validation" "Applicant Material Validation (.exe reject, size reject, pdf/jpg/png accept)"
run_req "req1_versioning" "Material Versioning keeps latest 3 versions"
run_req "req1_window" "72-hour Supplement Window (71 accept, 73 reject)"
run_req "req1_locks" "Post-deadline Material Lock"

run_req "req2_state_machine" "Reviewer State Machine (Submitted -> Supplemented -> Approved)"
run_req "req2_batch_50" "Reviewer Batch Review (exactly 50)"

run_req "req3_overspending" "Financial Overspending Warning at 110.1%"
run_req "req3_reports" "Report Export Structure (reconciliation/audit/compliance)"

run_req "req4_lockout" "Login Lockout after 10 failures within 5 minutes"
run_req "req4_masking" "Sensitive Data Masking for non-system-admin"
run_req "req4_fingerprint" "SHA-256 Duplicate Submission Blocking"

run_req "req5_metrics" "Quality Metrics (approval/correction/overspending rates)"

echo "== Installing frontend dependencies =="
npm --prefix "$FRONTEND_DIR" install

echo "== Running frontend tests =="
if npm --prefix "$FRONTEND_DIR" run test; then
  echo "[PASS] Frontend test suite"
  RESULTS+=("PASS|Frontend test suite")
else
  echo "[FAIL] Frontend test suite"
  RESULTS+=("FAIL|Frontend test suite")
  FAILURES=$((FAILURES + 1))
fi

echo "== Requirement Report =="
for row in "${RESULTS[@]}"; do
  status="${row%%|*}"
  title="${row#*|}"
  echo "[$status] $title"
done

if [ "$FAILURES" -gt 0 ]; then
  echo "Completed with $FAILURES failing check(s)."
  exit 1
fi

echo "All compliance checks completed successfully."
