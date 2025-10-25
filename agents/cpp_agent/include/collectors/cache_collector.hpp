#pragma once

#include "collector.hpp"

namespace im {

class CacheCollector : public Collector {
public:
    CacheCollector() = default;

    Metrics collect() override;
    std::string name() const override { return "cache"; }
};

} // namespace im
