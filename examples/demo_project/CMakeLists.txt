cmake_minimum_required(VERSION 3.20)
project(DemoApp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Demo executable
add_executable(demo_app
    src/main.cpp
    src/calculator.cpp
)

target_include_directories(demo_app PRIVATE include)

# Install
install(TARGETS demo_app DESTINATION bin)

# CPack
set(CPACK_GENERATOR "TGZ")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
include(CPack)
