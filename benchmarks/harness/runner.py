#!/usr/bin/env python3
"""
Benchmark Runner

Main harness for executing eBPF benchmarks and collecting metrics
"""

import os
import json
import yaml
import time
import subprocess
import argparse
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Stores benchmark result data"""
    benchmark_id: str
    benchmark_name: str
    language: str
    program_type: str
    data_mechanism: str
    duration: float
    timestamp: str
    status: str  # 'success', 'failed', 'skipped'
    metrics: Dict
    errors: Optional[str] = None
    warnings: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self):
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class SystemMetricsCollector:
    """Collects system metrics during benchmark execution"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.cpu_stats_start = None
        self.cpu_stats_end = None

    def start(self):
        """Start collecting metrics"""
        self.start_time = time.time()
        self.cpu_stats_start = self._read_cpu_stats()

    def end(self):
        """End collecting metrics"""
        self.end_time = time.time()
        self.cpu_stats_end = self._read_cpu_stats()

    def get_cpu_usage(self):
        """Calculate CPU usage percentage"""
        if not self.cpu_stats_start or not self.cpu_stats_end:
            return 0.0

        start_total = sum(self.cpu_stats_start[1:])
        end_total = sum(self.cpu_stats_end[1:])
        total_diff = end_total - start_total

        if total_diff == 0:
            return 0.0

        start_idle = self.cpu_stats_start[4]
        end_idle = self.cpu_stats_end[4]
        idle_diff = end_idle - start_idle

        return 100.0 * (1.0 - idle_diff / total_diff) if total_diff > 0 else 0.0

    def get_duration(self):
        """Get benchmark duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def get_memory_usage(self):
        """Get memory usage from /proc/meminfo"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                mem_available = 0
                mem_total = 0
                for line in lines:
                    if line.startswith('MemTotal:'):
                        mem_total = int(line.split()[1])
                    elif line.startswith('MemAvailable:'):
                        mem_available = int(line.split()[1])
                return {
                    'total_mb': mem_total / 1024,
                    'available_mb': mem_available / 1024,
                    'used_mb': (mem_total - mem_available) / 1024,
                }
        except Exception as e:
            logger.warning(f"Could not read memory info: {e}")
            return {}

    @staticmethod
    def _read_cpu_stats():
        """Read /proc/stat for CPU statistics"""
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                return [int(x) for x in line.split()[1:]]
        except Exception as e:
            logger.warning(f"Could not read CPU stats: {e}")
            return None


