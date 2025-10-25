#pragma once

#include "collectors/collector.hpp"

namespace im {

class Exporter {
public:
    virtual ~Exporter() = default;

    virtual void start() = 0;
    virtual void stop() = 0;
    virtual void export_metrics(const Metrics& metrics) = 0;
};

} // namespace im
