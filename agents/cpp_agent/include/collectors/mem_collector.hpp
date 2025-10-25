#pragma once

#include "collector.hpp"

namespace im {

class MemCollector : public Collector {
public:
    MemCollector() = default;

    Metrics collect() override;
    std::string name() const override { return "memory"; }
};

} // namespace im
