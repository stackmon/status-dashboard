import asyncio
import json
import os
import signal

import aiohttp

from modules.logger import get_logger
from modules.ws_status import handle_close_code

from websockets import serve


# Link to API of stackmon status dashboard
API_LINK = os.getenv("API_LINK", "http://127.0.0.1:5000/api/v1/incidents")
# INTERVAL is timeout for checking changes (in seconds)
INTERVAL = int(os.getenv("INTERVAL", 60))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 3))
log_level = os.getenv("LOG_LEVEL", "INFO")
# Setup logging
logger = get_logger(log_level)


class SignalHandler:
    KEEP_PROCESSING = True

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.info("Exiting gracefully")
        self.KEEP_PROCESSING = False


class DataProcessor:
    def __init__(self):
        self.api_link = API_LINK
        self.previous_data = []
        self.is_first_iteration = True
        self.connected_clients = set()

    async def check_api_availability(self):
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    self.api_link,
                    timeout=REQUEST_TIMEOUT
                ) as response,
            ):
                if response.status == 200:
                    return True
                logger.error(
                    "API is not available. Status code: %s",
                    response.status
                )
        except aiohttp.ClientError as req_error:
            logger.error(f"Failed to connect to API: {str(req_error)}")

        return False

    async def fetch_data(self):
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    self.api_link,
                    timeout=REQUEST_TIMEOUT
                ) as response,
            ):
                if response.status == 200:
                    data = await response.json()
                    if not data:
                        return data, 204
                    return data, 200
                logger.error("Failed to fetch data from API")
        except aiohttp.ClientError as req_error:
            logger.error(f"Failed to fetch data from API: {str(req_error)}")
        return None

    def find_changed_items(self, current_data):
        changed_items = []
        previous_ids = set(item["id"] for item in self.previous_data)

        # New items
        new_items = [
            item for item in current_data if item["id"] not in previous_ids
        ]
        if new_items:
            changed_items.extend(new_items)

        # Changed items
        for item in current_data:
            if item["id"] in previous_ids:
                previous_item = next(
                    (
                        i for i in self.previous_data if i["id"] == item["id"]
                    ),
                    None
                )
                if previous_item and item != previous_item:
                    changed_items.append(item)

        return changed_items

    async def check_changes(self):
        while True:
            logger.debug("Checking changes")
            current_data, status_code = await self.fetch_data()
            if current_data is not None:
                if status_code != 204:
                    changed_items = self.find_changed_items(current_data)
                    if not self.is_first_iteration and changed_items:
                        message = "Changes: " + json.dumps(changed_items)
                        for client in self.connected_clients:
                            await client.send(message)
                    self.previous_data = current_data
                    self.is_first_iteration = False

            await asyncio.sleep(INTERVAL)

    async def handle_connection(self, websocket):
        check_changes_task = None
        try:
            self.connected_clients.add(websocket)
            logger.info("New client connected")
            check_changes_task = asyncio.create_task(
                self.check_changes()
            )

            while True:
                message = await websocket.recv()
                if message != "get_incidents":
                    await websocket.send(
                        "Enter 'get_incidents' to get current incidents"
                    )
                    continue

                logger.info("Received 'get_incidents' request from client")

                current_data, status_code = await self.fetch_data()
                logger.info(
                    f"current data: {current_data}, "
                    f"status code: {status_code}, "
                )

                if current_data is None:
                    logger.error("Failed to fetch data from API")
                    await websocket.send(
                        "Failed to fetch data from API"
                    )
                    continue
                if status_code == 204:
                    logger.debug("Sending 'There are no incidents' message")
                    await websocket.send("There are no incidents")
                else:
                    logger.debug("Sending data to client")
                    await websocket.send(json.dumps(current_data))
        except Exception as error:
            logger.error("Type of Error: %s", type(error))
            close_reason = handle_close_code(error.code)
            if error.code == 1005 or error.code == 1000:
                logger.info("Close reason: %s", close_reason)
            else:
                logger.error("Close reason: %s", close_reason)
                if error.code:
                    logger.error("Status code is: %s", error.code)
        finally:
            self.connected_clients.remove(websocket)
            logger.info("Connection closed")
            if check_changes_task is not None:
                check_changes_task.cancel()

    async def start_server(self):
        async with serve(self.handle_connection, "localhost", 8765):
            logger.info("WebSocket server started")
            while signal_handler.KEEP_PROCESSING:
                await asyncio.sleep(0.0005)

    async def run(self):
        api_available = await self.check_api_availability()
        if not api_available:
            logger.error("API is not available. Exiting...")
            return

        await self.start_server()


if __name__ == "__main__":
    signal_handler = SignalHandler()
    data_processor = DataProcessor()
    print(f"Current log level: {logger.level}")
    asyncio.run(data_processor.run())
