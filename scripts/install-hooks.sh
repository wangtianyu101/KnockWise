#!/bin/sh
# Use the version-controlled hooks directly; do not copy them into .git/hooks.
set -eu

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

if [ ! -x "scripts/pre-commit" ]; then
  echo "❌ scripts/pre-commit 不存在或不可执行" >&2
  exit 1
fi

git config --local core.hooksPath scripts
configured=$(git config --local --get core.hooksPath)
if [ "$configured" != "scripts" ]; then
  echo "❌ core.hooksPath 配置失败: $configured" >&2
  exit 1
fi

echo "✅ Git hooks 已指向版本化目录: scripts"
