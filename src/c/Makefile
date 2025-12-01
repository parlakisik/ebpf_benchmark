# Makefile for C eBPF programs
#
# Compiles eBPF kernel programs using libbpf
# Generates .o (object) files for loading by userspace

# Compiler settings
CLANG ?= clang
LLC ?= llc
LLVM_STRIP ?= llvm-strip
BPFTOOL ?= bpftool

# Directories
OUTPUT := ../../build/c
VMLINUX_PATH ?= /sys/kernel/btf/vmlinux
VMLINUX_H := ./vmlinux.h

# Kernel version
KERNEL_VERSION := $(shell uname -r)
KERNEL_MAJOR := $(shell uname -r | cut -d. -f1)
KERNEL_MINOR := $(shell uname -r | cut -d. -f2)

# Compiler flags
INCLUDES := -I/usr/include/bpf -Iheaders -I.
CLANG_BPF_SYS_INCLUDES := $(shell clang -print-resource-dir)/include
CLANG_BPF_INCLUDES := -I$(CLANG_BPF_SYS_INCLUDES)

# Add architecture-specific include paths for ARM and other architectures
ARCH := $(shell uname -m)
ifeq ($(ARCH),aarch64)
	ARCH_INCLUDES := -I/usr/include/aarch64-linux-gnu
	ARCH_DEFINES := -D__TARGET_ARCH_arm64
else ifeq ($(ARCH),arm64)
	ARCH_INCLUDES := -I/usr/include/aarch64-linux-gnu
	ARCH_DEFINES := -D__TARGET_ARCH_arm64
else ifeq ($(ARCH),x86_64)
	ARCH_INCLUDES := -I/usr/include/x86_64-linux-gnu
	ARCH_DEFINES := -D__TARGET_ARCH_x86_64
else
	ARCH_DEFINES := -D__TARGET_ARCH_x86_64
endif

# Compilation flags for eBPF programs
CLANG_BPF_FLAGS := -g -O2 -target bpf $(CLANG_BPF_INCLUDES) $(ARCH_INCLUDES) $(ARCH_DEFINES) $(INCLUDES)

# C programs to compile
PROGRAMS := \
	programs/ringbuf_throughput \
	programs/perfbuf_throughput \
	programs/map_operations

# Default target
.PHONY: all clean vmlinux setup

all: setup vmlinux $(addprefix $(OUTPUT)/,$(addsuffix .o,$(PROGRAMS)))
	@echo "✓ All C eBPF programs compiled"

setup:
	@mkdir -p $(OUTPUT)
	@echo "✓ Output directory ready"

# Generate vmlinux.h from kernel BTF
vmlinux: $(VMLINUX_H)

$(VMLINUX_H): setup
	@if [ -f $(VMLINUX_PATH) ]; then \
		echo "Generating vmlinux.h from kernel BTF..."; \
		$(BPFTOOL) btf dump file $(VMLINUX_PATH) format c > $@; \
		echo "✓ vmlinux.h generated"; \
	else \
		echo "⚠ Kernel BTF not available at $(VMLINUX_PATH)"; \
		echo "  This is normal on kernels < 5.2"; \
		echo "  Falling back to manual definitions"; \
		touch $@; \
	fi

# Compile eBPF programs
# Rule: programs/name.c -> build/c/programs/name.o
$(OUTPUT)/programs/%.o: programs/%.c $(VMLINUX_H)
	@echo "Compiling $<..."
	@mkdir -p $(dir $@)
	$(CLANG) $(CLANG_BPF_FLAGS) -emit-llvm -c $< -o $(@:.o=.ll)
	$(LLC) -march=bpf -filetype=obj -o $@ $(@:.o=.ll)
	$(LLVM_STRIP) -g $@
	@rm -f $(@:.o=.ll)
	@echo "  ✓ $@"

# Generate skeleton header (optional, for advanced use)
%.skel.h: $(OUTPUT)/%.o
	$(BPFTOOL) gen object $(OUTPUT)/$*.skel.h $<

# Verify kernel capabilities
verify-kernel:
	@echo "Kernel version: $(KERNEL_VERSION)"
	@echo "Checking eBPF support..."
	@if grep -q "kprobes" /boot/config-$(KERNEL_VERSION) 2>/dev/null || [ -f /sys/kernel/debug/kprobes/enabled ]; then \
		echo "  ✓ kprobes enabled"; \
	else \
		echo "  ✗ kprobes not available"; \
	fi
	@if [ -f /sys/kernel/debug/tracing/events/syscalls/sys_enter_open/enable ]; then \
		echo "  ✓ Tracepoints enabled"; \
	else \
		echo "  ✗ Tracepoints not available"; \
	fi
	@if [ -d /sys/kernel/debug/bpf ]; then \
		echo "  ✓ BPF filesystem available"; \
	else \
		echo "  ✗ BPF filesystem not mounted"; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning C build artifacts..."
	@rm -rf $(OUTPUT)
	@rm -f $(VMLINUX_H)
	@echo "✓ Clean complete"

# Help target
help:
	@echo "C eBPF Build System"
	@echo ""
	@echo "Targets:"
	@echo "  make all           - Compile all eBPF programs"
	@echo "  make vmlinux       - Generate vmlinux.h from kernel BTF"
	@echo "  make verify-kernel - Check kernel eBPF capabilities"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make help          - Show this help message"
	@echo ""
	@echo "Configuration:"
	@echo "  CLANG        - Clang compiler (default: clang)"
	@echo "  LLC          - LLVM compiler (default: llc)"
	@echo "  LLVM_STRIP   - LLVM strip tool (default: llvm-strip)"
	@echo "  BPFTOOL      - BPF tool (default: bpftool)"
	@echo "  KERNEL_VERSION - Current kernel: $(KERNEL_VERSION)"

.DEFAULT_GOAL := all

# Phony targets
.PHONY: all clean setup verify-kernel help vmlinux
