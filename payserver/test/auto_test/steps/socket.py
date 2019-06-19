import threading
import asyncio
import logging

from channels.testing import WebsocketCommunicator

from payserver.asgi import application

logger = logging.getLogger(__name__)


class WebSocketThread(threading.Thread):
    def __init__(self, event, marketer_token, channel, queue):
        super().__init__()
        self.event = event
        self.marketer_token = marketer_token
        self.channel = channel
        self.queue = queue

    def run(self):
        self.start_create_web_socket()

    def start_create_web_socket(self):
        logger.info(f'start to create web-socket')

        ws_url = f'/ws/ws-service/{self.channel}/?token={self.marketer_token}'

        async def t_run():
            try:
                communicator = WebsocketCommunicator(application, ws_url)
                connected, subprotocol = await communicator.connect()
                assert connected
                logger.info("websocket connect success")
                self.event.set()

                message = await communicator.receive_json_from()
                logger.info(f"web-socket receive message: {message}")
                self.queue.put(message)

                await communicator.disconnect()
                logger.info("disconnect web-socket")
            except Exception as e:
                logger.error(e)
                self.event.set()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        coro = asyncio.coroutine(t_run)
        loop.run_until_complete(coro())
        loop.close()
        logger.info("WebSocketThread will be destroy")
        print("WebSocketThread will be destroy")