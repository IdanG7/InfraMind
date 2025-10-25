#include "exporters/logging.hpp"

#include <iostream>
#include <iomanip>
#include <chrono>

namespace im {

LoggingExporter::LoggingExporter(const std::string& level) : level_(level) {}

void LoggingExporter::start() {
    std::cout << "Logging exporter started (level: " << level_ << ")\n";
}

void LoggingExporter::stop() {
    std::cout << "Logging exporter stopped\n";
}

void LoggingExporter::export_metrics(const Metrics& metrics) {
    // Log as JSON to stdout (picked up by Fluent Bit)
    if (level_ == "debug") {
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::system_clock::to_time_t(now);

        std::cout << "{";
        std::cout << "\"ts\":\"" << std::put_time(std::gmtime(&timestamp), "%Y-%m-%dT%H:%M:%SZ") << "\",";
        std::cout << "\"gauges\":{";

        bool first = true;
        for (const auto& [name, value] : metrics.gauges) {
            if (!first) std::cout << ",";
            std::cout << "\"" << name << "\":" << value;
            first = false;
        }

        std::cout << "},\"counters\":{";

        first = true;
        for (const auto& [name, value] : metrics.counters) {
            if (!first) std::cout << ",";
            std::cout << "\"" << name << "\":" << value;
            first = false;
        }

        std::cout << "}}\n";
    }
}

} // namespace im
