#include "hv/WebSocketServer.h"
#include "hv/json.hpp"
#include <unordered_map>

#define SERVER_PORT 1909

using namespace hv;

struct addressedData {
    std::string sender;
    std::string destination;
    std::string data;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(addressedData, sender, destination, data);

std::unordered_map<std::string, WebSocketChannelPtr> connections_map;

int main(int argc, char **argv)
{
  WebSocketService ws;
  ws.onopen = [](const WebSocketChannelPtr &channel, const HttpRequestPtr &req)
  {};

  ws.onmessage = [](const WebSocketChannelPtr &channel, const std::string &msg)
  {
    Json j = Json::parse(msg);
    addressedData ad = j;

    // if the sender is new, save the connection
    if (connections_map.find(ad.sender) == connections_map.end()) {
        connections_map[ad.sender] = channel;
    }
    
    WebSocketChannelPtr destination_channel;

    // if the address is not known, return
    if (connections_map.find(ad.destination) == connections_map.end()) {
        std::cout << "unknown address: " << ad.destination << std::endl;
        return;
    } else {
        destination_channel = connections_map[ad.destination];
    }

    ad.data = ad.data;
    j = ad;

    // send the message to the address specified in the message
    destination_channel->send(j.dump());
  };
  ws.onclose = [&](const WebSocketChannelPtr &channel)
  {
    for (auto it = connections_map.begin(); it != connections_map.end();)
    {
      if (it->second == channel)
        it = connections_map.erase(it);
      else
        it++;
    }
  };

  WebSocketServer server(&ws);
  server.setPort(SERVER_PORT);
  server.setThreadNum(4);
  server.run();
  return 0;
}