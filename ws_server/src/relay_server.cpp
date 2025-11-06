#include "hv/WebSocketServer.h"
#include "hv/json.hpp"
#include <unordered_map>

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
  {
    printf("onopen: GET %s\n", req->Path().c_str());
  };
  ws.onmessage = [](const WebSocketChannelPtr &channel, const std::string &msg)
  {
    Json j = Json::parse(msg);
    addressedData ad = j;

    std::cout << "onmessage from " << ad.sender << ": " << ad.data << std::endl;

    // if the sender is new, save the connection
    if (connections_map.find(ad.sender) == connections_map.end()) {
        std::cout << "new sender: " << ad.sender << std::endl;
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
        std::cout << "removing connection for " << it->first << "\n",
        it = connections_map.erase(it);
      else
        it++;
    }
    for (auto &[k, v] : connections_map)
      std::cout << "still connected: " << k << std::endl;
  };

  WebSocketServer server(&ws);
  server.setPort(1909);
  server.setThreadNum(4);
  server.run();
  return 0;
}