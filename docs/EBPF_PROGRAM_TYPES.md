# eBPF Program Types and Mechanisms Reference

This document comprehensively covers all eBPF program types and data transfer mechanisms that will be benchmarked.

## Table of Contents
1. [Program Types](#program-types)
2. [Data Transfer Mechanisms](#data-transfer-mechanisms)
3. [Map Types](#map-types)
4. [Benchmark Coverage](#benchmark-coverage)

---

## Program Types

### 1. Tracing Program Types

#### 1.1 kprobes (Kernel Probes)
- **Type**: `BPF_PROG_TYPE_KPROBE`
- **Description**: Dynamic instrumentation of kernel functions at entry/exit
- **Use Cases**: Function call tracing, argument capture, latency measurement
- **Key Details**:
  - Entry (kprobe): At function entry, can read arguments (via kprobe context)
  - Return (kretprobe): At function return, can read return value
  - Zero-overhead when no attachments
  - Support for multiple simultaneous kprobes on same function
- **Example**: `kprobe:sys_openat`, `kretprobe:do_sys_open`
- **Performance Impact**: Medium (depends on hotness of traced function)

#### 1.2 Tracepoints (Static Kernel Instrumentation)
- **Type**: `BPF_PROG_TYPE_TRACEPOINT`
- **Description**: Static instrumentation points defined in kernel source
- **Use Cases**: Standardized event tracing, stable kernel API
- **Key Details**:
  - Pre-compiled into kernel at compile time
  - Lower overhead than kprobes
  - Access to structured event data
  - More stable across kernel versions than kprobes
  - Available for: syscalls, sched, filesystem, network, etc.
- **Example**: `tracepoint:syscalls:sys_enter_open`, `tracepoint:sched:sched_switch`
- **Performance Impact**: Low (optimized kernel instrumentation)

#### 1.3 Raw Tracepoints
- **Type**: `BPF_PROG_TYPE_RAW_TRACEPOINT`
- **Description**: Direct access to kernel trace event data without context conversion
- **Use Cases**: Low-latency tracing, minimal overhead
- **Key Details**:
  - No buffer allocation in kernel
  - Direct register access
  - Requires intimate kernel knowledge
  - Faster than regular tracepoints for high-volume events
  - Limited error handling
- **Example**: `raw_tracepoint:sys_enter`, `raw_tracepoint:sched_wakeup`
- **Performance Impact**: Very Low (direct kernel instrumentation)

#### 1.4 uprobes (Userspace Probes)
- **Type**: `BPF_PROG_TYPE_KPROBE` (same type, different attachment)
- **Description**: Dynamic instrumentation of userspace functions
- **Use Cases**: Application tracing, library function instrumentation
- **Key Details**:
  - Attaches to userspace function entry/exit
  - Requires symbol lookup
  - Higher overhead than kprobes (context switch)
  - Binary patching approach (breakpoint-based on older kernels)
  - Performance depends on traced function hotness
- **Example**: `uprobe:/usr/bin/bash:main`, `uretprobe:/lib/libc.so:malloc`
- **Performance Impact**: High (involves context switches)

#### 1.5 USDT (Userspace Statically Defined Tracepoints)
- **Type**: `BPF_PROG_TYPE_KPROBE` (semi_provider-based)
- **Description**: Application-defined tracepoints compiled into binaries
- **Use Cases**: Application-level observability, efficient app tracing
- **Key Details**:
  - Defined by application developers (STAP probes)
  - Low overhead when disabled (NOP instructions)
  - Requires application support (not all apps have USDT)
  - Very stable across application versions
  - Pre-calculated entry points
- **Example**: `usdt:nodejs:http:request`, `usdt:postgresql:lock:acquired`
- **Performance Impact**: Very Low (when disabled), Medium (when active)

---

### 2. Network Processing Program Types

#### 2.1 XDP (eXpress Data Path)
- **Type**: `BPF_PROG_TYPE_XDP`
- **Description**: Packet processing at driver level, before kernel network stack
- **Use Cases**: DDoS mitigation, load balancing, packet filtering, forwarding
- **Key Details**:
  - Runs in driver or NIC firmware
  - Can execute before memory allocation
  - Return codes: XDP_DROP, XDP_PASS, XDP_TX, XDP_REDIRECT
  - Access to packet buffer via `xdp_md` context
  - Per-NIC attachment
  - Supports XDP maps for data sharing
- **Performance Impact**: Very Low (hardware-based)
- **Kernel Requirement**: 4.8+

#### 2.2 TC (Traffic Control) / Classifier
- **Type**: `BPF_PROG_TYPE_SCHED_CLS`
- **Description**: Packet classification and filtering at qdisc level
- **Use Cases**: Traffic shaping, QoS, packet filtering, rerouting
- **Key Details**:
  - Operates on skb (socket buffer) objects
  - Can modify packet headers/data
  - Return codes: TC_ACT_OK, TC_ACT_RECLASSIFY, TC_ACT_SHOT, etc.
  - Attached to network interface via `tc` command
  - More flexible than XDP but slightly more overhead
  - Can access full packet content
- **Performance Impact**: Low (still in fast path)

#### 2.3 Socket Operations
- **Type**: `BPF_PROG_TYPE_SOCK_OPS`
- **Description**: Monitoring and controlling TCP socket operations
- **Use Cases**: TCP congestion control, socket behavior monitoring
- **Key Details**:
  - Hooks into TCP state machine
  - Can read/write socket options
  - Can modify TCP behavior
  - Returns bpf_sock_ops_t context
- **Performance Impact**: Low (TCP fast path)

#### 2.4 Socket Filter
- **Type**: `BPF_PROG_TYPE_SOCKET_FILTER`
- **Description**: Packet filtering at socket level (like traditional BPF)
- **Use Cases**: Packet filtering, monitoring
- **Key Details**:
  - Operates on received packets before socket delivery
  - Returns verdict (accept/drop)
  - Lower performance priority than XDP
  - Good for monitoring specific sockets
- **Performance Impact**: Medium

---

### 3. Performance Monitoring Program Types

#### 3.1 Perf Events
- **Type**: `BPF_PROG_TYPE_PERF_EVENT`
- **Description**: CPU performance counter event sampling
- **Use Cases**: Performance profiling, cycle-accurate sampling, bottleneck detection
- **Key Details**:
  - Attached to perf_event subsystem
  - Triggered by CPU performance counter overflows
  - Can read CPU registers, stack traces
  - Context: `bpf_perf_event_data` with CPU state
  - Highly configurable sampling rates
  - Supports hardware and software events
- **Event Examples**: CPU_CYCLES, CACHE_MISSES, BRANCH_MISSES, etc.
- **Performance Impact**: Medium (depends on sampling frequency)

#### 3.2 Ring Buffer Sampling
- **Type**: `BPF_PROG_TYPE_PERF_EVENT` (variant)
- **Description**: Periodic sampling to ring buffer
- **Use Cases**: Continuous profile collection, flame graph generation
- **Key Details**:
  - Sample every Nth event
  - Ring buffer output
  - Stack unwinding in kernel
  - Can collect kernel + userspace stacks
- **Performance Impact**: Medium-Low (configurable)

---

## Data Transfer Mechanisms

### 1. Ring Buffers (Modern)

#### 1.1 BPF_MAP_TYPE_RINGBUF
- **Introduced**: Linux 5.8
- **Description**: Single efficient ring buffer for kernel-to-userspace communication
- **Characteristics**:
  - Single shared buffer (not per-CPU)
  - Lock-free reads and writes
  - Automatic overflow handling (overwrites oldest data)
  - Zero-copy in both directions
  - Ordered event delivery
  - Memory efficient
  - Supports variable-sized records
- **API**:
  ```c
  bpf_ringbuf_output(map, data, size, 0)  // submit data
  bpf_ringbuf_reserve(map, size, 0)       // reserve space (atomically)
  ```
- **Userspace API**:
  ```c
  ring_buffer__new()
  ring_buffer__add()
  ring_buffer__poll()
  ```
- **Performance**: Excellent for high-frequency events
- **Memory**: O(ring_buffer_size) total
- **Throughput**: 100k+ events/sec typical

---

### 2. Perf Buffers (Legacy but Still Useful)

#### 2.1 BPF_MAP_TYPE_PERF_BUFFER
- **Description**: Per-CPU ring buffers for kernel-to-userspace communication
- **Characteristics**:
  - One buffer per CPU (cache-friendly)
  - Uses BPF_PERF_OUTPUT() macro
  - Separate memory per core
  - Slightly higher overhead per event
  - Good cache locality
  - Fixed-size records
  - Can lose events under extreme load
- **API**:
  ```c
  bpf_perf_event_output(ctx, map, BPF_F_CURRENT_CPU, data, size)
  ```
- **Userspace API**:
  ```c
  perf_buffer__new()
  perf_buffer__add_channel()
  perf_buffer__poll()
  ```
- **Performance**: Good for moderate frequency events
- **Memory**: O(ring_buffer_size * num_cpus)
- **Throughput**: 50k+ events/sec per core
- **Deprecation Note**: Ring buffers are preferred in newer code

---

### 3. Maps (Kernel-Userspace Data Sharing)

#### 3.1 Hash Maps (BPF_MAP_TYPE_HASH)
- **Description**: Generic key-value hash table
- **Characteristics**:
  - Dynamic sizing
  - O(1) average lookup
  - Preallocation optional
  - Atomic operations support
  - Per-element timeout (BPF_MAP_TYPE_HASH_OF_MAPS)
- **Use Cases**: State tracking, aggregation, filtering
- **Operations**:
  - `bpf_map_lookup_elem()`
  - `bpf_map_update_elem()`
  - `bpf_map_delete_elem()`
- **Performance**: Fast for small keys/values, contention at high frequencies

#### 3.2 Array Maps (BPF_MAP_TYPE_ARRAY)
- **Description**: Fixed-size array with integer indices
- **Characteristics**:
  - Preallocated
  - O(1) access
  - Fastest map type
  - Memory efficient
  - Good for counters and accumulators
- **Use Cases**: Statistics, counters, fixed-size data
- **Operations**:
  - `bpf_map_lookup_elem()`
  - `bpf_map_update_elem()` (atomic add)
- **Performance**: Excellent, minimal contention

#### 3.3 Per-CPU Maps
- **BPF_MAP_TYPE_PERCPU_ARRAY**: Per-CPU array
- **BPF_MAP_TYPE_PERCPU_HASH**: Per-CPU hash
- **Characteristics**:
  - One value per CPU
  - No lock required
  - Eliminates cache line bouncing
  - Require aggregation on read
- **Performance**: Excellent for high-frequency updates
- **Use Cases**: Statistics aggregation, thread-local storage

#### 3.4 Specialized Maps
- **BPF_MAP_TYPE_LRU_HASH**: Hash with LRU eviction
- **BPF_MAP_TYPE_STACK_TRACE**: Stack trace storage
- **BPF_MAP_TYPE_ARRAY_OF_MAPS**: Nested map support
- **BPF_MAP_TYPE_HASH_OF_MAPS**: Dynamic map composition

---

### 4. Stack Traces

#### 4.1 Stack Trace Collection
- **Map Type**: `BPF_MAP_TYPE_STACK_TRACE`
- **Description**: Kernel and userspace stack collection
- **Characteristics**:
  - `bpf_get_stackid()` to collect stacks
  - Automatic deduplication
  - Userspace unwinding support
  - Per-CPU or global stacks
- **Use Cases**: Profiling, flame graph generation, root cause analysis
- **Performance**: Medium overhead (requires stack walking)

#### 4.2 Performance Implications
- Kernel unwinding: 10-100 µs per stack
- Userspace unwinding: 100-1000 µs (done in userspace)
- DWARF parsing overhead

---

## Map Types

### Complete Reference

| Map Type | Key Size | Val Size | Max Size | Per-CPU | Operations | Use Case |
|----------|----------|----------|----------|---------|-----------|----------|
| ARRAY | 4 | Any | Pre-alloc | No | Fast lookup | Counters, stats |
| HASH | Any | Any | Dynamic | No | Standard ops | KV store |
| RINGBUF | N/A | Any | Pre-alloc | Single | Reserve/submit | Event stream |
| PERFBUF | N/A | Fixed | Pre-alloc | Yes | Output | High-freq events |
| STACK_TRACE | Idx | Stack | Pre-alloc | No | GetStackID | Call stacks |
| PROG_ARRAY | 4 | ProgFD | Pre-alloc | No | TailCall | Program dispatch |
| DEVMAP | 4 | DevIdx | Pre-alloc | No | Redirect | XDP redirect |
| SOCKMAP | Sockhash | SockOps | Pre-alloc | No | Redirect | Socket ops |
| CGROUP_ARRAY | 4 | CGrpFD | Pre-alloc | No | Check | Cgroup ops |
| QUEUE | N/A | Any | Pre-alloc | No | Pop/Push | FIFO queue |
| BLOOM_FILTER | N/A | Val | Pre-alloc | No | Lookup | Probabilistic set |

---

## Benchmark Coverage

### Phase 1: Core Benchmarks

```yaml
ring_buffer_throughput:
  - Program Type: kprobe or tracepoint
  - Data Mechanism: Ring Buffer
  - Metric: Events/second, MB/s
  - Load: sys_enter syscalls

ring_buffer_latency:
  - Program Type: kprobe
  - Data Mechanism: Ring Buffer
  - Metric: Time from event to userspace (µs)
  - Percentiles: P50, P95, P99, P99.9

perf_buffer_throughput:
  - Program Type: tracepoint
  - Data Mechanism: Perf Buffer
  - Metric: Events/second (per-CPU)
  - Load: Syscall flood

kprobe_overhead:
  - Program Type: kprobe on hot function
  - Data Mechanism: Simple counter map
  - Metric: CPU overhead %
  - Comparison: With vs without kprobe

tracepoint_overhead:
  - Program Type: tracepoint
  - Data Mechanism: Array map update
  - Metric: CPU overhead %
  - Comparison: With vs without tracepoint

xdp_packet_processing:
  - Program Type: XDP
  - Data Mechanism: Ring buffer events
  - Metric: Packets/second, latency
  - Load: Packet generation

map_operation_latency:
  - Program Type: Raw tracepoint
  - Data Mechanism: Hash/Array map operations
  - Metric: Map operation time (ns)
  - Operations: Lookup, update, delete
```

### Phase 2: Advanced Benchmarks

```yaml
uprobe_userspace_tracing:
  - Program Type: uprobe
  - Data Mechanism: Ring buffer
  - Metric: Userspace event latency

stack_trace_collection:
  - Program Type: perf_event
  - Data Mechanism: Stack trace maps
  - Metric: Stack trace collection overhead

multi_program_attachment:
  - Program Type: Multiple on same event
  - Data Mechanism: Ring buffer
  - Metric: Impact of multiple programs

tc_packet_classification:
  - Program Type: TC classifier
  - Data Mechanism: Array map lookup
  - Metric: Packet filtering throughput

memory_usage_analysis:
  - All program types
  - Metric: Kernel memory footprint
  - Tool: /proc/meminfo, etc.
```

---

## Performance Characteristics Summary

### Throughput (Events/sec)

| Mechanism | Typical Throughput | Peak Throughput | Data Mechanism |
|-----------|-------------------|-----------------|-----------------|
| Ring Buffer | 100k-500k | 1M+ | Modern kernel |
| Perf Buffer | 50k-250k/CPU | 500k/CPU | Per-CPU |
| Syscall Events | Depends on syscall | 10k-100k | Syscall rate |
| XDP | 1M+ packets/sec | 10M+ | Hardware |
| Stack Traces | 10k-100k | Variable | DWARF |

### Latency (kernel to userspace)

| Program Type | Typical Latency | Best Case | Worst Case |
|--------------|-----------------|-----------|-----------|
| Kprobe | 1-10 µs | <1 µs | 100+ µs |
| Tracepoint | 0.5-5 µs | <0.5 µs | 50 µs |
| Raw TP | 0.2-2 µs | <0.2 µs | 20 µs |
| Uprobe | 10-100 µs | 5 µs | 1000+ µs |
| XDP | 0.1-1 µs | <0.1 µs | 5 µs |

---

## References

- [kernel.org BPF Documentation](https://www.kernel.org/doc/html/latest/userspace-api/ebpf/index.html)
- [BPF Ring Buffer (lwn.net)](https://lwn.net/Articles/822542/)
- [eBPF Map Types Guide](https://www.kernel.org/doc/html/latest/userspace-api/ebpf/maps.html)
- [XDP Specification](https://www.kernel.org/doc/html/latest/networking/filter.html)
