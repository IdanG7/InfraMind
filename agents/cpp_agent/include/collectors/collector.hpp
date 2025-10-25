#pragma once

#include <string>
#include <map>

namespace im {

struct Metrics {
    std::map<std::string, double> gauges;
    std::map<std::string, double> counters;
};

class Collector {
public:
    virtual ~Collector() = default;
    virtual Metrics collect() = 0;
    virtual std::string name() const = 0;
};

} // namespace im
