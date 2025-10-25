FROM gcc:13 AS builder

WORKDIR /build

# Install CMake
RUN apt-get update && apt-get install -y cmake && rm -rf /var/lib/apt/lists/*

# Copy source
COPY . /build/

# Build
RUN mkdir -p build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . -j$(nproc)

# Runtime image
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/build/inframind_agent /usr/local/bin/
COPY --from=builder /build/config/agent.yaml /etc/inframind/

EXPOSE 9102

CMD ["/usr/local/bin/inframind_agent"]
