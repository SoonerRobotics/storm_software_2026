#include <string>
#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/json.hpp>
#include <iostream>

#define CLIENT_IP "127.0.0.1"

struct addressedData
{
  std::string client_id;
  std::string jsonMsgData;
};

void tag_invoke(boost::json::value_from_tag, boost::json::value &jv, const addressedData &s)
{
  jv = {
      {"client_id", s.client_id},
      {"jsonMsgData", s.jsonMsgData}};
}

addressedData tag_invoke(boost::json::value_to_tag<addressedData>, const boost::json::value &jv)
{
  const auto obj = jv.as_object();
  return addressedData{
      boost::json::value_to<std::string>(obj.at("client_id")),
      boost::json::value_to<std::string>(obj.at("jsonMsgData"))};
}

int main (int argc, char* argv[]) {
  std::string host = "0.0.0.0";

  std::string port = "8080";


  boost::asio::io_context ioc;

  boost::asio::ip::tcp::resolver resolver{ioc};

  boost::beast::websocket::stream<boost::asio::ip::tcp::socket> ws{ioc};

  boost::asio::ip::basic_resolver_results<boost::asio::ip::tcp> results = resolver.resolve(host, port);

  boost::asio::connect(ws.next_layer(), results);

  host += ":" + std::to_string(ws.next_layer().remote_endpoint().port());

  ws.handshake(host, "/");

  boost::beast::multi_buffer buffer;

  auto address_port = ws.next_layer().local_endpoint().address().to_string() + ":" + std::to_string(ws.next_layer().local_endpoint().port());

  addressedData msg = {address_port, "Hello, World!"};

  boost::json::value jv = boost::json::value_from(msg);

  std::string data = boost::json::serialize(jv);

  boost::beast::ostream(buffer) << data;

  std::cout << "before " << boost::beast::make_printable(buffer.data()) << std::endl;

  ws.write(buffer.data());

  buffer.consume(buffer.size());

  ws.read(buffer);

  std::cout << boost::beast::make_printable(buffer.data()) << std::endl;

  for (;;) {

  }
}