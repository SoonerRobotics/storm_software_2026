cmake_minimum_required(VERSION 3.3)

project(ws_server LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Boost REQUIRED COMPONENTS system json)

find_package(libhv REQUIRED)

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

function(add_libhv_executable name source)
  add_executable(${name} ${source})
  target_link_libraries(${name} PUBLIC hv)
  target_include_directories(${name} PUBLIC ${hv_INCLUDE_DIRS})
endfunction()

add_boost_executable(my_server src/my_server.cpp)

add_boost_executable(relay_server src/relay_server.cpp)

add_libhv_executable(hv_server src/hv_server.cpp)

add_libhv_executable(hv_client src/hv_client.cpp)
