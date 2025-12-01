#!/bin/bash
#
# Run eBPF Benchmarks in Vagrant VM
#
# This script automates the complete workflow:
# 1. Start Vagrant VM (if not running)
# 2. Build all eBPF programs
# 3. Run benchmarks for all languages
# 4. Retrieve results to host
# 5. Generate comparison reports
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAGRANT_DIR="$PROJECT_ROOT/vagrant"
RESULTS_DIR="$PROJECT_ROOT/benchmarks/results"
DURATION=${DURATION:-10}
LANGUAGES=${LANGUAGES:-"c python golang rust"}
VERBOSE=${VERBOSE:-0}

# Functions
log() {
    echo -e "${GREEN}[*]${NC} $1"
}

info() {
    echo -e "${BLUE}[i]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================================================="
    echo "  $1"
    echo "=========================================================================="
    echo ""
}

check_vagrant() {
    if ! command -v vagrant &> /dev/null; then
        error "Vagrant is not installed. Please install Vagrant first."
    fi
    success "Vagrant found: $(vagrant --version)"
}

check_vm_status() {
    cd "$VAGRANT_DIR"
    status=$(vagrant status | grep "default" | awk '{print $2}')
    echo "$status"
}

start_vm() {
    print_header "Starting Vagrant VM"

    local status=$(check_vm_status)

    if [ "$status" = "running" ]; then
        success "Vagrant VM is already running"
        return 0
    fi

    if [ "$status" = "not" ]; then
        log "Creating Vagrant VM (this may take several minutes)..."
        cd "$VAGRANT_DIR"
        vagrant up
        success "Vagrant VM created and started"
    else
        log "Resuming Vagrant VM..."
        cd "$VAGRANT_DIR"
        vagrant up
        success "Vagrant VM started"
    fi
}

build_benchmarks() {
    print_header "Building eBPF Programs in Vagrant"

    log "Running builds for: $LANGUAGES"

    for lang in $LANGUAGES; do
        info "Building $lang benchmarks..."
        vagrant ssh -c "cd /home/vagrant/ebpf_benchmark && make build-$lang" || warn "Failed to build $lang"
    done

    success "All builds completed"
}

run_benchmarks() {
    print_header "Running Benchmarks in Vagrant"

    log "Running benchmarks with duration: $DURATION seconds per test"

    if [ "$VERBOSE" -eq 1 ]; then
        vagrant ssh -c "cd /home/vagrant/ebpf_benchmark && python3 run_all_benchmarks.py -d $DURATION -v"
    else
        vagrant ssh -c "cd /home/vagrant/ebpf_benchmark && python3 run_all_benchmarks.py -d $DURATION"
    fi

    success "Benchmarks completed"
}

retrieve_results() {
    print_header "Retrieving Results from Vagrant"

    mkdir -p "$RESULTS_DIR"

    log "Copying results from Vagrant..."

    # Try different methods to copy results
    if command -v vagrant-scp &> /dev/null; then
        info "Using vagrant scp..."
        vagrant scp "default:/home/vagrant/ebpf_benchmark/benchmarks/results/*" "$RESULTS_DIR/" 2>/dev/null || true
    else
        info "Using vagrant ssh with tar..."
        vagrant ssh -c "cd /home/vagrant/ebpf_benchmark && tar -czf /tmp/results.tar.gz benchmarks/results/" 2>/dev/null || true
        vagrant scp "default:/tmp/results.tar.gz" "$RESULTS_DIR/" 2>/dev/null || true

        if [ -f "$RESULTS_DIR/results.tar.gz" ]; then
            cd "$RESULTS_DIR"
            tar -xzf results.tar.gz
            rm -f results.tar.gz
        fi
    fi

    success "Results retrieved to: $RESULTS_DIR"
}

generate_reports() {
    print_header "Generating Comparison Reports"

    log "Creating text and HTML reports..."

    cd "$PROJECT_ROOT"
    python3 generate_benchmark_report.py

    success "Reports generated:"
    success "  - Text report: $RESULTS_DIR/report.txt"
    success "  - HTML report: $RESULTS_DIR/report.html"
}

view_results() {
    print_header "Benchmark Results"

    if [ -f "$RESULTS_DIR/report.txt" ]; then
        cat "$RESULTS_DIR/report.txt"
    else
        warn "Text report not found"
    fi

    if [ -f "$RESULTS_DIR/report.html" ]; then
        info "HTML report available at: $RESULTS_DIR/report.html"

        # Try to open in browser
        if command -v open &> /dev/null; then
            info "Opening HTML report in browser..."
            open "$RESULTS_DIR/report.html" &
        elif command -v xdg-open &> /dev/null; then
            info "Opening HTML report in browser..."
            xdg-open "$RESULTS_DIR/report.html" &
        fi
    fi
}

print_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Run eBPF benchmarks in Vagrant VM and generate reports.

OPTIONS:
    -d, --duration SECS     Benchmark duration per test (default: 10)
    -l, --languages LANGS   Languages to test (default: "c python golang rust")
    -q, --quick             Quick run (5 seconds per test)
    -v, --verbose           Verbose output
    -h, --help              Show this help message

EXAMPLES:
    # Run quick benchmark (5 seconds)
    $0 --quick

    # Run specific languages for 20 seconds
    $0 -l "go rust" -d 20

    # Run with verbose output
    $0 --verbose

    # Quick test of Go and Rust only
    $0 -q -l "golang rust"

WORKFLOW:
    1. Starts Vagrant VM (if not running)
    2. Builds all eBPF programs
    3. Runs benchmarks for specified duration
    4. Retrieves results to host
    5. Generates comparison reports
    6. Displays results

REQUIREMENTS:
    - Vagrant installed
    - VirtualBox (or other Vagrant provider)
    - ~5GB disk space for VM
    - Internet connection (for VM setup)

NOTES:
    - First run may take 10-15 minutes for VM setup
    - Subsequent runs are faster
    - Results are saved to: benchmarks/results/
    - HTML report is generated automatically

EOF
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--duration)
                DURATION="$2"
                shift 2
                ;;
            -l|--languages)
                LANGUAGES="$2"
                shift 2
                ;;
            -q|--quick)
                DURATION=5
                shift
                ;;
            -v|--verbose)
                VERBOSE=1
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done

    # Main workflow
    clear
    print_header "eBPF BENCHMARK SUITE - Vagrant Runner"

    info "Project root: $PROJECT_ROOT"
    info "Benchmark duration: $DURATION seconds"
    info "Languages: $LANGUAGES"
    info "Results directory: $RESULTS_DIR"
    info "Verbose mode: $([ $VERBOSE -eq 1 ] && echo 'ON' || echo 'OFF')"

    check_vagrant
    start_vm
    build_benchmarks
    run_benchmarks
    retrieve_results
    generate_reports
    view_results

    print_header "✅ BENCHMARKING COMPLETE"

    success "All benchmarks completed successfully!"
    info "Results saved to: $RESULTS_DIR"

    if [ -f "$RESULTS_DIR/report.html" ]; then
        info "View results: $RESULTS_DIR/report.html"
    fi

    echo ""
}

# Run main function
main "$@"
