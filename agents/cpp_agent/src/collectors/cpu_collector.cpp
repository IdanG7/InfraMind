#include "collectors/cpu_collector.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>

namespace im {

Metrics CpuCollector::collect() {
    Metrics metrics;

    // Read /proc/stat
    std::ifstream stat_file("/proc/stat");
    if (!stat_file.is_open()) {
        throw std::runtime_error("Failed to open /proc/stat");
    }

    std::string line;
    std::getline(stat_file, line);

    std::istringstream iss(line);
    std::string cpu_label;
    unsigned long long user, nice, system, idle, iowait, irq, softirq, steal;

    iss >> cpu_label >> user >> nice >> system >> idle >> iowait >> irq >> softirq >> steal;

    unsigned long long total = user + nice + system + idle + iowait + irq + softirq + steal;
    unsigned long long idle_total = idle + iowait;

    // Calculate CPU usage percentage
    double cpu_usage = 0.0;
    if (prev_total_ > 0) {
        unsigned long long total_diff = total - prev_total_;
        unsigned long long idle_diff = idle_total - prev_idle_;

        if (total_diff > 0) {
            cpu_usage = 100.0 * (1.0 - static_cast<double>(idle_diff) / total_diff);
        }
    }

    prev_total_ = total;
    prev_idle_ = idle_total;

    metrics.gauges["im_cpu_usage_percent"] = cpu_usage;
    metrics.counters["im_cpu_user_seconds_total"] = user / 100.0;
    metrics.counters["im_cpu_system_seconds_total"] = system / 100.0;

    return metrics;
}

} // namespace im
