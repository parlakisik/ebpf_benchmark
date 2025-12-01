#!/usr/bin/env python3
"""
Common utilities for Python eBPF benchmarks

Provides shared definitions and helper functions for BCC-based programs
"""

from ctypes import Structure, c_uint64, c_uint32, c_char
import time
from enum import IntEnum

# Event types
class EventType(IntEnum):
    """eBPF event types"""
    KPROBE = 1
    TRACEPOINT = 2
    UPROBE = 3
    XDP = 4
    TC = 5


class Event(Structure):
    """Event structure for ring buffer"""
    _fields_ = [
        ("timestamp", c_uint64),  # Kernel timestamp
        ("pid", c_uint32),         # Process ID
        ("cpu_id", c_uint32),      # CPU ID
        ("event_type", c_uint32),  # Type of event
        ("data", c_uint32),        # Generic data field
    ]


class LatencyEvent(Structure):
    """Event structure for latency measurement"""
    _fields_ = [
        ("timestamp_start", c_uint64),
        ("timestamp_end", c_uint64),
        ("operation", c_uint32),
        ("pid", c_uint32),
    ]


class Stats(Structure):
    """Statistics structure"""
    _fields_ = [
        ("count", c_uint64),
        ("sum_latency", c_uint64),
        ("min_latency", c_uint64),
        ("max_latency", c_uint64),
    ]


def get_kernel_version():
    """Get current kernel version as tuple"""
    import subprocess
    version_str = subprocess.check_output(['uname', '-r']).decode().strip()
    parts = version_str.split('.')
    try:
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return (0, 0)


def check_kernel_capability(feature):
    """Check if kernel supports specific eBPF feature"""
    capabilities = {
        'ringbuf': (5, 8),  # Ring buffers introduced in 5.8
        'kprobes': (3, 5),
        'tracepoints': (3, 5),
        'uprobes': (3, 15),
        'xdp': (4, 8),
        'bpf_stats': (4, 16),
    }

    kernel_ver = get_kernel_version()
    required_ver = capabilities.get(feature, (0, 0))

    return kernel_ver >= required_ver


class EventCollector:
    """Helper class for collecting events from ring/perf buffers"""

    def __init__(self):
        self.events = []
        self.start_time = None
        self.end_time = None

    def start_collection(self):
        """Mark start of event collection"""
        self.start_time = time.time()
        self.events = []

    def end_collection(self):
        """Mark end of event collection"""
        self.end_time = time.time()

    def add_event(self, event_data):
        """Add event to collection"""
        if isinstance(event_data, bytes):
            event = Event.from_buffer_copy(event_data)
        else:
            event = event_data
        self.events.append(event)

    def get_duration(self):
        """Get collection duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def get_event_count(self):
        """Get total number of events collected"""
        return len(self.events)

    def get_throughput(self):
        """Get events per second"""
        duration = self.get_duration()
        if duration > 0:
            return self.get_event_count() / duration
        return 0

    def get_cpu_ids(self):
        """Get set of CPUs that generated events"""
        return set(e.cpu_id for e in self.events if hasattr(e, 'cpu_id'))

    def get_events_by_pid(self, pid=None):
        """Get events filtered by PID"""
        if pid is None:
            return self.events
        return [e for e in self.events if e.pid == pid]


def print_event(cpu, data, size):
    """Print callback for ring buffer events"""
    event = Event.from_buffer_copy(data)
    print(f"CPU {event.cpu_id}: PID {event.pid} Event {event.event_type} Data {event.data}")
    return 0
