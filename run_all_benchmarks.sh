#!/bin/bash
# Run all eBPF benchmarks and collect results

DURATION=10
RESULTS_DIR="/tmp/benchmark_results"
mkdir -p "$RESULTS_DIR"

echo "=========================================="
echo "eBPF Benchmark Suite - Running All Tests"
echo "=========================================="
echo "Duration: $DURATION seconds per test"
echo ""

# C Benchmark
echo "Running C Benchmark..."
sudo /home/vagrant/ebpf_benchmark/build/c/ringbuf_throughput -d $DURATION > "$RESULTS_DIR/c_result.txt" 2>&1
echo "C Benchmark Complete"
echo ""

# Go Benchmark
echo "Running Go Benchmark..."
/home/vagrant/ebpf_benchmark/build/go/ringbuf_throughput -d $DURATION > "$RESULTS_DIR/go_result.txt" 2>&1
echo "Go Benchmark Complete"
echo ""

# Rust Benchmark
echo "Running Rust Benchmark..."
/home/vagrant/ebpf_benchmark/build/rust/ringbuf_throughput -d $DURATION > "$RESULTS_DIR/rust_result.txt" 2>&1
echo "Rust Benchmark Complete"
echo ""

# Python Benchmark
echo "Running Python Benchmark..."
sudo python3 -m src.python.ringbuf_throughput -d $DURATION -v > "$RESULTS_DIR/python_result.txt" 2>&1
echo "Python Benchmark Complete"
echo ""

echo "=========================================="
echo "Benchmark Results Summary"
echo "=========================================="
echo ""

echo "=== C Benchmark ==="
grep -E "(Duration|Events|Throughput|Lost)" "$RESULTS_DIR/c_result.txt" || cat "$RESULTS_DIR/c_result.txt"
echo ""

echo "=== Go Benchmark ==="
grep -E "(Duration|Events|Throughput|Lost)" "$RESULTS_DIR/go_result.txt" || cat "$RESULTS_DIR/go_result.txt"
echo ""

echo "=== Rust Benchmark ==="
grep -E "(Duration|Events|Throughput|Lost)" "$RESULTS_DIR/rust_result.txt" || cat "$RESULTS_DIR/rust_result.txt"
echo ""

echo "=== Python Benchmark ==="
grep -E "(Duration|Events|Throughput|Lost)" "$RESULTS_DIR/python_result.txt" || cat "$RESULTS_DIR/python_result.txt"
echo ""

echo "=========================================="
echo "All Results saved to: $RESULTS_DIR"
echo "=========================================="
