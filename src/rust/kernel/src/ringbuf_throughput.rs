#![no_std]
#![no_main]

use aya_ebpf::{
    bindings::*,
    macros::{map, tracepoint},
    maps::RingBuf,
    programs::TracePointContext,
};

#[repr(C)]
pub struct Event {
    pub timestamp: u64,
    pub pid: u32,
    pub cpu_id: u32,
    pub event_type: u32,
    pub data: u32,
}

#[map]
static RINGBUF: RingBuf = RingBuf::with_byte_capacity(256 * 1024, 0);

#[map]
static COUNTERS: aya_ebpf::maps::Array<u64> =
    aya_ebpf::maps::Array::with_max_entries(10, 0);

const EVENT_TYPE_TRACEPOINT: u32 = 2;

#[tracepoint]
pub fn ringbuf_throughput(ctx: TracePointContext) -> u32 {
    match unsafe { try_ringbuf_throughput(ctx) } {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

unsafe fn try_ringbuf_throughput(ctx: TracePointContext) -> Result<u32, u32> {
    // Reserve space in ring buffer
    let event = RINGBUF.reserve::<Event>(0).ok_or(1u32)?;

    // Fill event structure
    (*event).timestamp = bpf_ktime_get_ns();
    (*event).pid = bpf_get_current_pid_uid() >> 32;
    (*event).cpu_id = bpf_get_smp_processor_id();
    (*event).event_type = EVENT_TYPE_TRACEPOINT;
    (*event).data = 0;

    // Submit event
    RINGBUF.submit(event, 0);

    // Update counter
    if let Some(counter) = COUNTERS.get_mut(0) {
        *counter += 1;
    }

    Ok(0)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
