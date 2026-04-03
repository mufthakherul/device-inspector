#!/bin/bash
################################################################################
# Device Inspector (Inspecta) Setup Script for Linux and macOS
#
# Provides automated setup with Python environment, dependencies, and optional tools
# 
# Usage:
#   ./setup.sh                    # Full dev setup
#   ./setup.sh --prod             # Production setup (minimal)
#   ./setup.sh --install-tools    # Install optional system tools
#   ./setup.sh --help             # Show help
#
# Supports: Ubuntu/Debian, Fedora/RHEL, Arch, Alpine, macOS
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/venv"
PYTHON_CMD=""
MODE="dev"
INSTALL_TOOLS=false
VERBOSE=false

################################################################################
# Logging Functions
################################################################################

log_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}  $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

log_info() {
    echo -e "${BLUE}•${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

log_error() {
    echo -e "${RED}✗${NC}  $1"
}

################################################################################
# Help
################################################################################

show_help() {
    cat << EOF
Device Inspector Setup Script

Usage:
  $0 [OPTIONS]

Options:
  --mode {dev|prod}      Setup mode (default: dev)
                         dev:  Full setup with tests and optional tools
                         prod: Minimal production setup
  
  --install-tools        Install optional system diagnostics tools
  
  --skip-tests           Skip running test suite
  
  -v, --verbose          Show detailed output
  
  -h, --help             Show this help message

Examples:
  $0                        # Full development setup
  $0 --mode prod            # Production setup
  $0 --install-tools        # Install system tools
  $0 --skip-tests           # Skip tests

EOF
    exit 0
}

################################################################################
# Detection & Validation
################################################################################

detect_python() {
    log_section "Detecting Python Installation"
    
    for cmd in python3 python; do
        if command -v "$cmd" &> /dev/null; then
            version=$("$cmd" --version 2>&1)
            log_success "Found: $version"
            PYTHON_CMD="$cmd"
            return 0
        fi
    done
    
    log_error "Python 3.11+ not found"
    suggest_python_install
    return 1
}

check_python_version() {
    local version=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 11 ]); then
        log_error "Python $version found, but 3.11+ required"
        suggest_python_install
        return 1
    fi
    
    log_success "Python $version ✓"
    return 0
}

suggest_python_install() {
    log_section "Python Installation Required"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "macOS detected:"
        log_info "1. Using Homebrew: brew install python@3.12"
        log_info "2. Or visit: https://www.python.org/downloads/macos/"
    else
        log_info "Linux detected - Use your package manager:"
        log_info "Ubuntu/Debian: sudo apt update && sudo apt install python3.12 python3.12-venv"
        log_info "Fedora/RHEL: sudo dnf install python3.12 python3.12-venv"
        log_info "Arch: sudo pacman -S python"
        log_info "Alpine: sudo apk add python3"
    fi
}

################################################################################
# Virtual Environment Setup
################################################################################

setup_venv() {
    log_section "Setting Up Virtual Environment"
    
    if [ -d "$VENV_DIR" ]; then
        log_info "venv already exists at $VENV_DIR"
        return 0
    fi
    
    log_info "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR" || {
        log_error "Failed to create virtual environment"
        return 1
    }
    
    log_success "Virtual environment created ✓"
    return 0
}

get_venv_python() {
    echo "$VENV_DIR/bin/python"
}

get_venv_pip() {
    echo "$VENV_DIR/bin/pip"
}

################################################################################
# Dependencies
################################################################################

install_dependencies() {
    log_section "Installing Python Dependencies"
    
    local venv_pip=$(get_venv_pip)
    local venv_python=$(get_venv_python)
    
    # Upgrade pip
    log_info "Upgrading pip..."
    $venv_pip install --upgrade pip > /dev/null 2>&1 || {
        log_error "Failed to upgrade pip"
        return 1
    }
    
    # Install main requirements
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        log_info "Installing requirements.txt..."
        $venv_pip install -r "$PROJECT_ROOT/requirements.txt" > /dev/null 2>&1 || {
            log_error "Failed to install main dependencies"
            return 1
        }
    fi
    
    # Install optional dependencies if in dev mode
    if [ "$MODE" == "dev" ] && [ -f "$PROJECT_ROOT/requirements-optional.txt" ]; then
        log_info "Installing optional dependencies..."
        $venv_pip install -r "$PROJECT_ROOT/requirements-optional.txt" > /dev/null 2>&1 || {
            log_warn "Some optional dependencies failed to install"
        }
    fi
    
    # Install project in editable mode (best-effort)
    # Note: some environments may not support editable build for this repo shape.
    log_info "Installing project in editable mode..."
    if ! $venv_pip install -e "$PROJECT_ROOT" > /dev/null 2>&1; then
        log_warn "Editable install failed; continuing with module execution from repo root"
        log_warn "Use: $venv_python -m agent.cli ..."
    fi
    
    log_success "Dependencies installed ✓"
    return 0
}

################################################################################
# Code Quality Checks
################################################################################

run_code_checks() {
    log_section "Running Code Quality Checks"
    
    local venv_python=$(get_venv_python)
    
    # Black format check
    log_info "Running Black format check..."
    if $venv_python -m black --check . --quiet 2>/dev/null; then
        log_success "Black check passed ✓"
    else
        log_warn "Black check found formatting issues"
    fi
    
    # Ruff lint check
    log_info "Running Ruff linter..."
    if $venv_python -m ruff check . 2>/dev/null; then
        log_success "Ruff check passed ✓"
    else
        log_warn "Ruff check found issues"
    fi
}

