#include <iostream>
#include <boost/asio.hpp>
#include <chrono>

boost::asio::awaitable<void> my_func(int num) {
  boost::asio::any_io_executor exec = co_await boost::asio::this_coro::executor;

  boost::asio::steady_timer timer(exec);

  timer.expires_after(std::chrono::seconds(num));

  co_await timer.async_wait(boost::asio::use_awaitable);

  std::cout << "timer " << num << " has finished!" << std::endl;
}

int main () {
  boost::asio::io_context ioc;

  boost::asio::co_spawn(ioc, my_func(10), boost::asio::detached);

  boost::asio::co_spawn(ioc, my_func(5), boost::asio::detached);

  ioc.run();

  std::cout << "ioc finished running" << std::endl;

  return 0;
}