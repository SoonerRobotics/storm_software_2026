import asyncio
import cv2

from websockets import serve

from daniel_testing.command_robot import BASE_STATION_ADDRESS, BASE_STATION_PORT

#TODO keep these out of the module/package namespace?
camera = None
#TODO FIXME adjust these
DRIVER_CAMERA_PARAMS = [cv2.IMWRITE_JPEG_QUALITY, 50, cv2.IMWRITE_JPEG_OPTIMIZE, 1]

async def send_camera_frame(websocket):

    if camera is None:
        #TODO FIXME do somethihng?
        return

    else:
        ret, frame = camera.read()

    #TODO FIXME rate-limit ourselves somehow or something?

    #TODO FIXME resize the image too

    if not ret:
        # TODO FIXME what to do if no camera???
        return
    else:
        #TODO jpeg for speed, is this even worth it? too much delay on Pi?
        encoded = cv2.imencode(".jpg", frame)


        await websocket.send(frame)

async def main():
    async with serve(send_camera_frame, BASE_STATION_ADDRESS, BASE_STATION_PORT) as server:
        await server.serve_forever()

if __name__ == "__main__":
    camera = cv2.VideoCapture(0) #TODO FIXME which port/whatever?

    try:
        asyncio.run(main())
    finally:
        camera.release