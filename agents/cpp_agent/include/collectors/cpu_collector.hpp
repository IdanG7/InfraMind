#pragma once

#include "collector.hpp"

namespace im {

class CpuCollector : public Collector {
public:
    CpuCollector() = default;

    Metrics collect() override;
    std::string name() const override { return "cpu"; }

private:
    unsigned long long prev_total_ = 0;
    unsigned long long prev_idle_ = 0;
};

} // namespace im
