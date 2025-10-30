#include "hv/WebSocketClient.h"
#include "hv/json.hpp"
using namespace hv;

struct addressedData {
    std::string address;
    std::string data;
};

int main(int argc, char **argv)
{
  WebSocketClient ws;
  ws.onopen = [&]()
  {
    printf("onopen\n");
    addressedData ad;
    ad.address = ws.channel.get()->localaddr();
    ad.data = "Hello, server!";

    Json j;
    j["address"] = ad.address;
    j["data"] = ad.data;
    ws.send(j.dump());
  };
  ws.onmessage = [](const std::string &msg)
  {
    printf("onmessage: %.*s\n", (int)msg.size(), msg.data());
  };
  ws.onclose = []()
  {
    printf("onclose\n");
  };

  // reconnect: 1,2,4,8,10,10,10...
  reconn_setting_t reconn;
  reconn_setting_init(&reconn);
  reconn.min_delay = 1000;
  reconn.max_delay = 10000;
  reconn.delay_policy = 2;
  ws.setReconnect(&reconn);

  ws.open("ws://127.0.0.1:9999");

  std::string str;
  while (std::getline(std::cin, str))
  {
    if (!ws.isConnected())
      break;
    if (str == "quit")
    {
      ws.close();
      break;
    }
    ws.send(str);
  }

  return 0;
}