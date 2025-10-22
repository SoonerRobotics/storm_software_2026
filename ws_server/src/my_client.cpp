#include <string>
#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/json.hpp>
#include <iostream>

struct exampleMessageType {
  std::string msg;
  int id;
};

void tag_invoke(boost::json::value_from_tag, boost::json::value& jv, const exampleMessageType& s) {
  jv = {
    {"msg", s.msg},
    {"id", s.id}
  };
}

exampleMessageType tag_invoke(boost::json::value_to_tag<exampleMessageType>, const boost::json::value& jv) {
  const auto obj = jv.as_object();
  return exampleMessageType{
    boost::json::value_to<std::string>(obj.at("msg")),
    boost::json::value_to<int>(obj.at("id"))
  };
}


int main () {
  std::string host;

  std::string port = "8080";

  exampleMessageType msg {
    "hello world",
    1234
  };

  boost::json::value jv = boost::json::value_from(msg);

  std::string data = boost::json::serialize(jv);

  boost::asio::io_context ioc;

  boost::asio::ip::tcp::resolver resolver{ioc};

  boost::beast::websocket::stream<boost::asio::ip::tcp::socket> ws{ioc};

  boost::asio::ip::basic_resolver_results<boost::asio::ip::tcp> results = resolver.resolve(host, port);

  boost::asio::ip::basic_endpoint<boost::asio::ip::tcp> ep = boost::asio::connect(ws.next_layer(), results);

  host += ":" + std::to_string(ep.port());

  ws.handshake(host, "/");

  boost::beast::multi_buffer buffer;

  boost::beast::ostream(buffer) << data;

  std::cout << "before " << boost::beast::make_printable(buffer.data()) << std::endl;

  ws.write(buffer.data());

  buffer.consume(buffer.size());

  ws.read(buffer);

  ws.close(boost::beast::websocket::close_code::normal);

  std::cout << boost::beast::make_printable(buffer.data()) << std::endl;
}