################################################################################
# Testing
################################################################################

run_tests() {
    log_section "Running Test Suite"
    
    local venv_python=$(get_venv_python)
    
    if ! [ -d "$PROJECT_ROOT/tests" ]; then
        log_warn "Tests directory not found"
        return 0
    fi
    
    log_info "Running pytest..."
    if $venv_python -m pytest -q "$PROJECT_ROOT/tests" 2>/dev/null; then
        log_success "All tests passed ✓"
        return 0
    else
        log_warn "Some tests failed (non-critical)"
        return 0
    fi
}

smoke_test_cli() {
    log_section "Running CLI Smoke Test"
    
    local venv_python=$(get_venv_python)
    local output_dir="$PROJECT_ROOT/test-smoke"
    
    log_info "Testing: inspecta run --mode quick --use-sample"
    
    if $venv_python -m agent.cli run \
        --mode quick \
        --output "$output_dir" \
        --use-sample \
        > /dev/null 2>&1; then
        
        if [ -f "$output_dir/report.json" ]; then
            log_success "CLI smoke test passed ✓"
            return 0
        fi
    fi
    
    log_warn "CLI smoke test did not produce expected output"
    return 0
}

################################################################################
# System Tools Installation
################################################################################

install_system_tools() {
    if [ "$INSTALL_TOOLS" != "true" ]; then
        return 0
    fi
    
    log_section "Installing System Diagnostics Tools"
    
    detect_package_manager
    case "$PKG_MANAGER" in
        apt-get)
            install_tools_apt
            ;;
        dnf)
            install_tools_dnf
            ;;
        pacman)
            install_tools_pacman
            ;;
        brew)
            install_tools_brew
            ;;
        *)
            log_warn "No supported package manager found"
            ;;
    esac
}

detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt-get"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
    elif command -v brew &> /dev/null; then
        PKG_MANAGER="brew"
    else
        PKG_MANAGER="unknown"
    fi
}

install_tools_apt() {
    log_info "Detected: apt (Ubuntu/Debian)"
    log_info "Installing smartmontools, dmidecode, lm-sensors..."
    
    sudo apt-get update -qq || true
    sudo apt-get install -y smartmontools dmidecode lm-sensors 2>/dev/null || {
        log_warn "Some packages failed to install"
    }
    
    log_success "Tools installation complete ✓"
}

install_tools_dnf() {
    log_info "Detected: dnf (Fedora/RHEL)"
    log_info "Installing smartmontools, dmidecode, lm_sensors..."
    
    sudo dnf install -y smartmontools dmidecode lm_sensors 2>/dev/null || {
        log_warn "Some packages failed to install"
    }
    
    log_success "Tools installation complete ✓"
}

install_tools_pacman() {
    log_info "Detected: pacman (Arch)"
    log_info "Installing smartmontools, dmidecode, lm_sensors..."
    
    sudo pacman -S --noconfirm smartmontools dmidecode lm_sensors 2>/dev/null || {
        log_warn "Some packages failed to install"
    }
    
    log_success "Tools installation complete ✓"
}

install_tools_brew() {
    log_info "Detected: Homebrew (macOS)"
    log_info "Installing smartmontools..."
    
    brew install smartmontools 2>/dev/null || {
        log_warn "Some packages failed to install"
    }
    
    log_success "Tools installation complete ✓"
}

################################################################################
# Next Steps
################################################################################

print_next_steps() {
    local venv_python=$(get_venv_python)
    
    log_section "Setup Complete!"
    
    cat << EOF
Next Steps:

1. Activate Virtual Environment:
   source $VENV_DIR/bin/activate

2. Run inspecta with sample data (no root needed):
   $venv_python -m agent.cli run --mode quick --output ./reports/test --use-sample

3. Run real hardware inspection (requires root):
   sudo $venv_python -m agent.cli run --mode quick --output ./reports/mydevice

4. Check device inventory:
   $venv_python -m agent.cli inventory --use-sample

5. Auto precheck launcher:
    $venv_python scripts/launch_inspecta.py --setup-only
    $venv_python scripts/launch_inspecta.py --require-hardware --install-tools

6. View documentation:
   - Developer Guide: docs/DEV_SETUP.md
   - Architecture: docs/ARCHITECTURE.md
   - Contributing: CONTRIBUTING.md

7. Running tests:
   $venv_python -m pytest -v

8. Code formatting:
   $venv_python -m black .
   $venv_python -m ruff check --fix .

For more details, see: README.md
Repository: https://github.com/mufthakherul/device-inspector

Happy developing! 🚀
EOF
}

################################################################################
# Parse Arguments
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --install-tools)
            INSTALL_TOOLS=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

################################################################################
# Main Setup Flow
################################################################################

banner() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║   DEVICE-INSPECTOR (INSPECTA) SETUP WIZARD                   ║
║   Cross-Platform Project Initialization                      ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo ""
}

main() {
    banner
    
    # Detect Python
    if ! detect_python; then
        exit 1
    fi
    
    # Check version
    if ! check_python_version; then
        exit 1
    fi
    
    # Setup venv
    if ! setup_venv; then
        exit 1
    fi
    
    # Install dependencies
    if ! install_dependencies; then
        exit 1
    fi
    
    # Code checks
    run_code_checks
    
    # Tests (unless skipped)
    if [ "$SKIP_TESTS" != "true" ]; then
        run_tests
        smoke_test_cli
    fi
    
    # System tools (optional)
    if [ "$INSTALL_TOOLS" == "true" ]; then
        install_system_tools
    fi
    
    # Summary
    print_next_steps
}

# Run main
main
