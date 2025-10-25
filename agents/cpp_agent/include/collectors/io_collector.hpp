#pragma once

#include "collector.hpp"

namespace im {

class IoCollector : public Collector {
public:
    IoCollector() = default;

    Metrics collect() override;
    std::string name() const override { return "io"; }

private:
    unsigned long long prev_read_bytes_ = 0;
    unsigned long long prev_write_bytes_ = 0;
};

} // namespace im
