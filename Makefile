.PHONY: help setup build build-c build-python build-golang build-rust clean test benchmark benchmark-c benchmark-python benchmark-golang benchmark-rust vagrant-up vagrant-down vagrant-provision

# Default target
help:
	@echo "eBPF Benchmark Suite - Available Targets:"
	@echo ""
	@echo "Setup & Build:"
	@echo "  make setup              - Create project directories"
	@echo "  make build              - Build all eBPF programs"
	@echo "  make build-c            - Build C (libbpf) programs"
	@echo "  make build-python       - Prepare Python environment"
	@echo "  make build-golang       - Build Go programs"
	@echo "  make build-rust         - Build Rust (Aya) programs"
	@echo ""
	@echo "Testing & Benchmarking:"
	@echo "  make test               - Run unit tests"
	@echo "  make benchmark          - Run all benchmarks"
	@echo "  make benchmark-c        - Run C benchmarks"
	@echo "  make benchmark-python   - Run Python benchmarks"
	@echo "  make benchmark-golang   - Run Go benchmarks"
	@echo "  make benchmark-rust     - Run Rust benchmarks"
	@echo ""
	@echo "Vagrant VM Management:"
	@echo "  make vagrant-up         - Start Vagrant VM"
	@echo "  make vagrant-down       - Stop Vagrant VM"
	@echo "  make vagrant-provision  - Re-run provisioning"
	@echo "  make vagrant-shell      - SSH into Vagrant VM"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean              - Remove build artifacts"
	@echo "  make clean-all          - Remove build artifacts and results"
	@echo "  make format             - Format code"
	@echo "  make lint               - Lint code"

# Variables
BUILD_DIR := build
VAGRANT_DIR := vagrant
SRC_DIR := src
BENCHMARK_DIR := benchmarks
ANALYSIS_DIR := analysis

# Setup target
setup:
	@echo "Creating project directories..."
	mkdir -p $(BUILD_DIR)
	mkdir -p $(BENCHMARK_DIR)/results
	mkdir -p $(ANALYSIS_DIR)/plots
	mkdir -p $(SRC_DIR)/{c/{programs,headers,userspace},python,golang,rust/{kernel,userspace}}
	@echo "✓ Project structure ready"

# Build all
build: build-c build-python build-golang build-rust
	@echo "✓ All builds complete"

# C eBPF Programs
build-c:
	@echo "Building C (libbpf) eBPF programs..."
	@if [ ! -f "$(SRC_DIR)/c/Makefile" ]; then \
		echo "⚠ C Makefile not found at $(SRC_DIR)/c/Makefile"; \
		echo "  Create it with appropriate clang/llvm build rules"; \
	else \
		$(MAKE) -C $(SRC_DIR)/c; \
	fi
	@echo "✓ C build complete"

# Python eBPF Programs
build-python:
	@echo "Setting up Python environment..."
	@if [ ! -d venv ]; then \
		python3 -m venv venv; \
		echo "✓ Virtual environment created"; \
	fi
	@if [ -f requirements.txt ]; then \
		./venv/bin/pip install -r requirements.txt; \
		echo "✓ Python dependencies installed"; \
	else \
		echo "⚠ requirements.txt not found"; \
	fi

# Go eBPF Programs
build-golang:
	@echo "Building Go (ebpf-go) programs..."
	@if command -v go >/dev/null 2>&1; then \
		cd $(SRC_DIR)/golang && \
		go build -o ../../$(BUILD_DIR)/go_ringbuf ringbuf_throughput.go common.go && \
		echo "✓ Go build complete"; \
	else \
		echo "⚠ Go not installed"; \
	fi

# Rust eBPF Programs
build-rust:
	@echo "Building Rust (Aya) programs..."
	@if command -v cargo >/dev/null 2>&1; then \
		cd $(SRC_DIR)/rust/userspace && \
		cargo build --release && \
		echo "✓ Rust build complete"; \
	else \
		echo "⚠ Rust not installed"; \
	fi

