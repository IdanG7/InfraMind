#pragma once

#include "exporter.hpp"
#include <atomic>
#include <thread>
#include <mutex>

namespace im {

class PrometheusExporter : public Exporter {
public:
    explicit PrometheusExporter(int port);
    ~PrometheusExporter() override;

    void start() override;
    void stop() override;
    void export_metrics(const Metrics& metrics) override;

private:
    void serve();
    std::string format_metrics();

    int port_;
    std::atomic<bool> running_{false};
    std::thread server_thread_;

    std::mutex metrics_mutex_;
    Metrics current_metrics_;
};

} // namespace im
