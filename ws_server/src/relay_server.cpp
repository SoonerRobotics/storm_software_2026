#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/json.hpp>
#include <iostream>
#include <future>
#include <boost/asio.hpp>
#include <unordered_map>

#define SERVER_IP "0.0.0.0"

#define SERVER_PORT "8080"

std::unordered_map<std::string, std::shared_ptr<boost::beast::websocket::stream<boost::asio::ip::tcp::socket>>> websocket_table;

struct addressedData {
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

boost::asio::awaitable<void> forward(const std::string &client_id, const std::string &message) {

  auto ex = co_await boost::asio::this_coro::executor;

  std::cout << "forwarding message to client_id: " << client_id << " message: " << message << std::endl;

  auto it = websocket_table.find(client_id);
  if (it != websocket_table.end()) {
    auto socket_ptr = it->second;

    boost::beast::multi_buffer buffer;

    addressedData returnMsg {
      client_id,
      message
    };

    boost::json::value jv = boost::json::value_from(returnMsg);

    std::string data = boost::json::serialize(jv);

    std::cout << "forwarding data: " << data << std::endl;

    co_await socket_ptr->async_write(boost::asio::buffer(data), boost::asio::use_awaitable);
  } else {
    std::cerr << "Client ID not found: " << client_id << std::endl;
  }
}

boost::asio::awaitable<void> do_session(const std::string &client_id) {
  auto ex = co_await boost::asio::this_coro::executor;

  std::cout << "starting session" << std::endl;

  // read a message from the websocket
  auto it = websocket_table.find(client_id);
  if (it == websocket_table.end()) {
    std::cerr << "Client ID not found: " << client_id << std::endl;
    co_return;
  }

  auto socket_ptr = it->second;

  boost::beast::multi_buffer buffer;

  try {
    for (;;) {
      co_await socket_ptr->async_read(buffer, boost::asio::use_awaitable);
      std::string data = boost::beast::buffers_to_string(buffer.data());
      std::cout << "received: " << data << std::endl;

      // parse the message
      boost::json::value jv = boost::json::parse(data);
      addressedData received = boost::json::value_to<addressedData>(jv);

      // call forward with the address and message
      auto it = websocket_table.find(received.client_id);

      boost::asio::co_spawn(ex, forward(received.client_id, received.jsonMsgData), boost::asio::detached);

      buffer.consume(buffer.size());
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
}

boost::asio::awaitable<void> event_loop(boost::asio::ip::tcp::acceptor &acceptor)
{
  auto ex = co_await boost::asio::this_coro::executor;

  std::cout << "event loop running" << std::endl;

  for (;;)
  {
    boost::asio::ip::tcp::socket socket{ex};
    co_await acceptor.async_accept(socket, boost::asio::use_awaitable);

    auto ws_ptr = std::make_shared<boost::beast::websocket::stream<boost::asio::ip::tcp::socket>>(std::move(socket));

    co_await ws_ptr->async_accept(boost::asio::use_awaitable);

    std::string client_id = ws_ptr->next_layer().remote_endpoint().address().to_string() + ":" +
                            std::to_string(ws_ptr->next_layer().remote_endpoint().port());

    websocket_table.emplace(client_id, ws_ptr);

    boost::asio::co_spawn(ex, do_session(client_id), boost::asio::detached);

    std::cout << "New client connected: " << client_id << std::endl;
  }
}

int main () {
  // a hashmap of websockets
  // in the event loop, define an acceptor. When a new client connects, add the websocket to the hashmap
  // in forward(), lookup the ws by its id (address) and

  boost::asio::io_context ioc{1};

  const auto address = boost::asio::ip::make_address(SERVER_IP);

  const auto port = static_cast<unsigned short>(std::atoi(SERVER_PORT));

  //acceptor
  boost::asio::ip::tcp::acceptor acceptor{ioc, {address, port}};

  std::future<void> f = boost::asio::co_spawn(ioc, event_loop(acceptor), boost::asio::use_future);

  ioc.run();
}