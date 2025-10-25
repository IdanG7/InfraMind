#include "agent.hpp"

#include <iostream>
#include <csignal>
#include <atomic>

std::atomic<bool> g_shutdown{false};

void signal_handler(int signal) {
    if (signal == SIGINT || signal == SIGTERM) {
        std::cout << "\nReceived shutdown signal\n";
        g_shutdown = true;
    }
}

int main(int argc, char** argv) {
    std::cout << "InfraMind Telemetry Agent v0.1.0\n";

    // Setup signal handlers
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);

    // Parse config (for now, use defaults)
    im::Config config;
    config.scrape_interval_ms = 1000;
    config.prometheus_port = 9102;
    config.log_level = "info";

    // Create and start agent
    im::Agent agent(config);
    if (!agent.start()) {
        std::cerr << "Failed to start agent\n";
        return 1;
    }

    std::cout << "Agent running. Press Ctrl+C to stop.\n";

    // Wait for shutdown signal
    while (!g_shutdown) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    agent.stop();
    std::cout << "Agent stopped gracefully\n";

    return 0;
}
