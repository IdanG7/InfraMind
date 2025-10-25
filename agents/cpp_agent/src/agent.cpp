#include "agent.hpp"
#include "collectors/cpu_collector.hpp"
#include "collectors/mem_collector.hpp"
#include "collectors/io_collector.hpp"
#include "collectors/cache_collector.hpp"
#include "exporters/prometheus.hpp"
#include "exporters/logging.hpp"

#include <iostream>
#include <chrono>

namespace im {

Agent::Agent(const Config& config) : config_(config) {
    // Initialize collectors
    collectors_.emplace_back(std::make_unique<CpuCollector>());
    collectors_.emplace_back(std::make_unique<MemCollector>());
    collectors_.emplace_back(std::make_unique<IoCollector>());
    collectors_.emplace_back(std::make_unique<CacheCollector>());

    // Initialize exporters
    exporters_.emplace_back(std::make_unique<PrometheusExporter>(config_.prometheus_port));
    exporters_.emplace_back(std::make_unique<LoggingExporter>(config_.log_level));
}

Agent::~Agent() {
    stop();
}

bool Agent::start() {
    if (running_.exchange(true)) {
        std::cerr << "Agent already running\n";
        return false;
    }

    std::cout << "Starting InfraMind agent on port " << config_.prometheus_port << "\n";

    // Start exporters
    for (auto& exporter : exporters_) {
        exporter->start();
    }

    // Start collection thread
    collect_thread_ = std::thread(&Agent::collect_loop, this);

    return true;
}

void Agent::stop() {
    if (!running_.exchange(false)) {
        return;
    }

    std::cout << "Stopping InfraMind agent\n";

    if (collect_thread_.joinable()) {
        collect_thread_.join();
    }

    // Stop exporters
    for (auto& exporter : exporters_) {
        exporter->stop();
    }
}

void Agent::register_step(const StepLabel& label) {
    std::cout << "Registered step: " << label.stage << "/" << label.step
              << " (span: " << label.span_id << ")\n";
    // In production, would trigger specific collection for this span
}

void Agent::collect_loop() {
    using namespace std::chrono;

    while (running_) {
        auto start = steady_clock::now();

        // Collect from all collectors
        Metrics all_metrics;
        for (const auto& collector : collectors_) {
            try {
                auto metrics = collector->collect();
                all_metrics.gauges.insert(metrics.gauges.begin(), metrics.gauges.end());
                all_metrics.counters.insert(metrics.counters.begin(), metrics.counters.end());
            } catch (const std::exception& e) {
                std::cerr << "Collector " << collector->name() << " failed: " << e.what() << "\n";
            }
        }

        // Export to all exporters
        for (auto& exporter : exporters_) {
            exporter->export_metrics(all_metrics);
        }

        // Sleep for remaining interval
        auto elapsed = duration_cast<milliseconds>(steady_clock::now() - start);
        auto sleep_time = milliseconds(config_.scrape_interval_ms) - elapsed;
        if (sleep_time > milliseconds(0)) {
            std::this_thread::sleep_for(sleep_time);
        }
    }
}

} // namespace im
