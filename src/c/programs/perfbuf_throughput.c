/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/*
 * Perf Buffer Throughput Benchmark
 *
 * This eBPF program measures perf buffer throughput (legacy but still useful)
 * Compares with ring buffer implementation
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>  /* For PT_REGS_PARM macros */
#include "../headers/benchmark.h"

/* Per-CPU buffer for event submission */
struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(max_entries, 256);
} perf_events SEC(".maps");

/* Counter for event statistics */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 10);
} counters SEC(".maps");

/**
 * Simplified event for perf buffer (fixed-size)
 * Note: renamed to avoid collision with kernel's struct perf_event
 */
struct benchmark_perf_event {
    __u64 timestamp;
    __u32 pid;
    __u32 cpu_id;
    __u32 event_type;
    __u32 data;
};

/**
 * kprobe_perf - Trace syscall via kprobe, submit to perf buffer
 *
 * Uses BPF_PERF_OUTPUT which maps to perf buffer
 */
SEC("kprobe/do_sys_openat2")
int kprobe_perf(struct pt_regs *ctx)
{
    struct benchmark_perf_event event = {};
    __u32 zero = 0;

    /* Fill event structure */
    event.timestamp = bpf_ktime_get_ns();
    event.pid = bpf_get_current_uid_gid() >> 32;
    event.cpu_id = bpf_get_smp_processor_id();
    event.event_type = EVENT_TYPE_KPROBE;
    event.data = PT_REGS_PARM1(ctx);

    /* Submit to per-CPU perf buffer */
    bpf_perf_event_output(ctx, &perf_events, BPF_F_CURRENT_CPU, &event, sizeof(event));

    /* Update counter */
    __u64 *counter = bpf_map_lookup_elem(&counters, &zero);
    if (counter)
        __sync_fetch_and_add(counter, 1);

    return 0;
}

/**
 * tracepoint_perf - Trace syscall via tracepoint, submit to perf buffer
 */
SEC("tp/syscalls/sys_enter_openat")
int tracepoint_perf(struct trace_event_raw_sys_enter *ctx)
{
    struct benchmark_perf_event event = {};
    __u32 one = 1;

    /* Fill event structure */
    event.timestamp = bpf_ktime_get_ns();
    event.pid = bpf_get_current_uid_gid() >> 32;
    event.cpu_id = bpf_get_smp_processor_id();
    event.event_type = EVENT_TYPE_TRACEPOINT;
    event.data = ctx->args[1];

    /* Submit to per-CPU perf buffer */
    bpf_perf_event_output(ctx, &perf_events, BPF_F_CURRENT_CPU, &event, sizeof(event));

    /* Update counter */
    __u64 *counter = bpf_map_lookup_elem(&counters, &one);
    if (counter)
        __sync_fetch_and_add(counter, 1);

    return 0;
}

/**
 * raw_tracepoint_perf - Raw tracepoint with perf buffer
 *
 * Note: raw_tp doesn't have bpf_perf_event_output equivalent
 * This demonstrates the limitation of raw_tp for event submission
 */
SEC("raw_tp/sys_enter")
int raw_tracepoint_perf(struct bpf_raw_tracepoint_args *ctx)
{
    struct benchmark_perf_event event = {};
    __u32 two = 2;

    /* Fill event structure */
    event.timestamp = bpf_ktime_get_ns();
    event.pid = bpf_get_current_uid_gid() >> 32;
    event.cpu_id = bpf_get_smp_processor_id();
    event.event_type = EVENT_TYPE_TRACEPOINT;
    event.data = 0;

    /* For raw_tp, we must use helper differently or fall back to map */
    /* Note: raw_tp context is less feature-rich than regular tracepoint */

    /* Update counter instead (raw_tp doesn't work with bpf_perf_event_output) */
    __u64 *counter = bpf_map_lookup_elem(&counters, &two);
    if (counter)
        __sync_fetch_and_add(counter, 1);

    return 0;
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";
