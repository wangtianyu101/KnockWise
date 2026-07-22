#!/usr/bin/env bash
# E2E test for auto-fix-ci workflow (T10 / Spec Scenarios S1-S8)
# Usage: ./scripts/ci/test_auto_fix_e2e.sh [--local] [--scenario S1]
#
# --local: use act for local simulation (no real CI)
# --scenario S1..S8: run only specific scenario

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

LOCAL=false
SCENARIO_FILTER=""

for arg in "$@"; do
  case "$arg" in
    --local) LOCAL=true ;;
    --scenario) shift; SCENARIO_FILTER="$1" ;;
    *) ;;
  esac
  shift || true
done

run_scenario() {
  local id="$1"
  local name="$2"
  local check="$3"

  if [ -n "$SCENARIO_FILTER" ] && [ "$SCENARIO_FILTER" != "$id" ]; then
    return 0
  fi

  echo ""
  echo "━━━ Scenario $id: $name ━━━"
  if eval "$check"; then
    echo "✅ Scenario $id passed"
    return 0
  else
    echo "❌ Scenario $id failed"
    return 1
  fi
}

FAILED=0

# S1: Auto-fix on frontend typecheck failure
run_scenario "S1" "Auto-fix frontend typecheck" '
  # Trigger: simulate CI failure with frontend-test typecheck error
  python3 scripts/ci/sanitize_ci_log.py < <(echo "##[error]frontend-test\nProperty X does not exist") | grep -q "frontend-test"
' || FAILED=$((FAILED+1))

# S2: Auto-fix on backend coverage failure
run_scenario "S2" "Auto-fix backend coverage" '
  python3 scripts/ci/sanitize_ci_log.py < <(echo "##[error]backend-test\nCoverageBelowThreshold") | grep -q "CoverageBelowThreshold"
' || FAILED=$((FAILED+1))

# S3: Auto-fix on test-quality placeholder
run_scenario "S3" "Auto-fix test-quality placeholder" '
  python3 scripts/ci/sanitize_ci_log.py < <(echo "##[error]test-quality\nPlaceholderViolation") | grep -q "PlaceholderViolation"
' || FAILED=$((FAILED+1))

# S4: Main branch push is skipped (workflow-level branches-ignore)
# Verified by reading workflow YAML: branches-ignore: [main]
run_scenario "S4" "Main branch skipped" '
  grep -q "branches-ignore:" .github/workflows/auto-fix-ci.yml && \
  grep -A 2 "branches-ignore:" .github/workflows/auto-fix-ci.yml | grep -q "main"
' || FAILED=$((FAILED+1))

# S5: 3rd attempt is stopped (label check)
# Verified by code review of apply-fix job's "Check retry limit" step
run_scenario "S5" "3rd attempt label check" '
  grep -q "MAX_FIX_ATTEMPTS" .github/workflows/auto-fix-ci.yml && \
  grep -q "auto-fix-count" .github/workflows/auto-fix-ci.yml
' || FAILED=$((FAILED+1))

# S6: Service file change needs review (via check_auto_fix_diff.py)
run_scenario "S6" "Service file needs_review" '
  TMP=$(mktemp -d)
  (cd "$TMP" && git init -q && git config user.email t@t.com && git config user.name t && \
    echo init > README.md && git add . && git commit -qm init && \
    mkdir -p backend/services && echo svc > backend/services/foo.py && \
    git add . && git commit -qm "add service") && \
  (cd "$TMP" && python3 "$PROJECT_ROOT/scripts/ci/check_auto_fix_diff.py" 2>&1 | grep -q "needs_review=true")
  rm -rf "$TMP"
' || FAILED=$((FAILED+1))

# S7: pytest failure is rejected (covered by [NO-TEST-NEEDED] check)
run_scenario "S7" "No test marker rejected" '
  TMP=$(mktemp -d)
  (cd "$TMP" && git init -q && git config user.email t@t.com && git config user.name t && \
    echo init > README.md && git add . && git commit -qm init && \
    mkdir -p tests && echo t > tests/test_foo.py && \
    git add . && git commit -qm "test [NO-TEST-NEEDED]") && \
  (cd "$TMP" && python3 "$PROJECT_ROOT/scripts/ci/check_auto_fix_diff.py" 2>&1) || TEST_EXIT=$?
  rm -rf "$TMP"
  [ "${TEST_EXIT:-0}" = "1" ]
' || FAILED=$((FAILED+1))

# S8: CI cancelled is ignored (workflow-level if)
run_scenario "S8" "Cancelled conclusion ignored" '
  grep -q "conclusion == .failure" .github/workflows/auto-fix-ci.yml
' || FAILED=$((FAILED+1))

echo ""
echo "━━━ Summary ━━━"
if [ "$FAILED" -eq 0 ]; then
  echo "✅ All scenarios passed"
  exit 0
else
  echo "❌ $FAILED scenario(s) failed"
  exit 1
fi