#include "exporters/prometheus.hpp"

#include <iostream>
#include <sstream>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <cstring>

namespace im {

PrometheusExporter::PrometheusExporter(int port) : port_(port) {}

PrometheusExporter::~PrometheusExporter() {
    stop();
}

void PrometheusExporter::start() {
    if (running_.exchange(true)) {
        return;
    }

    std::cout << "Starting Prometheus exporter on :" << port_ << "/metrics\n";
    server_thread_ = std::thread(&PrometheusExporter::serve, this);
}

void PrometheusExporter::stop() {
    if (!running_.exchange(false)) {
        return;
    }

    if (server_thread_.joinable()) {
        server_thread_.join();
    }
}

void PrometheusExporter::export_metrics(const Metrics& metrics) {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    current_metrics_ = metrics;
}

std::string PrometheusExporter::format_metrics() {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    std::ostringstream oss;

    // Format gauges
    for (const auto& [name, value] : current_metrics_.gauges) {
        oss << "# TYPE " << name << " gauge\n";
        oss << name << " " << value << "\n";
    }

    // Format counters
    for (const auto& [name, value] : current_metrics_.counters) {
        oss << "# TYPE " << name << " counter\n";
        oss << name << " " << value << "\n";
    }

    return oss.str();
}

void PrometheusExporter::serve() {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        std::cerr << "Failed to create socket\n";
        return;
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port_);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "Failed to bind to port " << port_ << "\n";
        close(server_fd);
        return;
    }

    if (listen(server_fd, 3) < 0) {
        std::cerr << "Listen failed\n";
        close(server_fd);
        return;
    }

    while (running_) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);

        if (client_fd < 0) {
            if (running_) {
                std::cerr << "Accept failed\n";
            }
            continue;
        }

        // Read request (simple, not parsing)
        char buffer[1024] = {0};
        ssize_t bytes_read = read(client_fd, buffer, sizeof(buffer));
        (void)bytes_read;  // Intentionally unused

        // Send response
        std::string metrics = format_metrics();
        std::ostringstream response;
        response << "HTTP/1.1 200 OK\r\n";
        response << "Content-Type: text/plain\r\n";
        response << "Content-Length: " << metrics.size() << "\r\n";
        response << "\r\n";
        response << metrics;

        std::string resp_str = response.str();
        ssize_t bytes_written = write(client_fd, resp_str.c_str(), resp_str.size());
        (void)bytes_written;  // Intentionally unused
        close(client_fd);
    }

    close(server_fd);
}

} // namespace im
