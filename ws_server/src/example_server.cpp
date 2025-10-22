//
// Copyright (c) 2016-2019 Vinnie Falco (vinnie dot falco at gmail dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// Official repository: https://github.com/boostorg/beast
//

//------------------------------------------------------------------------------
//
// Example: WebSocket server, synchronous
//
//------------------------------------------------------------------------------

#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio.hpp>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <string>
#include <thread>
#include <vector>
#include <future>
<<<<<<< HEAD
#include <vector>
#include <future>
=======
>>>>>>> 7a8c70382425a4f13752e76e3a8b65c364e9f36c

namespace beast = boost::beast;         // from <boost/beast.hpp>
namespace http = beast::http;           // from <boost/beast/http.hpp>
namespace websocket = beast::websocket; // from <boost/beast/websocket.hpp>
namespace net = boost::asio;            // from <boost/asio.hpp>
using tcp = boost::asio::ip::tcp;       // from <boost/asio/ip/tcp.hpp>

//------------------------------------------------------------------------------

struct Sustruct
{
  int id;
  char text[128];

  template <class Archive>
  void serialize(Archive &ar, const unsigned int)
  {
    ar & id;
    ar & text;
  }
};

// Echoes back all received WebSocket messages
boost::asio::awaitable<void> do_session(tcp::socket socket)
{
  try
  {
    // Construct the stream by moving in the socket
    websocket::stream<tcp::socket> ws{std::move(socket)};

    // Set a decorator to change the Server of the handshake
    ws.set_option(websocket::stream_base::decorator(
        [](websocket::response_type &res)
        {
          res.set(http::field::server,
                  std::string(BOOST_BEAST_VERSION_STRING) +
                      " websocket-server-sync");
        }));

    // Accept the websocket handshake
    co_await ws.async_accept(boost::asio::use_awaitable);

    for (;;)
    {
      // This buffer will hold the incoming message
      beast::multi_buffer buffer;

      // Read a message
      co_await ws.async_read(buffer, boost::asio::use_awaitable);

<<<<<<< HEAD
      std::string data = boost::beast::buffers_to_string(buffer.data());

      std::cout << "heard: " + data << std::endl;
=======
      std::string msg = "echoing: " + beast::buffers_to_string(buffer.data());
>>>>>>> 7a8c70382425a4f13752e76e3a8b65c364e9f36c

      buffer.consume(buffer.size());

      data = "echoing " + data;

<<<<<<< HEAD
      beast::ostream(buffer) << data;

      // // Echo the message back
      co_await ws.async_write(buffer.data(), boost::asio::use_awaitable);

      std::cout << "reached here" << std::endl;
=======
      // Echo the message back
      ws.write(buffer.data());
>>>>>>> 7a8c70382425a4f13752e76e3a8b65c364e9f36c
    }
  }
  catch (beast::system_error const &se)
  {
    // This indicates that the session was closed
    if (se.code() != websocket::error::closed)
      std::cerr << "Error: " << se.code().message() << std::endl;
  }
  catch (std::exception const &e)
  {
    std::cerr << "Error: " << e.what() << std::endl;
  }
}

//------------------------------------------------------------------------------

int main(int argc, char *argv[])
{
  try
  {
    // Check command line arguments.
    if (argc != 3)
    {
      std::cerr << "Usage: websocket-server-sync <address> <port>\n"
                << "Example:\n"
                << "    websocket-server-sync 0.0.0.0 8080\n";
      return EXIT_FAILURE;
    }
    auto const address = net::ip::make_address(argv[1]);
    auto const port = static_cast<unsigned short>(std::atoi(argv[2]));

    // The io_context is required for all I/O
    net::io_context ioc{1};

    // The acceptor receives incoming connections
    tcp::acceptor acceptor{ioc, {address, port}};
    for (;;)
    {
      // This will receive the new connection
      tcp::socket socket{ioc};

      // Block until we get a connection
      acceptor.accept(socket);

<<<<<<< HEAD

      auto work_guard = boost::asio::make_work_guard(ioc);

      // Launch the session, transferring ownership of the socket
      std::future<void> f = boost::asio::co_spawn(ioc, do_session(std::move(socket)), boost::asio::use_future);

      ioc.run();

      std::cout << "coroutine running in the background" << std::endl;

      f.get();

      std::cout << "coroutine done" << std::endl;
=======
      std::vector<std::future<void>> sessions;

      // Launch the session, transferring ownership of the socket
      sessions.push_back(std::async(std::launch::async, do_session, std::move(socket)));
>>>>>>> 7a8c70382425a4f13752e76e3a8b65c364e9f36c
    }
  }
  catch (const std::exception &e)
  {
    std::cerr << "Error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }
}