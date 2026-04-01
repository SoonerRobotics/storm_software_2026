import asyncio

from websockets.sync.client import connect


BASE_STATION_ADDRESS = "http://127.0.0.1" #TODO port and actual address
BASE_STATION_PORT = 3333

APRILTAG_ADDRESS = "http://127.0.0.1" #TODO port and actual address (this one can be localhost though I think)


def main():
    with connect(BASE_STATION_ADDRESS) as base_station:
        #TODO FIXME
        pass

    with connect(APRILTAG_ADDRESS) as apriltags:
        #TODO FIXME
        pass


if __name__ == "__main__":
    main()
