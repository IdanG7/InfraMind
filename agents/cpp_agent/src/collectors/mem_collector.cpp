#include "collectors/mem_collector.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>

namespace im {

Metrics MemCollector::collect() {
    Metrics metrics;

    std::ifstream meminfo("/proc/meminfo");
    if (!meminfo.is_open()) {
        throw std::runtime_error("Failed to open /proc/meminfo");
    }

    unsigned long long mem_total = 0, mem_free = 0, mem_available = 0;
    unsigned long long buffers = 0, cached = 0;

    std::string line;
    while (std::getline(meminfo, line)) {
        std::istringstream iss(line);
        std::string key;
        unsigned long long value;
        std::string unit;

        iss >> key >> value >> unit;

        if (key == "MemTotal:") mem_total = value * 1024;
        else if (key == "MemFree:") mem_free = value * 1024;
        else if (key == "MemAvailable:") mem_available = value * 1024;
        else if (key == "Buffers:") buffers = value * 1024;
        else if (key == "Cached:") cached = value * 1024;
    }

    unsigned long long mem_used = mem_total - mem_free - buffers - cached;

    metrics.gauges["im_mem_total_bytes"] = static_cast<double>(mem_total);
    metrics.gauges["im_mem_used_bytes"] = static_cast<double>(mem_used);
    metrics.gauges["im_mem_available_bytes"] = static_cast<double>(mem_available);
    metrics.gauges["im_mem_cached_bytes"] = static_cast<double>(cached);

    return metrics;
}

} // namespace im
