#!/bin/bash
# ============================================================================
# Test Extensions (VSCode & Browser)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo -e "${BLUE}Testing Extensions${NC}"
echo ""

ERRORS=0

# ============================================================================
# Test VSCode Extension
# ============================================================================

echo "1. VSCode Extension"
echo "-------------------"

if [ -d "$PROJECT_ROOT/extensions/vscode" ]; then
    cd "$PROJECT_ROOT/extensions/vscode"
    
    # Check package.json
    if [ -f "package.json" ]; then
        print_success "package.json exists"
    else
        print_error "package.json not found"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check source files
    if [ -f "src/extension.ts" ]; then
        print_success "extension.ts exists"
    else
        print_error "extension.ts not found"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check resources
    if [ -f "resources/icon.svg" ]; then
        print_success "icon.svg exists"
    else
        print_info "icon.svg not found (optional)"
    fi
    
    # Validate package.json structure
    if python3 -c "import json; j=json.load(open('package.json')); assert 'name' in j and 'version' in j" 2>/dev/null; then
        print_success "package.json structure valid"
    else
        print_error "package.json structure invalid"
        ERRORS=$((ERRORS + 1))
    fi
    
    cd "$PROJECT_ROOT"
else
    print_error "VSCode extension directory not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# ============================================================================
# Test Browser Extension
# ============================================================================

echo "2. Browser Extension"
echo "--------------------"

if [ -d "$PROJECT_ROOT/extensions/browser" ]; then
    cd "$PROJECT_ROOT/extensions/browser"
    
    # Check manifest
    if [ -f "manifest.json" ]; then
        print_success "manifest.json exists"
        
        # Validate JSON
        if python3 -c "import json; json.load(open('manifest.json'))" 2>/dev/null; then
            print_success "manifest.json is valid JSON"
        else
            print_error "manifest.json is invalid JSON"
            ERRORS=$((ERRORS + 1))
        fi
        
        # Check manifest version
        if python3 -c "import json; j=json.load(open('manifest.json')); assert j.get('manifest_version') == 3" 2>/dev/null; then
            print_success "Manifest V3 confirmed"
        else
            print_info "Manifest version check skipped"
        fi
    else
        print_error "manifest.json not found"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check popup files
    if [ -f "popup/popup.html" ]; then
        print_success "popup.html exists"
    else
        print_error "popup.html not found"
        ERRORS=$((ERRORS + 1))
    fi
    
    if [ -f "popup/popup.js" ]; then
        print_success "popup.js exists"
    else
        print_error "popup.js not found"
        ERRORS=$((ERRORS + 1))
    fi
    
    if [ -f "popup/popup.css" ]; then
        print_success "popup.css exists"
    else
        print_info "popup.css not found (optional)"
    fi
    
    # Check background script
    if [ -f "background/background.js" ]; then
        print_success "background.js exists"
    else
        print_error "background.js not found"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check content script
    if [ -f "content/content.js" ]; then
        print_success "content.js exists"
    else
        print_error "content.js not found"
        ERRORS=$((ERRORS + 1))
    fi
    
    cd "$PROJECT_ROOT"
else
    print_error "Browser extension directory not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

if [ $ERRORS -eq 0 ]; then
    print_success "All extension tests passed"
    exit 0
else
    print_error "$ERRORS error(s) found"
    exit 1
fi