# Testing
test:
	@echo "Running tests..."
	@if [ -d tests ]; then \
		$(MAKE) -C tests test; \
	else \
		echo "⚠ No tests directory found"; \
	fi

# Benchmarking
benchmark: build
	@echo "Running all benchmarks..."
	@python3 run_all_benchmarks.py -d 10 -v
	@echo "✓ Benchmarks complete - results in $(BENCHMARK_DIR)/results/"

benchmark-c: build-c
	@echo "Running C benchmarks..."
	@python3 $(BENCHMARK_DIR)/harness/run_benchmarks.py --language c

benchmark-python: build-python
	@echo "Running Python benchmarks..."
	@python3 $(BENCHMARK_DIR)/harness/run_benchmarks.py --language python

benchmark-golang: build-golang
	@echo "Running Go benchmarks..."
	@python3 run_all_benchmarks.py -d 10 -v 2>&1 | grep -A 20 "Go Benchmark"

benchmark-rust: build-rust
	@echo "Running Rust benchmarks..."
	@python3 run_all_benchmarks.py -d 10 -v 2>&1 | grep -A 20 "Rust Benchmark"

# Quick benchmark (5 seconds each)
benchmark-quick: build
	@echo "Running quick benchmarks..."
	@python3 run_all_benchmarks.py -d 5 -v

# Vagrant targets
vagrant-up:
	@cd $(VAGRANT_DIR) && vagrant up
	@echo "✓ Vagrant VM started"

vagrant-down:
	@cd $(VAGRANT_DIR) && vagrant halt
	@echo "✓ Vagrant VM stopped"

vagrant-provision:
	@cd $(VAGRANT_DIR) && vagrant provision
	@echo "✓ Vagrant VM re-provisioned"

vagrant-shell:
	@cd $(VAGRANT_DIR) && vagrant ssh

# Code quality
format:
	@echo "Formatting C code..."
	@find $(SRC_DIR)/c -name "*.c" -o -name "*.h" | xargs -I {} clang-format -i {} 2>/dev/null || true
	@echo "Formatting Rust code..."
	@cd $(SRC_DIR)/rust && cargo fmt 2>/dev/null || true
	@echo "Formatting Python code..."
	@python3 -m black $(SRC_DIR)/python $(BENCHMARK_DIR) $(ANALYSIS_DIR) 2>/dev/null || true
	@echo "✓ Code formatted"

lint:
	@echo "Linting code..."
	@echo "  Python files..."
	@python3 -m pylint $(SRC_DIR)/python $(BENCHMARK_DIR) $(ANALYSIS_DIR) 2>/dev/null || true
	@echo "✓ Lint complete"

# Cleaning
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)/*
	@rm -rf $(BENCHMARK_DIR)/harness/__pycache__
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✓ Clean complete"

clean-all: clean
	@echo "Removing all results..."
	@rm -rf $(BENCHMARK_DIR)/results/*
	@rm -rf $(ANALYSIS_DIR)/plots/*
	@echo "✓ Full clean complete"

# Analysis
analyze:
	@echo "Generating analysis and plots..."
	@python3 $(ANALYSIS_DIR)/generate_report.py
	@echo "✓ Analysis complete - plots in $(ANALYSIS_DIR)/plots/"

# Utility targets
check-deps:
	@echo "Checking dependencies..."
	@command -v clang >/dev/null 2>&1 && echo "✓ clang" || echo "✗ clang"
	@command -v llvm-strip >/dev/null 2>&1 && echo "✓ llvm-strip" || echo "✗ llvm-strip"
	@command -v python3 >/dev/null 2>&1 && echo "✓ python3" || echo "✗ python3"
	@command -v go >/dev/null 2>&1 && echo "✓ go" || echo "✗ go"
	@command -v cargo >/dev/null 2>&1 && echo "✓ cargo" || echo "✗ cargo"
	@command -v vagrant >/dev/null 2>&1 && echo "✓ vagrant" || echo "✗ vagrant"

# Default
.DEFAULT_GOAL := help
