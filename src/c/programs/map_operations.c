/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/*
 * Map Operations Benchmark
 *
 * This program benchmarks various map operations:
 * - Hash map lookup/update/delete
 * - Array map operations
 * - Per-CPU map operations
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include "../headers/benchmark.h"

/* Hash map for key-value operations */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 10240);
} hash_map SEC(".maps");

/* Array map for fixed-size lookups */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 256);
} array_map SEC(".maps");

/* Per-CPU array for lock-free statistics */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 256);
} percpu_array SEC(".maps");

/* Per-CPU hash for statistics without lock contention */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_HASH);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 1024);
} percpu_hash SEC(".maps");

/* Ring buffer for latency measurement */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} ringbuf_events SEC(".maps");

/* Latency measurement event */
struct latency_event {
    __u64 timestamp_start;
    __u64 timestamp_end;
    __u32 operation;  /* 0=hash_lookup, 1=hash_update, 2=array_lookup, etc */
    __u32 pid;
};

/**
 * hash_map_lookup_benchmark - Measure hash map lookup latency
 *
 * Traces sys_openat and performs hash map lookup
 */
SEC("tp/syscalls/sys_enter_openat")
int hash_map_lookup(struct trace_event_raw_sys_enter *ctx)
{
    __u32 key = (bpf_get_current_pid_uid() >> 32) & 0xFF;
    __u64 start = bpf_ktime_get_ns();

    /* Perform hash map lookup */
    __u64 *val = bpf_map_lookup_elem(&hash_map, &key);

    __u64 end = bpf_ktime_get_ns();

    /* Record latency */
    struct latency_event *e = bpf_ringbuf_reserve(&ringbuf_events, sizeof(*e), 0);
    if (!e)
        return 1;

    e->timestamp_start = start;
    e->timestamp_end = end;
    e->operation = 0;  /* Hash lookup */
    e->pid = bpf_get_current_pid_uid() >> 32;

    bpf_ringbuf_submit(e, 0);

    return 0;
}

/**
 * hash_map_update_benchmark - Measure hash map update latency
 */
SEC("tp/syscalls/sys_enter_read")
int hash_map_update(struct trace_event_raw_sys_enter *ctx)
{
    __u32 key = (bpf_get_current_pid_uid() >> 32) & 0xFF;
    __u64 value = bpf_ktime_get_ns();
    __u64 start = bpf_ktime_get_ns();

    /* Perform hash map update */
    bpf_map_update_elem(&hash_map, &key, &value, BPF_ANY);

    __u64 end = bpf_ktime_get_ns();

    /* Record latency */
    struct latency_event *e = bpf_ringbuf_reserve(&ringbuf_events, sizeof(*e), 0);
    if (!e)
        return 1;

    e->timestamp_start = start;
    e->timestamp_end = end;
    e->operation = 1;  /* Hash update */
    e->pid = bpf_get_current_pid_uid() >> 32;

    bpf_ringbuf_submit(e, 0);

    return 0;
}

/**
 * array_map_benchmark - Measure array map operations
 *
 * Array maps should be faster than hash maps for small key ranges
 */
SEC("tp/syscalls/sys_enter_write")
int array_map_benchmark(struct trace_event_raw_sys_enter *ctx)
{
    __u32 key = (bpf_get_current_pid_uid() >> 32) & 0xFF;
    __u64 start = bpf_ktime_get_ns();

    /* Array map lookup */
    __u64 *val = bpf_map_lookup_elem(&array_map, &key);
    if (val) {
        /* Array map update */
        __sync_fetch_and_add(val, 1);
    }

    __u64 end = bpf_ktime_get_ns();

    /* Record latency */
    struct latency_event *e = bpf_ringbuf_reserve(&ringbuf_events, sizeof(*e), 0);
    if (!e)
        return 1;

    e->timestamp_start = start;
    e->timestamp_end = end;
    e->operation = 2;  /* Array lookup+update */
    e->pid = bpf_get_current_pid_uid() >> 32;

    bpf_ringbuf_submit(e, 0);

    return 0;
}

/**
 * percpu_array_benchmark - Measure per-CPU array operations
 *
 * Per-CPU operations have no contention between CPUs
 */
SEC("tp/syscalls/sys_enter_close")
int percpu_array_benchmark(struct trace_event_raw_sys_enter *ctx)
{
    __u32 key = (bpf_get_current_pid_uid() >> 32) & 0xFF;
    __u64 start = bpf_ktime_get_ns();

    /* Per-CPU array lookup and increment */
    __u64 *val = bpf_map_lookup_elem(&percpu_array, &key);
    if (val) {
        __sync_fetch_and_add(val, 1);
    }

    __u64 end = bpf_ktime_get_ns();

    /* Record latency */
    struct latency_event *e = bpf_ringbuf_reserve(&ringbuf_events, sizeof(*e), 0);
    if (!e)
        return 1;

    e->timestamp_start = start;
    e->timestamp_end = end;
    e->operation = 3;  /* Per-CPU array */
    e->pid = bpf_get_current_pid_uid() >> 32;

    bpf_ringbuf_submit(e, 0);

    return 0;
}

/**
 * percpu_hash_benchmark - Measure per-CPU hash operations
 */
SEC("tp/syscalls/sys_enter_stat")
int percpu_hash_benchmark(struct trace_event_raw_sys_enter *ctx)
{
    __u32 key = (bpf_get_current_pid_uid() >> 32) & 0xFF;
    __u64 start = bpf_ktime_get_ns();

    /* Per-CPU hash lookup */
    __u64 *val = bpf_map_lookup_elem(&percpu_hash, &key);
    if (!val) {
        __u64 init_val = 1;
        bpf_map_update_elem(&percpu_hash, &key, &init_val, BPF_ANY);
    } else {
        __sync_fetch_and_add(val, 1);
    }

    __u64 end = bpf_ktime_get_ns();

    /* Record latency */
    struct latency_event *e = bpf_ringbuf_reserve(&ringbuf_events, sizeof(*e), 0);
    if (!e)
        return 1;

    e->timestamp_start = start;
    e->timestamp_end = end;
    e->operation = 4;  /* Per-CPU hash */
    e->pid = bpf_get_current_pid_uid() >> 32;

    bpf_ringbuf_submit(e, 0);

    return 0;
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";
