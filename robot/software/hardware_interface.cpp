#include "hv/WebSocketClient.h"
#include "hv/json.hpp"
using namespace hv;


// https://pubs.opengroup.org/onlinepubs/7908799/xbd/termios.html ???


// TODO define Serial structs

// TODO define Software Messages 110 and 160

struct addressedData {
    std::string sender;
    std::string destination;
    std::string data;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(addressedData, sender, destination, data);



int main(int argc, char **argv) {
    WebSocketClient ws;

    ws.onopen = [&]() {
        printf("Hardware Interface Initialized!\n");
    };

    // TODO: we need message callbacks for the Autonomous and Manual nodes
    ws.onmessage = [&](const std::string &msg) {
        // addressedData received_ad = Json::parse(msg);
        // std::cout << "heard: " << received_ad.data << std::endl;

        // // send a message to client2
        // addressedData ad;
        // ad.sender = "client1";
        // ad.destination = "client2";
        // ad.data = "Hello, client2!";

        // Json j = ad;
        // ws.send(j.dump());
    };

    ws.onclose = []() {
        printf("Hardware Interface shuting down...\n");
        // TODO cleanup???
    };

    // reconnect: 1,2,4,8,10,10,10...
    reconn_setting_t reconn;
    reconn_setting_init(&reconn);
    reconn.min_delay = 1000;
    reconn.max_delay = 10000;
    reconn.delay_policy = 2;
    ws.setReconnect(&reconn);

    // TODO FIXME
    ws.open("ws://127.0.0.1:1909");


    // TODO main loop goes here???
    std::string str;
    while (std::getline(std::cin, str)) {
        if (!ws.isConnected())
            break;
        if (str == "quit") {
            ws.close();
            break;
        }
        ws.send(str);
    }

    return 0;
}