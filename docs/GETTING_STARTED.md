# Getting Started with eBPF Benchmark Suite

This guide will help you set up and run the eBPF Benchmark Suite.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Quick Start](#quick-start)
3. [Using Vagrant](#using-vagrant)
4. [Running Benchmarks](#running-benchmarks)
5. [Analyzing Results](#analyzing-results)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **Linux Kernel**: 5.8+ (for ring buffers; 5.4+ for basic eBPF)
- **RAM**: 4GB minimum (8GB+ recommended)
- **CPU**: 4 cores minimum (for scalability tests)
- **Storage**: 2GB free space

### Supported Distributions
- Ubuntu 20.04 LTS or later
- Debian 11+
- CentOS 8+
- Fedora 33+

### Build Dependencies

**System packages:**
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    clang \
    llvm \
    libelf-dev \
    libz-dev \
    linux-headers-$(uname -r) \
    pkg-config
```

**Language toolchains:**
- Python 3.8+
- Go 1.18+
- Rust 1.70+ (with `cargo`)
- LLVM 12+

**eBPF tools:**
```bash
sudo apt-get install -y \
    libbpf-dev \
    bcc \
    libbcc
```

---

## Quick Start

### 1. Clone the Repository
```bash
cd ~/projects
git clone https://github.com/yourusername/ebpf_benchmark.git
cd ebpf_benchmark
```

### 2. Install Dependencies

**On Ubuntu/Debian:**
```bash
# Install system packages
sudo apt-get update
sudo apt-get install -y \
    build-essential clang llvm libelf-dev libz-dev \
    linux-headers-$(uname -r) python3 python3-pip \
    pkg-config bcc libbpf-dev

# Install Python dependencies
pip3 install -r requirements.txt
```

### 3. Verify Setup
```bash
# Check kernel eBPF support
make check-deps

# Verify kernel capabilities
make -C src/c verify-kernel
```

### 4. Build Programs
```bash
# Build all language implementations
make build

# Or build specific languages
make build-c
make build-python
make build-golang
make build-rust
```

### 5. Run a Simple Benchmark
```bash
# Run Python ring buffer benchmark (quickest to test)
sudo python3 src/python/ringbuf_throughput.py -d 10
```

---

## Using Vagrant

The easiest way to get started is using the included Vagrant configuration, which automatically provisions an Ubuntu VM with all dependencies.

### Prerequisites
- VirtualBox or other hypervisor
- Vagrant 2.2.0+
- 4GB+ RAM available for VM

### Setup

```bash
# From project root
cd vagrant

# Create and provision the VM
vagrant up

# SSH into the VM
vagrant ssh

# Inside VM, run benchmarks
cd /home/vagrant/ebpf_benchmark
make build
make benchmark
```

### Running via Host Script

From the host machine:
```bash
# This builds and runs benchmarks inside the VM
bash scripts/vagrant_run.sh
```

### Copy Results Back

```bash
# From host, copy results from VM
vagrant scp "default:/home/vagrant/ebpf_benchmark/benchmarks/results/*" benchmarks/results/
```

### Managing the VM

```bash
# Stop VM
vagrant halt

# Resume VM
vagrant up

# Destroy VM (careful!)
vagrant destroy

# Rebuild with new provisioning
vagrant destroy -f && vagrant up
```

---

## Running Benchmarks

### Run All Benchmarks
```bash
sudo make benchmark
```

### Run Specific Language Benchmarks
```bash
sudo make benchmark-c
sudo make benchmark-python
sudo make benchmark-golang
sudo make benchmark-rust
```

### Run Custom Benchmarks

```bash
# Run benchmark runner directly
sudo python3 benchmarks/harness/runner.py \
    -c benchmarks/configs/benchmark_config.yaml \
    -o benchmarks/results \
    -l python \
    --verbose
```

### Benchmark Parameters

Edit `benchmarks/configs/benchmark_config.yaml` to customize:
- Duration of each benchmark
- Load generator type and intensity
- Languages to test
- Metrics to collect
- CPU affinity settings

### Load Generators

Available load types in configuration:
- `syscall_flood`: Flood system with syscalls (default)
- `cpu_bound`: CPU-intensive workload
- `memory`: Memory-intensive workload
- `multi_cpu_flood`: Multi-CPU syscall flood
- `packet_flood`: Network packet flooding (requires setup)

---

## Analyzing Results

### View Results

Results are saved to `benchmarks/results/latest.json`

```bash
# Pretty-print latest results
cat benchmarks/results/latest.json | python3 -m json.tool
```

### Process Results

```bash
# Process and summarize
python3 analysis/scripts/process_results.py \
    -d benchmarks/results \
    --summary
```

### Generate Plots

```bash
# Generate all analysis plots
python3 analysis/scripts/generate_plots.py \
    -d benchmarks/results \
    -o analysis/plots

# Open HTML report
open analysis/plots/report.html
```

### Plots Generated

1. **throughput_comparison.png** - Events/sec across languages
2. **latency_distribution.png** - Latency percentiles
3. **program_type_comparison.png** - Performance by eBPF type
4. **data_mechanism_comparison.png** - Ring buffer vs perf buffer
5. **performance_heatmap.png** - Language × Benchmark matrix
6. **cpu_usage_analysis.png** - CPU overhead
7. **duration_comparison.png** - Benchmark execution time

### Export to CSV

```bash
python3 analysis/scripts/process_results.py \
    -d benchmarks/results \
    -o results.csv
```

---

## Detailed Benchmark Descriptions

### Ring Buffer Throughput
Tests the maximum event throughput using modern ring buffers. Measures events/second for different attachment types.

```bash
sudo python3 src/python/ringbuf_throughput.py -d 60
```

**Expected Results:**
- C (libbpf): 200k-500k events/sec
- Python (BCC): 100k-300k events/sec
- Go: 150k-400k events/sec
- Rust (Aya): 200k-450k events/sec

### Map Operations
Benchmarks map performance: hash lookup/update, array operations, per-CPU maps.

```bash
make benchmark
# Then check: benchmarks/results/latest.json
```

### Latency Measurement
Measures end-to-end latency from kernel event to userspace delivery.

```bash
# Latency benchmarks included in make benchmark
# Results show P50, P95, P99 percentiles
```

---

## Troubleshooting

### Kernel eBPF Support
```bash
# Check tracepoint support
ls /sys/kernel/debug/tracing/events/syscalls/ | head

# Check kprobe support
sudo cat /sys/kernel/debug/kprobes/enabled

# Check ring buffer support (5.8+)
grep RINGBUF /boot/config-$(uname -r)
```

### Permission Denied
Most eBPF programs require root:
```bash
# Use sudo
sudo make benchmark

# Or enable unprivileged eBPF (not recommended for benchmarks)
sudo sysctl kernel.unprivileged_bpf_disabled=0
```

### Module Compilation Errors
If C programs fail to compile:
```bash
# Check clang installation
clang --version

# Verify LLVM
llvm-config --version

# Install missing headers
sudo apt-get install -y linux-headers-$(uname -r)
```

### BCC Import Errors
```bash
# Verify BCC installation
python3 -c "import bcc; print(bcc.__version__)"

# If not found, install:
sudo apt-get install -y python3-bcc libbcc
```

### Vagrant Issues

**VM fails to start:**
```bash
# Increase VM resources
export VAGRANT_MEMORY=4096
export VAGRANT_CPUS=4
vagrant up
```

**Shared folder not working:**
```bash
# Install VirtualBox guest additions
vagrant plugin install vagrant-vbguest
vagrant vbguest --do install
```

**Provision fails:**
```bash
# Re-run provisioning
vagrant provision

# Or start fresh
vagrant destroy -f
vagrant up
```

### Performance Issues

**Benchmarks too slow:**
- Reduce duration in config: `duration_seconds: 10`
- Reduce event frequency
- Use lighter load generator
- Run on native Linux (not VM) for realistic numbers

**Out of memory:**
- Reduce ring buffer size in programs
- Run with fewer concurrent benchmarks
- Check for memory leaks with: `sudo valgrind --leak-check=full`

---

## Next Steps

1. **Read the Documentation**
   - See `docs/EBPF_PROGRAM_TYPES.md` for detailed information on program types
   - See `docs/ARCHITECTURE.md` for design details

2. **Customize Benchmarks**
   - Edit `benchmarks/configs/benchmark_config.yaml`
   - Add new benchmark scenarios
   - Create custom load generators

3. **Extend with Your Programs**
   - Add your own eBPF programs to `src/c/`, `src/python/`, etc.
   - Register in benchmark configuration
   - Run comparative analysis

4. **Contribute**
   - Submit pull requests with improvements
   - Share benchmark results
   - Report issues

---

## Support and Resources

- **GitHub Issues**: https://github.com/yourusername/ebpf_benchmark/issues
- **eBPF Documentation**: https://ebpf.io/
- **Kernel BPF Docs**: https://www.kernel.org/doc/html/latest/userspace-api/ebpf/
- **BCC Documentation**: https://github.com/iovisor/bcc/
- **Aya Documentation**: https://docs.aya-rs.dev/

---

## License

MIT License - See LICENSE file for details
