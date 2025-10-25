#pragma once

#include <string>
#include <memory>
#include <atomic>
#include <thread>

namespace im {

struct StepLabel {
    std::string stage;
    std::string step;
    std::string span_id;
};

struct Config {
    int scrape_interval_ms = 1000;
    int prometheus_port = 9102;
    std::string log_level = "info";
};

class Collector;
class Exporter;

class Agent {
public:
    explicit Agent(const Config& config);
    ~Agent();

    bool start();
    void stop();
    void register_step(const StepLabel& label);

private:
    void collect_loop();

    Config config_;
    std::atomic<bool> running_{false};
    std::thread collect_thread_;

    std::vector<std::unique_ptr<Collector>> collectors_;
    std::vector<std::unique_ptr<Exporter>> exporters_;
};

} // namespace im
