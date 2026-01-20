#!/bin/bash
# Test Extensions
# Validates VSCode and Browser extension files

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           EXTENSION VALIDATION                             ║"
echo "╚════════════════════════════════════════════════════════════╝"

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

errors=0

echo ""
echo "═══ VSCode Extension ═══"

# VSCode files
vscode_files=(
    "extensions/vscode/package.json"
    "extensions/vscode/src/extension.ts"
    "extensions/vscode/resources/icon.svg"
)

for file in "${vscode_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
        ((errors++))
    fi
done

# Validate package.json
if [ -f "extensions/vscode/package.json" ]; then
    if grep -q '"name"' extensions/vscode/package.json; then
        echo -e "${GREEN}✓${NC} package.json has name field"
    else
        echo -e "${RED}✗${NC} package.json missing name field"
        ((errors++))
    fi
fi

echo ""
echo "═══ Browser Extension ═══"

# Browser files
browser_files=(
    "extensions/browser/manifest.json"
    "extensions/browser/popup/popup.html"
    "extensions/browser/popup/popup.js"
    "extensions/browser/popup/popup.css"
    "extensions/browser/content/content.js"
    "extensions/browser/background/background.js"
)

for file in "${browser_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
        ((errors++))
    fi
done

# Validate manifest.json
if [ -f "extensions/browser/manifest.json" ]; then
    if grep -q '"manifest_version"' extensions/browser/manifest.json; then
        echo -e "${GREEN}✓${NC} manifest.json has manifest_version"
    else
        echo -e "${RED}✗${NC} manifest.json missing manifest_version"
        ((errors++))
    fi
fi

echo ""
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ ALL EXTENSION FILES VALIDATED${NC}"
    exit 0
else
    echo -e "${RED}❌ $errors ERROR(S) FOUND${NC}"
    exit 1
fi
