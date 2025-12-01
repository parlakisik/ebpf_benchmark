#!/bin/bash
#
# Run eBPF Benchmarks in Docker (Works on ARM Mac)
#
# This script runs benchmarks in a Docker container, which works
# on Apple Silicon Macs where VirtualBox/Vagrant don't support ARM.
#
# Prerequisites:
#   - Docker Desktop installed and running
#
# Usage:
#   bash scripts/run_docker_benchmark.sh [OPTIONS]
#
#   Options:
#     -q, --quick      Quick 5-second tests
#     -d, --duration   Duration per benchmark (default: 10)
#     -l, --langs      Languages to test (default: "c python golang rust")
#     -v, --verbose    Verbose output
#     -h, --help       Show this help message
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DURATION=${DURATION:-10}
LANGUAGES=${LANGUAGES:-"c python golang rust"}
VERBOSE=${VERBOSE:-0}
IMAGE_NAME="ebpf-benchmark:local"

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
    echo "==========================================================================="
    echo "  $1"
    echo "==========================================================================="
    echo ""
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker Desktop first."
    fi

    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker Desktop."
    fi

    success "Docker found: $(docker --version)"
}

build_image() {
    print_header "Building Docker Image"

    log "Creating Dockerfile..."

    cat > /tmp/Dockerfile.ebpf << 'DOCKERFILE'
FROM ubuntu:jammy

RUN apt-get update && apt-get install -y \
    build-essential \
    clang llvm libelf-dev libz-dev \
    linux-headers-generic \
    bcc libbpf-dev \
    python3 python3-pip \
    golang-go \
    rustc cargo \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    matplotlib \
    numpy \
    pyyaml \
    jinja2

WORKDIR /app

CMD ["/bin/bash"]
DOCKERFILE

    log "Building image (this may take 2-5 minutes on first run)..."
    docker build -f /tmp/Dockerfile.ebpf -t "$IMAGE_NAME" . > /dev/null 2>&1 || {
        error "Docker image build failed"
    }

    success "Docker image built successfully"
}

run_benchmarks() {
    print_header "Running eBPF Benchmarks in Docker"

    log "Duration: $DURATION seconds per test"
    log "Languages: $LANGUAGES"

    VERBOSE_FLAG=""
    if [ "$VERBOSE" -eq 1 ]; then
        VERBOSE_FLAG="-v"
    fi

    log "Starting Docker container..."

    docker run --rm -it \
        -v "$PROJECT_ROOT:/app" \
        -w /app \
        "$IMAGE_NAME" \
        bash -c "
            echo 'Building all programs...'
            for lang in $LANGUAGES; do
                echo \"Building \$lang...\"
                make build-\$lang 2>&1 || echo \"Warning: \$lang build may have failed\"
            done

            echo ''
            echo 'Running benchmarks...'
            python3 run_all_benchmarks.py -d $DURATION $VERBOSE_FLAG

            echo ''
            echo 'Generating reports...'
            python3 generate_benchmark_report.py
        " || {
        error "Benchmark execution failed"
    }

    success "Benchmarks completed successfully"
}

view_results() {
    print_header "Benchmark Results"

    RESULTS_DIR="$PROJECT_ROOT/benchmarks/results"

    if [ -f "$RESULTS_DIR/report.txt" ]; then
        cat "$RESULTS_DIR/report.txt"
    else
        warn "Text report not found at $RESULTS_DIR/report.txt"
    fi

    if [ -f "$RESULTS_DIR/report.html" ]; then
        info "HTML report saved to: $RESULTS_DIR/report.html"
        info "View it with: open $RESULTS_DIR/report.html"
    fi
}

print_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Run eBPF benchmarks in Docker (works on ARM Mac).

OPTIONS:
    -q, --quick              Quick run (5 seconds per test)
    -d, --duration SECS      Benchmark duration per test (default: 10)
    -l, --languages LANGS    Languages to test (default: "c python golang rust")
    -v, --verbose            Verbose output
    -h, --help               Show this help message

EXAMPLES:
    # Quick benchmark (5 seconds)
    $0 --quick

    # Benchmark specific languages for 20 seconds
    $0 -l "golang rust" -d 20

    # Verbose output
    $0 --verbose

REQUIREMENTS:
    - Docker Desktop installed and running
    - 5GB free disk space
    - ~10-15 minutes for first run (image build)

NOTES:
    - First run builds Docker image (~5 minutes)
    - Subsequent runs reuse the image (much faster)
    - Results saved to: benchmarks/results/
    - Works on ARM Mac (Apple Silicon)

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
    print_header "eBPF BENCHMARK SUITE - Docker Runner (ARM Mac)"

    info "Project root: $PROJECT_ROOT"
    info "Benchmark duration: $DURATION seconds"
    info "Languages: $LANGUAGES"
    info "Verbose mode: $([ $VERBOSE -eq 1 ] && echo 'ON' || echo 'OFF')"

    check_docker
    build_image
    run_benchmarks
    view_results

    print_header "✅ BENCHMARKING COMPLETE"

    success "All benchmarks completed successfully!"
    info "Results saved to: $PROJECT_ROOT/benchmarks/results"

    if [ -f "$PROJECT_ROOT/benchmarks/results/report.html" ]; then
        info "View HTML report: open $PROJECT_ROOT/benchmarks/results/report.html"
    fi

    echo ""
}

# Run main function
main "$@"
