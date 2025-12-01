#!/bin/bash
# Script to build and run benchmarks inside Vagrant VM

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== eBPF Benchmark - Vagrant Build & Run ===${NC}"

# Check if Vagrant is running
if ! vagrant -v &> /dev/null; then
    echo -e "${RED}Error: Vagrant not installed${NC}"
    exit 1
fi

cd "$PROJECT_ROOT/vagrant"

# Check if VM is running
if vagrant status | grep -q "not created"; then
    echo -e "${YELLOW}VM not created, creating now...${NC}"
    vagrant up
elif vagrant status | grep -q "poweroff"; then
    echo -e "${YELLOW}VM is powered off, starting...${NC}"
    vagrant up
fi

# Run make targets inside Vagrant
echo -e "${GREEN}Building all eBPF programs...${NC}"
vagrant ssh -c "cd /home/vagrant/ebpf_benchmark && make build"

echo -e "${GREEN}Running benchmarks...${NC}"
vagrant ssh -c "cd /home/vagrant/ebpf_benchmark && make benchmark"

echo -e "${GREEN}Generating analysis plots...${NC}"
vagrant ssh -c "cd /home/vagrant/ebpf_benchmark && python3 analysis/scripts/generate_plots.py"

echo -e "${GREEN}Copying results back to host...${NC}"
vagrant ssh -c "tar -czf /tmp/ebpf_results.tar.gz -C /home/vagrant/ebpf_benchmark benchmarks/results analysis/plots"
vagrant scp "default:/tmp/ebpf_results.tar.gz" "$PROJECT_ROOT/" || true

echo -e "${GREEN}=== Build and benchmark complete! ===${NC}"
echo -e "Results are available in:"
echo -e "  - ${YELLOW}benchmarks/results/${NC}"
echo -e "  - ${YELLOW}analysis/plots/${NC}"
