cmake_minimum_required(VERSION 3.20)
project(inframind_agent VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Dependencies
find_package(Threads REQUIRED)

# Source files
set(AGENT_SOURCES
    src/main.cpp
    src/agent.cpp
    src/collectors/cpu_collector.cpp
    src/collectors/mem_collector.cpp
    src/collectors/io_collector.cpp
    src/collectors/cache_collector.cpp
    src/exporters/prometheus.cpp
    src/exporters/logging.cpp
)

# Executable
add_executable(inframind_agent ${AGENT_SOURCES})

target_include_directories(inframind_agent PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(inframind_agent PRIVATE
    Threads::Threads
)

# Compiler warnings
target_compile_options(inframind_agent PRIVATE
    -Wall -Wextra -Wpedantic -Werror
)

# Install
install(TARGETS inframind_agent DESTINATION bin)
install(FILES config/agent.yaml DESTINATION etc/inframind)

# Testing (optional)
enable_testing()
