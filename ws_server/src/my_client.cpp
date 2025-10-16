#include <string>
#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <iostream>

int main () {
  std::string host;

  char * port = "8080";

  std::string text = "hello world";

  boost::asio::io_context ioc;

  boost::asio::ip::tcp::resolver resolver{ioc};

  boost::beast::websocket::stream<boost::asio::ip::tcp::socket> ws{ioc};

  boost::asio::ip::basic_resolver_results<boost::asio::ip::tcp> results = resolver.resolve(host, port);

  boost::asio::ip::basic_endpoint<boost::asio::ip::tcp> ep = boost::asio::connect(ws.next_layer(), results);

  host += ":" + std::to_string(ep.port());

  ws.handshake(host, "/");

  boost::beast::multi_buffer buffer;

  boost::beast::ostream(buffer) << text;

  ws.write(buffer.data());

  buffer.consume(buffer.size());

  std::cout << "before " << boost::beast::make_printable(buffer.data()) << std::endl;

  ws.read(buffer);

  ws.close(boost::beast::websocket::close_code::normal);

  std::cout << boost::beast::make_printable(buffer.data()) << std::endl;
}