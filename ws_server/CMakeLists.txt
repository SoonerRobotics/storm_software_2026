cmake_minimum_required(VERSION 3.3)

project(ws_server LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Boost REQUIRED COMPONENTS system json)

add_executable(hw src/hello_world.cpp)

add_executable(server src/example_server.cpp)

add_executable(client src/example_client.cpp)

add_executable(my_client src/my_client.cpp)

target_link_libraries(client PUBLIC ${Boost_LIBRARIES})

target_include_directories(client PUBLIC ${Boost_INCLUDE_DIRS})

target_link_libraries(server PUBLIC ${Boost_LIBRARIES})

target_include_directories(server PUBLIC ${Boost_INCLUDE_DIRS})

target_link_libraries(my_client PUBLIC ${Boost_LIBRARIES})

target_include_directories(my_client PUBLIC ${Boost_INCLUDE_DIRS})

function(add_boost_executable name source)
  add_executable(${name} ${source})
  target_link_libraries(${name} PUBLIC ${Boost_LIBRARIES})
  target_include_directories(${name} PUBLIC ${Boost_INCLUDE_DIRS})
endfunction()

add_boost_executable(my_server src/my_server.cpp)
