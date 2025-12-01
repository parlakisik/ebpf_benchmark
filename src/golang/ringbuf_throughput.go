package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/signal"
	"runtime"
	"syscall"
	"time"
)

// RingBufferBenchmark implements benchmarking for ring buffers
type RingBufferBenchmark struct {
	eventBuffer *EventBuffer
	duration    time.Duration
	verbose     bool
	result      *BenchmarkResult
	stopChan    chan struct{}
}

const (
	eventTypeKprobe     = 1
	eventTypeTracepoint = 2
	eventTypeUprobe     = 3
	eventTypeXDP        = 4
	eventTypeTC         = 5
)

func main() {
	durationSecs := flag.Int("d", 10, "Benchmark duration (seconds)")
	verbose := flag.Bool("v", false, "Verbose output")
	output := flag.String("o", "ringbuf_result.json", "Output JSON file")
	flag.Parse()

	duration := time.Duration(*durationSecs) * time.Second

	bench := NewRingBufferBenchmark(duration, *verbose)

	if err := bench.Run(); err != nil {
		log.Fatalf("Benchmark failed: %v", err)
	}

	if err := bench.SaveResult(*output); err != nil {
		log.Printf("Warning: Failed to save result: %v", err)
	}

	bench.PrintResults()
}

// NewRingBufferBenchmark creates a new benchmark instance
func NewRingBufferBenchmark(duration time.Duration, verbose bool) *RingBufferBenchmark {
	return &RingBufferBenchmark{
		duration:    duration,
		verbose:     verbose,
		eventBuffer: NewEventBuffer(10000000), // 10M event capacity
		stopChan:    make(chan struct{}),
		result: &BenchmarkResult{
			Name:          "Ring Buffer Throughput",
			Language:      "Go",
			ProgramType:   "tracepoint",
			DataMechanism: "ring_buffer",
			Errors:        []string{},
		},
	}
}

// Run executes the benchmark
func (b *RingBufferBenchmark) Run() error {
	if b.verbose {
		PrintBenchmarkHeader("Ring Buffer Throughput Benchmark (Go)")
		PrintBenchmarkStatus("Starting benchmark simulation...")
	}

	b.result.StartTime = time.Now()
	b.eventBuffer.Start()

	// Simulate event collection for the specified duration
	ticker := time.NewTicker(1 * time.Millisecond)
	defer ticker.Stop()

	done := time.After(b.duration)
	eventCounter := 0

	// Set up signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	if b.verbose {
		PrintBenchmarkStatus(fmt.Sprintf("Running for %v...", b.duration))
	}

	for {
		select {
		case <-done:
			if b.verbose {
				PrintBenchmarkStatus("Benchmark duration completed")
			}
			goto finish

		case <-sigChan:
			if b.verbose {
				PrintBenchmarkStatus("Interrupted by user")
			}
			goto finish

		case <-ticker.C:
			// Simulate generating events from syscall tracing
			// In a real implementation, these would come from ring buffer
			eventsThisTick := b.simulateEvents()
			eventCounter += eventsThisTick

		case <-b.stopChan:
			goto finish
		}
	}

finish:
	b.eventBuffer.End()
	b.result.EndTime = time.Now()

	// Calculate metrics
	b.result.Duration = b.eventBuffer.GetDuration()
	b.result.EventCount = b.eventBuffer.GetEventCount()
	b.result.Throughput = b.eventBuffer.GetThroughput()

	// Get system metrics
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	b.result.MemoryUsage = m.Alloc

	if b.verbose {
		PrintBenchmarkStatus("Calculating final metrics...")
	}

	return nil
}

// simulateEvents simulates event collection from ring buffer
// In production, this would read from actual eBPF ring buffer
func (b *RingBufferBenchmark) simulateEvents() int {
	// Simulate ~100 events per millisecond (realistic for syscall tracing)
	eventsToCreate := 50 + (runtime.NumCPU() * 5)

	for i := 0; i < eventsToCreate; i++ {
		// Create a simulated event
		e := Event{
			Timestamp: uint64(time.Now().UnixNano()),
			PID:       uint32(os.Getpid()),
			CPU:       uint32(i % runtime.NumCPU()),
			EventType: eventTypeTracepoint,
			Data:      uint32(i),
		}

		if !b.eventBuffer.Add(e) {
			if b.verbose {
				fmt.Printf("Event buffer full, dropped event\n")
			}
			return i
		}
	}

	return eventsToCreate
}

// SaveResult saves the benchmark result to JSON
func (b *RingBufferBenchmark) SaveResult(filename string) error {
	data, err := json.MarshalIndent(b.result, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal result: %w", err)
	}

	err = ioutil.WriteFile(filename, data, 0644)
	if err != nil {
		return fmt.Errorf("failed to write result file: %w", err)
	}

	if b.verbose {
		PrintBenchmarkStatus(fmt.Sprintf("Result saved to %s", filename))
	}

	return nil
}

// PrintResults prints benchmark results to console
func (b *RingBufferBenchmark) PrintResults() {
	PrintSeparator()
	fmt.Print(b.result.String())
	PrintSeparator()

	if len(b.result.Errors) > 0 {
		fmt.Println("\nErrors encountered:")
		for _, err := range b.result.Errors {
			fmt.Printf("  - %s\n", err)
		}
	}
}
