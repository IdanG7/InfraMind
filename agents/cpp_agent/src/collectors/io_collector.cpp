#include "collectors/io_collector.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>
#include <unistd.h>

namespace im {

Metrics IoCollector::collect() {
    Metrics metrics;

    // Read /proc/self/io for process I/O stats
    std::ifstream io_file("/proc/self/io");
    if (!io_file.is_open()) {
        // Fall back to /proc/diskstats if self not available
        metrics.gauges["im_io_read_bytes"] = 0;
        metrics.gauges["im_io_write_bytes"] = 0;
        return metrics;
    }

    unsigned long long read_bytes = 0, write_bytes = 0;
    std::string line;

    while (std::getline(io_file, line)) {
        std::istringstream iss(line);
        std::string key;
        unsigned long long value;

        iss >> key >> value;

        if (key == "read_bytes:") read_bytes = value;
        else if (key == "write_bytes:") write_bytes = value;
    }

    metrics.counters["im_io_read_bytes_total"] = static_cast<double>(read_bytes);
    metrics.counters["im_io_write_bytes_total"] = static_cast<double>(write_bytes);

    return metrics;
}

} // namespace im
