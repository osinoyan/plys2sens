cmake_minimum_required(VERSION 2.6)
project(SensReader)


set(CMAKE_CXX_COMPILER g++)
message("compiler: ${CMAKE_CXX_COMPILER}")
set(CMAKE_CXX_FLAGS "-std=c++11 -g")
message("cxxflags: ${CMAKE_CXX_FLAGS}")

set(SRC_FILES src/main.cpp)
message("source files: ${SRC_FILES}")
add_executable(${PROJECT_NAME} ${SRC_FILES})


