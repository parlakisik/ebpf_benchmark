package main

import (
	"fmt"
	"time"
)

// Event matches the kernel-space structure
type Event struct {
	Timestamp uint64 // Kernel timestamp
	PID       uint32 // Process ID
	CPU       uint32 // CPU ID
	EventType uint32 // Type of event
	Data      uint32 // Generic data field
}

// BenchmarkResult stores benchmark metrics
type BenchmarkResult struct {
	Name          string
	Language      string
	ProgramType   string
	DataMechanism string
	Duration      float64
	EventCount    int64
	Throughput    float64
	CPUUsage      float64
	MemoryUsage   uint64
	StartTime     time.Time
	EndTime       time.Time
	Errors        []string
}

// EventBuffer manages event collection
type EventBuffer struct {
	events    []Event
	maxSize   int
	startTime time.Time
	endTime   time.Time
}

// NewEventBuffer creates a new event buffer
func NewEventBuffer(maxSize int) *EventBuffer {
	return &EventBuffer{
		events:  make([]Event, 0, maxSize),
		maxSize: maxSize,
	}
}

// Add adds an event to the buffer
func (eb *EventBuffer) Add(e Event) bool {
	if len(eb.events) >= eb.maxSize {
		return false
	}
	eb.events = append(eb.events, e)
	return true
}

// Start marks the start of collection
func (eb *EventBuffer) Start() {
	eb.startTime = time.Now()
	eb.events = eb.events[:0] // Reset events
}

// End marks the end of collection
func (eb *EventBuffer) End() {
	eb.endTime = time.Now()
}

// GetEventCount returns the number of events collected
func (eb *EventBuffer) GetEventCount() int64 {
	return int64(len(eb.events))
}

// GetDuration returns the collection duration
func (eb *EventBuffer) GetDuration() float64 {
	if eb.endTime.IsZero() || eb.startTime.IsZero() {
		return 0
	}
	return eb.endTime.Sub(eb.startTime).Seconds()
}

// GetThroughput calculates events per second
func (eb *EventBuffer) GetThroughput() float64 {
	duration := eb.GetDuration()
	if duration <= 0 {
		return 0
	}
	return float64(eb.GetEventCount()) / duration
}

// GetLatencyStats calculates latency statistics
func (eb *EventBuffer) GetLatencyStats() map[string]float64 {
	if len(eb.events) < 2 {
		return map[string]float64{
			"min":     0,
			"max":     0,
			"average": 0,
		}
	}

	// Calculate latencies from timestamp differences
	latencies := make([]float64, 0)
	for i := 1; i < len(eb.events); i++ {
		diff := float64(eb.events[i].Timestamp-eb.events[i-1].Timestamp) / 1000 // Convert to microseconds
		latencies = append(latencies, diff)
	}

	var minLat, maxLat, sumLat float64
	if len(latencies) > 0 {
		minLat = latencies[0]
		maxLat = latencies[0]
		for _, lat := range latencies {
			if lat < minLat {
				minLat = lat
			}
			if lat > maxLat {
				maxLat = lat
			}
			sumLat += lat
		}
	}

	avgLat := 0.0
	if len(latencies) > 0 {
		avgLat = sumLat / float64(len(latencies))
	}

	return map[string]float64{
		"min":     minLat,
		"max":     maxLat,
		"average": avgLat,
	}
}

// GetCPUs returns unique CPUs that generated events
func (eb *EventBuffer) GetCPUs() map[uint32]bool {
	cpus := make(map[uint32]bool)
	for _, e := range eb.events {
		cpus[e.CPU] = true
	}
	return cpus
}

// EventSize returns the size of an Event structure
func (e *Event) EventSize() int {
	return 32 // 8 + 4 + 4 + 4 + 4 + 4 bytes for timestamp, pid, cpu, type, data, padding
}

// PrintEvent prints event details
func (e *Event) String() string {
	return fmt.Sprintf(
		"Event{Timestamp:%d, PID:%d, CPU:%d, Type:%d, Data:%d}",
		e.Timestamp, e.PID, e.CPU, e.EventType, e.Data,
	)
}

// PrintResult prints benchmark result
func (r *BenchmarkResult) String() string {
	return fmt.Sprintf(
		`
=== %s Benchmark Results ===
Language:        %s
Program Type:    %s
Data Mechanism:  %s
Duration:        %.2f seconds
Event Count:     %d
Throughput:      %.0f events/sec
CPU Usage:       %.2f%%
Memory Usage:    %d bytes
Start:           %v
End:             %v
Errors:          %v
`,
		r.Name, r.Language, r.ProgramType, r.DataMechanism,
		r.Duration, r.EventCount, r.Throughput, r.CPUUsage,
		r.MemoryUsage, r.StartTime, r.EndTime, r.Errors,
	)
}

// SaveToJSON saves result to JSON (placeholder)
func (r *BenchmarkResult) SaveToJSON(filename string) error {
	// This would use encoding/json in real implementation
	fmt.Printf("Would save result to %s\n", filename)
	return nil
}

// GetCPUUsage gets current CPU usage percentage
func GetCPUUsage() (float64, error) {
	// Simplified version - in real implementation would read /proc/stat
	return 0.0, nil
}

// GetMemoryUsage gets current memory usage
func GetMemoryUsage() (uint64, error) {
	// Simplified version - in real implementation would read /proc/self/status
	return 0, nil
}

// PrintBenchmarkHeader prints header for benchmark output
func PrintBenchmarkHeader(name string) {
	fmt.Println()
	fmt.Println("=" + "[" + name + "]" + "=")
	fmt.Println()
}

// PrintBenchmarkStatus prints status updates
func PrintBenchmarkStatus(msg string) {
	fmt.Printf("[%v] %s\n", time.Now().Format("15:04:05"), msg)
}

// PrintSeparator prints a separator line
func PrintSeparator() {
	fmt.Println("=" + "=================================================" + "=")
}
