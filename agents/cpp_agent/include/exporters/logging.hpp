#pragma once

#include "exporter.hpp"
#include <string>

namespace im {

class LoggingExporter : public Exporter {
public:
    explicit LoggingExporter(const std::string& level = "info");

    void start() override;
    void stop() override;
    void export_metrics(const Metrics& metrics) override;

private:
    std::string level_;
};

} // namespace im
