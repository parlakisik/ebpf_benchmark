/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/*
 * Ring Buffer Throughput Benchmark
 *
 * This eBPF program measures ring buffer throughput by tracing
 * high-frequency syscalls and recording events to ring buffer.
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>  /* For PT_REGS_PARM macros */
#include "../headers/benchmark.h"

/* Ring buffer map for event submission */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} ringbuf_events SEC(".maps");

/* Simple counter for statistics */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 10);
} counters SEC(".maps");

/**
 * kprobe_handler - Trace sys_enter_openat syscall
 *
 * This is called every time a process calls open() or openat()
 * Records event to ring buffer for latency measurement
 */
SEC("kprobe/do_sys_openat2")
int kprobe_openat(struct pt_regs *ctx)
{
    struct event *e;
    __u32 zero = 0;

    /* Reserve space in ring buffer */
    e = bpf_ringbuf_reserve(&ringbuf_events, sizeof(*e), 0);
    if (!e)
        return 1;

    /* Fill event structure */
    e->timestamp = bpf_ktime_get_ns();
    e->pid = bpf_get_current_uid_gid() >> 32;
    e->cpu_id = bpf_get_smp_processor_id();
    e->event_type = EVENT_TYPE_KPROBE;
    /* On ARM64, use first argument register - varies by architecture */
    e->data = PT_REGS_PARM1(ctx);

    /* Submit event */
    bpf_ringbuf_submit(e, 0);

    /* Update counter */
    __u64 *counter = bpf_map_lookup_elem(&counters, &zero);
    if (counter)
        __sync_fetch_and_add(counter, 1);

    return 0;
}

/**
 * tracepoint_handler - Trace sys_enter_openat via tracepoint
 *
 * Alternative implementation using static tracepoint instead of kprobe
 * Should have lower overhead than kprobe version
 */
SEC("tp/syscalls/sys_enter_openat")
int tracepoint_openat(struct trace_event_raw_sys_enter *ctx)
{
    struct event *e;
    __u32 one = 1;

    /* Reserve space in ring buffer */
    e = bpf_ringbuf_reserve(&ringbuf_events, sizeof(*e), 0);
    if (!e)
        return 1;

    /* Fill event structure */
    e->timestamp = bpf_ktime_get_ns();
    e->pid = bpf_get_current_uid_gid() >> 32;
    e->cpu_id = bpf_get_smp_processor_id();
    e->event_type = EVENT_TYPE_TRACEPOINT;
    e->data = ctx->args[1]; /* Flags argument */

    /* Submit event */
    bpf_ringbuf_submit(e, 0);

    /* Update counter */
    __u64 *counter = bpf_map_lookup_elem(&counters, &one);
    if (counter)
        __sync_fetch_and_add(counter, 1);

    return 0;
}

/**
 * raw_tracepoint_handler - Raw tracepoint version
 *
 * Direct kernel event access with minimal overhead
 * Requires knowledge of kernel structures
 */
SEC("raw_tp/sys_enter")
int raw_tracepoint_handler(struct bpf_raw_tracepoint_args *ctx)
{
    struct event *e;
    __u32 two = 2;

    /* Reserve space in ring buffer */
    e = bpf_ringbuf_reserve(&ringbuf_events, sizeof(*e), 0);
    if (!e)
        return 1;

    /* Fill event structure with minimal data */
    e->timestamp = bpf_ktime_get_ns();
    e->pid = bpf_get_current_uid_gid() >> 32;
    e->cpu_id = bpf_get_smp_processor_id();
    e->event_type = EVENT_TYPE_TRACEPOINT;
    e->data = 0;

    /* Submit event */
    bpf_ringbuf_submit(e, 0);

    /* Update counter */
    __u64 *counter = bpf_map_lookup_elem(&counters, &two);
    if (counter)
        __sync_fetch_and_add(counter, 1);

    return 0;
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";
