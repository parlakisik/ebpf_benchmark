#!/bin/bash
# Don't exit on first error - some packages may not be available on ARM
set +e

echo "=== eBPF Benchmark VM Provisioning ==="
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

echo "Installing system dependencies..."
apt-get install -y \
    build-essential \
    git \
    vim \
    curl \
    wget \
    pkg-config \
    sudo

# Kernel headers and development
echo "Installing kernel headers and development tools..."
apt-get install -y \
    linux-headers-$(uname -r) \
    linux-image-generic \
    dkms \
    clang \
    llvm \
    libelf-dev \
    libz-dev \
    libzstd-dev

# Install linux-tools for bpftool
echo "Installing linux-tools..."
apt-get install -y \
    linux-tools-common \
    linux-tools-generic \
    linux-tools-$(uname -r) || echo "linux-tools installation may have failed on ARM"

# Verify kernel version (need 5.8+ for ring buffers)
KERNEL_VERSION=$(uname -r | cut -d. -f1-2)
echo "Kernel version: $KERNEL_VERSION"
if [ $(echo "$KERNEL_VERSION < 5.8" | bc) -eq 1 ]; then
    echo "Warning: Kernel version 5.8+ is recommended for ring buffers"
fi

# libbpf and kernel eBPF support
echo "Installing libbpf and kernel BPF support..."
apt-get install -y \
    libbpf-dev || echo "Note: libbpf-dev not available on this architecture"
# bpftool and libbpf1 may not be available on ARM, continuing anyway

# Python 3 and BCC
echo "Installing Python 3 and BCC..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv

# BCC and BCC tools installation
echo "Installing BCC tools and headers..."
apt-get install -y \
    bpfcc-tools \
    libbcc \
    libbcc-dev \
    linux-headers-$(uname -r) || echo "Note: BCC tools may not be fully available on this architecture"

# Python dependencies
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install \
    PyYAML \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    psutil \
    click \
    tabulate

# Go installation
echo "Installing Go..."
GO_VERSION="1.21.0"
HOST_ARCH=$(uname -m)
if [ "$HOST_ARCH" = "aarch64" ] || [ "$HOST_ARCH" = "arm64" ]; then
    GO_ARCH="linux-arm64"
else
    GO_ARCH="linux-amd64"
fi

if ! command -v go &> /dev/null; then
    cd /tmp
    wget https://go.dev/dl/go${GO_VERSION}.${GO_ARCH}.tar.gz
    tar -xzf go${GO_VERSION}.${GO_ARCH}.tar.gz -C /usr/local
    rm go${GO_VERSION}.${GO_ARCH}.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile
    echo 'export PATH=$PATH:/usr/local/go/bin' >> /root/.bashrc
    export PATH=$PATH:/usr/local/go/bin
fi

# Rust and Aya
echo "Installing Rust..."
if ! command -v rustup &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source /root/.cargo/env
fi

# Set up Rust in PATH for all users and shells
export PATH=$PATH:/root/.cargo/bin
echo 'export PATH=$PATH:/root/.cargo/bin' >> /etc/profile
echo 'export PATH=$PATH:/root/.cargo/bin' >> /etc/bash.bashrc
echo 'export PATH=$PATH:/root/.cargo/bin' >> /root/.bashrc

# Also create symlinks to make rustc/cargo accessible system-wide
ln -sf /root/.cargo/bin/rustc /usr/local/bin/rustc 2>/dev/null || true
ln -sf /root/.cargo/bin/cargo /usr/local/bin/cargo 2>/dev/null || true
ln -sf /root/.cargo/bin/rustup /usr/local/bin/rustup 2>/dev/null || true

# Install Aya (Rust eBPF framework)
echo "Installing Aya..."
/root/.cargo/bin/cargo install aya-gen --git https://github.com/aya-rs/aya.git 2>/dev/null || echo "Note: Aya install may have issues on ARM"

# Performance tools (some may not exist on ARM)
echo "Installing performance monitoring tools..."
apt-get install -y \
    sysstat \
    iotop \
    htop \
    stress \
    trace-cmd 2>/dev/null || true

# These may not exist on ARM
apt-get install -y perf-tools-unstable 2>/dev/null || echo "perf-tools-unstable not available"
apt-get install -y blktrace 2>/dev/null || echo "blktrace not available"

# Testing tools
echo "Installing testing tools..."
apt-get install -y \
    strace \
    tcpdump \
    netcat-traditional 2>/dev/null || true

apt-get install -y ltrace 2>/dev/null || echo "ltrace not available"

# Configure kernel for eBPF
echo "Configuring kernel parameters..."
cat >> /etc/sysctl.conf << EOF

# eBPF Configuration
kernel.unprivileged_bpf_disabled=0
kernel.bpf_stats_enabled=1
kernel.bpf_verbose=1
EOF

sysctl -p

# Enable BPF filesystem
echo "Enabling BPF filesystem..."
mkdir -p /sys/kernel/debug
mount -t debugfs none /sys/kernel/debug || true

# Verify eBPF support
echo "Verifying eBPF support..."
if [ -f /sys/kernel/debug/tracing/events/syscalls/sys_enter_open/enable ]; then
    echo "✓ Tracepoint support detected"
else
    echo "⚠ Tracepoint support not fully available"
fi

if [ -d /sys/kernel/debug/kprobes ]; then
    echo "✓ Kprobe support detected"
else
    echo "⚠ Kprobe support not fully available"
fi

# Create working directory
mkdir -p /root/ebpf_benchmark
cd /home/vagrant/ebpf_benchmark || true

echo "=== Provisioning Complete ==="
echo "Kernel version: $(uname -r)"
echo "Go version: $(go version 2>/dev/null || echo 'not installed')"
echo "Rust version: $(rustc --version 2>/dev/null || echo 'not installed')"
echo "Python version: $(python3 --version)"
echo "BCC version: $(python3 -c 'import bcc; print(bcc.__version__)' 2>/dev/null || echo 'not found')"
echo ""
echo "Ready for eBPF benchmarking!"
