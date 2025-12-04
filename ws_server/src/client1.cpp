#include "hv/WebSocketClient.h"
#include "hv/json.hpp"
using namespace hv;

#define SERVER_PORT 1909

struct addressedData {
    std::string sender;
    std::string destination;
    std::string data;
};

struct exampleDataType {
  int ID;
  std::string message;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(addressedData, sender, destination, data);

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(exampleDataType, ID, message);

int main(int argc, char **argv)
{
  WebSocketClient ws;
  ws.onopen = [&]()
  {
    printf("onopen\n");
    addressedData ad;
    ad.sender = "client1";
    ad.destination = "init";
    ad.data = "init";

    Json j = ad;
    ws.send(j.dump());
  };
  ws.onmessage = [&](const std::string &msg)
  {
    addressedData received_ad = Json::parse(msg);
    std::cout << "heard: " << received_ad.data << std::endl;

    // send a message to client2
    addressedData ad;
    ad.sender = "client1";
    ad.destination = "client2";
    
    // create struct
    exampleDataType edt_instance;
    edt_instance.ID = 200;
    edt_instance.message = "Hello Client2!";

    // serialize the struct
    Json edt_j = edt_instance;

    // pack into addressed data
    ad.data = edt_j.dump();

    Json j = ad;
    ws.send(j.dump());
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

  std::string server_address = std::format("ws://127.0.0.1:{}", SERVER_PORT);

  ws.open(server_address.c_str());

  return 0;
}