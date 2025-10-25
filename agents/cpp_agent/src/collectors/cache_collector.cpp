#include "collectors/cache_collector.hpp"

#include <cstdlib>

namespace im {

Metrics CacheCollector::collect() {
    Metrics metrics;

    // Placeholder: In production, would parse ccache/bazel stats
    // For now, return dummy values
    metrics.gauges["im_cache_hit_ratio"] = 0.75;
    metrics.counters["im_cache_hits_total"] = 100;
    metrics.counters["im_cache_misses_total"] = 25;

    return metrics;
}

} // namespace im
