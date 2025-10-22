#include "boost/asio.hpp"
#include "boost/beast/core.hpp"
#include "boost/beast/websocket.hpp"
#include <iostream>
#include <future>
#include <chrono>


boost::asio::awaitable<void> do_session(boost::asio::ip::tcp::socket socket) {
  boost::beast::websocket::stream<boost::asio::ip::tcp::socket> ws(std::move(socket));

  co_await ws.async_accept(boost::asio::use_awaitable);

  boost::beast::multi_buffer buffer;

  
  try {
    for (;;) {
      co_await ws.async_read(buffer, boost::asio::use_awaitable);

      std::string data = boost::beast::buffers_to_string(buffer.data());

      buffer.consume(buffer.size()); // clear buffer

      std::cout << "heard: " + data << std::endl;

      data = "echoing " + data;

      boost::beast::ostream(buffer) << data;

      co_await ws.async_write(buffer.data(), boost::asio::use_awaitable);
    }
  }

  catch (boost::beast::system_error const &se)
  {
    // This indicates that the session was closed
    if (se.code() != boost::beast::websocket::error::closed)
      std::cerr << "Error: " << se.code().message() << std::endl;
  }
  catch (std::exception const &e)
  {
    std::cerr << "Error: " << e.what() << std::endl;
  }
  

  std::cout << "reached the end of read write" << std::endl;
}

boost::asio::awaitable<void> other_work() {
  const auto ex = co_await boost::asio::this_coro::executor;

  for (;;) {
    boost::asio::steady_timer timer(ex);
    std::cout << "doing other work" << std::endl; 
    timer.expires_after(std::chrono::seconds(5));

    co_await timer.async_wait(boost::asio::use_awaitable);
    std::cout << "done with other work" << std::endl;
  }
}

boost::asio::awaitable<void> event_loop(boost::asio::ip::tcp::acceptor& acceptor) {
  // these run once
  auto ex = co_await boost::asio::this_coro::executor;

  boost::asio::co_spawn(ex, other_work(), boost::asio::detached);

  // event loop
  for (;;) {
    std::cout << "event loop running" << std::endl;
    
    boost::asio::ip::tcp::socket socket{ex};

    co_await acceptor.async_accept(socket, boost::asio::use_awaitable);

    boost::asio::co_spawn(ex, do_session(std::move(socket)), boost::asio::detached);

    std::cout << "event loop continuing" << std::endl;
  };
}

int main () {
  boost::asio::io_context ioc{1};
  
  auto const address = boost::asio::ip::make_address("0.0.0.0");
  
  auto const port = 8080;

  boost::asio::ip::tcp::acceptor acceptor{ioc, {address, port}};

  std::future<void> f = boost::asio::co_spawn(ioc, event_loop(acceptor), boost::asio::use_future);

  ioc.run();
}