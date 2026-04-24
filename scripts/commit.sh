#!/usr/bin/env bash
# Usage: ./scripts/commit.sh "what changed"
# Stages log file, commits with a short UUID as the message.
set -e

if [ -z "$1" ]; then
  echo "Usage: ./scripts/commit.sh \"what changed\""
  exit 1
fi

UUID=$(openssl rand -hex 4)
DATE=$(date -u +"%Y-%m-%d %H:%M UTC")
CHANGED=$(git diff --cached --name-only)

mkdir -p log
cat > "log/${UUID}.md" <<EOF
# ${UUID}
**Date:** ${DATE}
**Change:** $1

## Files
\`\`\`
${CHANGED}
\`\`\`
EOF

git add "log/${UUID}.md"
git commit -m "${UUID}"
echo "→ committed as ${UUID}"