class LoadGenerator:
    """Generates system load for benchmarks"""

    def __init__(self, load_type: str = "syscall_flood", duration: int = 10):
        self.load_type = load_type
        self.duration = duration
        self.process = None

    def start(self):
        """Start load generation"""
        commands = {
            'syscall_flood': f"stress-ng --syscall 4 --timeout {self.duration}s --quiet",
            'cpu_bound': f"stress-ng --cpu 2 --timeout {self.duration}s --quiet",
            'memory': f"stress-ng --vm 2 --vm-bytes 128M --timeout {self.duration}s --quiet",
        }

        cmd = commands.get(self.load_type)
        if not cmd:
            logger.warning(f"Unknown load type: {self.load_type}")
            return

        try:
            self.process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Started {self.load_type} load generator")
        except Exception as e:
            logger.error(f"Failed to start load generator: {e}")

    def stop(self):
        """Stop load generation"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("Stopped load generator")


class BenchmarkRunner:
    """Main benchmark execution engine"""

    def __init__(self, config_path: str, output_dir: str = "results"):
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.benchmarks = self.config.get('benchmarks', [])
        self.results: List[BenchmarkResult] = []

    def run_all(self, language_filter: Optional[str] = None, benchmark_filter: Optional[str] = None):
        """Run all configured benchmarks"""
        logger.info(f"Starting benchmark run with {len(self.benchmarks)} benchmarks")

        for benchmark in self.benchmarks:
            if benchmark_filter and benchmark['id'] != benchmark_filter:
                continue

            languages = benchmark.get('languages', [])
            if language_filter and language_filter not in languages:
                continue

            for language in languages:
                self.run_single(benchmark, language)

        self.save_results()
        logger.info("Benchmark run complete")

    def run_single(self, benchmark_config: Dict, language: str):
        """Run a single benchmark"""
        benchmark_id = benchmark_config['id']
        logger.info(f"Running {benchmark_id} ({language})")

        try:
            metrics = self._execute_benchmark(benchmark_config, language)

            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_config['name'],
                language=language,
                program_type=benchmark_config.get('program_type', 'unknown'),
                data_mechanism=benchmark_config.get('data_mechanism', 'unknown'),
                duration=metrics.get('duration', 0),
                timestamp=datetime.now().isoformat(),
                status='success',
                metrics=metrics
            )

        except Exception as e:
            logger.error(f"Error running benchmark: {e}")
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_config['name'],
                language=language,
                program_type=benchmark_config.get('program_type', 'unknown'),
                data_mechanism=benchmark_config.get('data_mechanism', 'unknown'),
                duration=0,
                timestamp=datetime.now().isoformat(),
                status='failed',
                metrics={},
                errors=str(e)
            )

        self.results.append(result)
        logger.info(f"  Status: {result.status}")

    def _execute_benchmark(self, benchmark_config: Dict, language: str) -> Dict:
        """Execute benchmark and collect metrics"""
        metrics_collector = SystemMetricsCollector()
        load_generator = None

        try:
            # Start metrics collection
            metrics_collector.start()

            # Start load generator if specified
            load_type = benchmark_config.get('load_type', 'syscall_flood')
            duration = benchmark_config.get('duration_seconds', 10)

            if load_type:
                load_generator = LoadGenerator(load_type, duration)
                load_generator.start()

            # Run benchmark (simplified - actual implementation would call language-specific harnesses)
            time.sleep(duration)

            metrics_collector.end()

            return {
                'duration': metrics_collector.get_duration(),
                'cpu_usage_percent': metrics_collector.get_cpu_usage(),
                'memory_info': metrics_collector.get_memory_usage(),
                'throughput': 0,  # Would be populated by actual benchmark
                'latency_p50': 0,
                'latency_p95': 0,
                'latency_p99': 0,
            }

        finally:
            if load_generator:
                load_generator.stop()

    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"results_{timestamp}.json"

        results_data = {
            'timestamp': datetime.now().isoformat(),
            'config_file': str(self.config_path),
            'results': [r.to_dict() for r in self.results],
            'summary': self._get_summary(),
        }

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Results saved to {output_file}")

        # Also save to latest.json for easy access
        latest_file = self.output_dir / "latest.json"
        with open(latest_file, 'w') as f:
            json.dump(results_data, f, indent=2)

    def _get_summary(self) -> Dict:
        """Generate summary statistics"""
        successful = sum(1 for r in self.results if r.status == 'success')
        failed = sum(1 for r in self.results if r.status == 'failed')

        return {
            'total_benchmarks': len(self.results),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(self.results) if self.results else 0,
        }

    def print_summary(self):
        """Print summary of results"""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)

        for result in self.results:
            status_symbol = "✓" if result.status == 'success' else "✗"
            print(f"\n{status_symbol} {result.benchmark_name} ({result.language})")
            print(f"  Status: {result.status}")
            print(f"  Duration: {result.duration:.2f}s")

            if result.metrics:
                print(f"  Metrics:")
                for key, value in result.metrics.items():
                    if isinstance(value, float):
                        print(f"    {key}: {value:.2f}")
                    else:
                        print(f"    {key}: {value}")

            if result.errors:
                print(f"  Error: {result.errors}")

        print("\n" + "="*60)
        summary = self._get_summary()
        print(f"Total: {summary['total_benchmarks']} | "
              f"Successful: {summary['successful']} | "
              f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']*100:.1f}%")
        print("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="eBPF Benchmark Runner"
    )
    parser.add_argument(
        '-c', '--config',
        default='benchmarks/configs/benchmark_config.yaml',
        help='Path to benchmark configuration file'
    )
    parser.add_argument(
        '-o', '--output',
        default='benchmarks/results',
        help='Output directory for results'
    )
    parser.add_argument(
        '-l', '--language',
        help='Filter to specific language (c, python, golang, rust)'
    )
    parser.add_argument(
        '-b', '--benchmark',
        help='Filter to specific benchmark ID'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        runner = BenchmarkRunner(args.config, args.output)
        runner.run_all(language_filter=args.language, benchmark_filter=args.benchmark)
        runner.print_summary()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
