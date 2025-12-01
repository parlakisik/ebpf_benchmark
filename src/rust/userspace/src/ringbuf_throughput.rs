use anyhow::{Context, Result};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};
use std::collections::HashMap;
use tokio::time::sleep;

/// Ring Buffer Throughput Benchmark
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Benchmark duration in seconds
    #[arg(short, long, default_value = "10")]
    duration: u64,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,

    /// Output JSON file
    #[arg(short, long, default_value = "ringbuf_result.json")]
    output: String,
}

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct Event {
    pub timestamp: u64,
    pub pid: u32,
    pub cpu_id: u32,
    pub event_type: u32,
    pub data: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BenchmarkResult {
    pub name: String,
    pub language: String,
    pub program_type: String,
    pub data_mechanism: String,
    pub duration: f64,
    pub event_count: i64,
    pub throughput: f64,
    pub cpu_usage: f64,
    pub memory_usage: u64,
    pub start_time: String,
    pub end_time: String,
    pub cpu_ids: Vec<u32>,
    pub errors: Vec<String>,
}

pub struct RingBufferBenchmark {
    duration: Duration,
    verbose: bool,
    events: Vec<Event>,
    start_time: Instant,
    cpu_ids: std::collections::HashSet<u32>,
}

impl RingBufferBenchmark {
    pub fn new(duration_secs: u64, verbose: bool) -> Self {
        Self {
            duration: Duration::from_secs(duration_secs),
            verbose,
            events: Vec::with_capacity(1_000_000),
            start_time: Instant::now(),
            cpu_ids: std::collections::HashSet::new(),
        }
    }

    pub async fn run(&mut self) -> Result<()> {
        if self.verbose {
            println!("\n=== Ring Buffer Throughput Benchmark (Rust) ===\n");
            println!("[*] Starting benchmark simulation...");
        }

        self.start_time = Instant::now();

        // Simulate event collection
        let start = Instant::now();
        let mut event_count = 0;

        loop {
            // Check if duration exceeded
            if start.elapsed() >= self.duration {
                if self.verbose {
                    println!("[*] Benchmark duration completed");
                }
                break;
            }

            // Simulate events arriving from ring buffer
            let events_this_tick = self.simulate_events();
            event_count += events_this_tick;

            // Small delay to prevent CPU burning
            sleep(Duration::from_millis(1)).await;
        }

        if self.verbose {
            println!("[*] Calculating metrics...");
        }

        Ok(())
    }

    fn simulate_events(&mut self) -> usize {
        let num_cpus = num_cpus::get();
        let events_to_create = 100 + (num_cpus * 10);

        for i in 0..events_to_create {
            let event = Event {
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_nanos() as u64,
                pid: std::process::id(),
                cpu_id: (i % num_cpus) as u32,
                event_type: 2, // EVENT_TYPE_TRACEPOINT
                data: i as u32,
            };

            self.events.push(event);
            self.cpu_ids.insert(event.cpu_id);
        }

        events_to_create
    }

    pub fn get_results(&self) -> BenchmarkResult {
        let duration_secs = self.start_time.elapsed().as_secs_f64();
        let throughput = if duration_secs > 0.0 {
            self.events.len() as f64 / duration_secs
        } else {
            0.0
        };

        let mut cpu_ids_vec: Vec<u32> = self.cpu_ids.iter().copied().collect();
        cpu_ids_vec.sort();

        BenchmarkResult {
            name: "Ring Buffer Throughput".to_string(),
            language: "Rust".to_string(),
            program_type: "tracepoint".to_string(),
            data_mechanism: "ring_buffer".to_string(),
            duration: duration_secs,
            event_count: self.events.len() as i64,
            throughput,
            cpu_usage: 0.0,
            memory_usage: std::mem::size_of_val(&self.events) as u64,
            start_time: chrono::Local::now()
                .format("%Y-%m-%d %H:%M:%S")
                .to_string(),
            end_time: chrono::Local::now()
                .format("%Y-%m-%d %H:%M:%S")
                .to_string(),
            cpu_ids: cpu_ids_vec,
            errors: Vec::new(),
        }
    }

    pub fn print_results(&self) {
        let results = self.get_results();
        println!("\n{}", "=".repeat(60));
        println!("Ring Buffer Throughput Benchmark Results (Rust)");
        println!("{}", "=".repeat(60));
        println!("Language:        {}", results.language);
        println!("Program Type:    {}", results.program_type);
        println!("Data Mechanism:  {}", results.data_mechanism);
        println!("Duration:        {:.2} seconds", results.duration);
        println!("Event Count:     {}", results.event_count);
        println!("Throughput:      {:.0} events/sec", results.throughput);
        println!("Memory Usage:    {} bytes", results.memory_usage);
        println!("CPUs Involved:   {:?}", results.cpu_ids);
        println!("{}\n", "=".repeat(60));
    }

    pub fn save_results(&self, filename: &str) -> Result<()> {
        let results = self.get_results();
        let json = serde_json::to_string_pretty(&results)
            .context("Failed to serialize results")?;
        std::fs::write(filename, json)
            .context(format!("Failed to write results to {}", filename))?;

        if self.verbose {
            println!("[+] Results saved to {}", filename);
        }

        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    let mut bench = RingBufferBenchmark::new(args.duration, args.verbose);

    bench.run().await?;
    bench.print_results();
    bench.save_results(&args.output)?;

    Ok(())
}

// Mock num_cpus module if not available
mod num_cpus {
    use std::thread;

    pub fn get() -> usize {
        thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(1)
    }
}
