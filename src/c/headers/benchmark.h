#ifndef __BENCHMARK_H__
#define __BENCHMARK_H__

/* Note: This header is used by both eBPF programs and user-space code.
 * eBPF programs (target bpf) will have vmlinux.h included first, which provides kernel types.
 * User-space code will define standard types.
 */
#if defined(__KERNEL__) || defined(__BPF__)
/* For eBPF and kernel code, types come from vmlinux.h */
/* Types are already defined: __u64, __u32, etc. */
#else
/* For user-space code */
#include <stdint.h>
typedef uint64_t __u64;
typedef uint32_t __u32;
#endif

/* Event structure for ring buffer */
struct event {
    __u64 timestamp;      /* Kernel timestamp */
    __u32 pid;            /* Process ID */
    __u32 cpu_id;         /* CPU ID */
    __u32 event_type;     /* Type of event */
    __u32 data;           /* Generic data field */
};

/* Statistics structure for hash maps */
struct stats {
    __u64 count;          /* Event count */
    __u64 sum_latency;    /* Sum of latencies */
    __u64 min_latency;    /* Minimum latency */
    __u64 max_latency;    /* Maximum latency */
};

/* Ring buffer map name - will be created by userspace */
#define RINGBUF_MAP_NAME "ringbuf_events"
#define PERF_MAP_NAME "perf_events"
#define STATS_MAP_NAME "stats"
#define COUNTER_MAP_NAME "counters"

/* Event types */
#define EVENT_TYPE_KPROBE 1
#define EVENT_TYPE_TRACEPOINT 2
#define EVENT_TYPE_UPROBE 3
#define EVENT_TYPE_XDP 4
#define EVENT_TYPE_TC 5

#endif /* __BENCHMARK_H__ */
