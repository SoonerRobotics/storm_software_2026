#include <cstdlib>

int main () {
  std::system("../ws_server/build/relay_server");
  std::system("../ws_server/build/client1");
  std::system("../ws_server/build/client2");

  return 0;
}