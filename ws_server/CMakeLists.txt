cmake_minimum_required(VERSION 3.3)

project(ws_server LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Boost REQUIRED COMPONENTS system)

add_executable(hw src/hello_world.cpp)

function(add_boost_executable name source)
  add_executable(${name} ${source})
  target_link_libraries(${name} PUBLIC ${Boost_LIBRARIES})
  target_include_directories(${name} PUBLIC ${Boost_INCLUDE_DIRS})
endfunction()

add_boost_executable(server src/example_server.cpp)

add_boost_executable(client src/example_client.cpp)

add_boost_executable(my_client src/my_client.cpp)
