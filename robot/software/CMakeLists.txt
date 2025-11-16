cmake_minimum_required(VERSION 3.3)

project(robot_software LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Boost REQUIRED COMPONENTS system json)

find_package(libhv REQUIRED)

function(add_libhv_executable name source)
  add_executable(${name} ${source})
  target_link_libraries(${name} PUBLIC hv)
  target_include_directories(${name} PUBLIC ${hv_INCLUDE_DIRS})
endfunction()

# ADD YOUR ROBOT SOFTWARE FILES HERE
add_libhv_executable(hardware_interface src/hardwar_interface.cpp)
