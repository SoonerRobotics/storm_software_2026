#include "hv/WebSocketServer.h"
#include "hv/json.hpp"
using namespace hv;

struct addressedData {
    std::string address;
    std::string data;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(addressedData, address, data);

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
    std::cout << "onmessage from " << ad.address << ": " << ad.data << std::endl;
    // echo back
    ad.data = ad.data + " (echo)";
    j = ad;
    channel->send(j.dump());
  };
  ws.onclose = [](const WebSocketChannelPtr &channel)
  {
    printf("onclose\n");
  };

  WebSocketServer server(&ws);
  server.setPort(9999);
  server.setThreadNum(4);
  server.run();
  return 0;
}