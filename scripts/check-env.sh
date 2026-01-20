#!/bin/bash

# ============================================================================
# Environment Check Script - Quick prerequisite validation
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "Environment Check"
echo "================="
echo ""

# Node.js
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓${NC} Node.js: $(node -v)"
else
    echo -e "${RED}✗${NC} Node.js: Not installed"
fi

# npm
if command -v npm &> /dev/null; then
    echo -e "${GREEN}✓${NC} npm: v$(npm -v)"
else
    echo -e "${RED}✗${NC} npm: Not installed"
fi

# Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python: $(python3 --version)"
else
    echo -e "${RED}✗${NC} Python: Not installed"
fi

# pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip: $(pip3 --version | cut -d' ' -f2)"
else
    echo -e "${RED}✗${NC} pip: Not installed"
fi

# Git
if command -v git &> /dev/null; then
    echo -e "${GREEN}✓${NC} Git: $(git --version | cut -d' ' -f3)"
else
    echo -e "${RED}✗${NC} Git: Not installed"
fi

# Disk space
AVAILABLE=$(df -h . | tail -1 | awk '{print $4}')
echo -e "${GREEN}✓${NC} Disk available: $AVAILABLE"

echo ""
echo "System ready for validation."
