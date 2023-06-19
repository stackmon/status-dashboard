import unittest
from unittest.mock import AsyncMock, patch

from server import DataProcessor, handle_close_code


class TestDataProcessor(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_response = [
            {
                "end_date": "2023-08-22 15:12",
                "id": 1,
                "impact": 2,
                "start_date": "2023-08-22 17:08",
                "text": "Incident 002",
                "updates": [
                    {
                        "status": "actual",
                        "text": "Acknowledged",
                        "timestamp": "2023-08-22 15:13"
                    },
                    {
                        "status": "non actual",
                        "text": "Acknowledged",
                        "timestamp": "2023-08-22 15:12"
                    }
                ]
            },
            {
                "end_date": "2023-08-22 15:21",
                "id": 2,
                "impact": 2,
                "start_date": "2023-08-22 17:15",
                "text": "Incident 003",
                "updates": [
                    {
                        "status": "non actual",
                        "text": "Acknowledged",
                        "timestamp": "2023-08-22 15:22"
                    }
                ]
            }
        ]

    @patch("server.aiohttp.ClientSession.get")
    async def test_fetch_data_with_mock_api_response(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = self.api_response
        mock_get.return_value.__aenter__.return_value = mock_response

        data_processor = DataProcessor()
        result_data, status_code = await data_processor.fetch_data()
        self.assertEqual(result_data, self.api_response)
        self.assertEqual(status_code, 200)

    @patch("server.aiohttp.ClientSession.get")
    async def test_fetch_data_empty_response(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = []  # Empty response
        mock_get.return_value.__aenter__.return_value = mock_response

        data_processor = DataProcessor()
        result_data, status_code = await data_processor.fetch_data()
        self.assertEqual(result_data, [])
        self.assertEqual(status_code, 204)

    @patch("server.aiohttp.ClientSession.get")
    async def test_check_api_availability_success(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        data_processor = DataProcessor()
        api_available = await data_processor.check_api_availability()
        self.assertTrue(api_available)

    def test_find_changed_items(self):
        data_processor = DataProcessor()
        data_processor.previous_data = [
            {"id": 1, "text": "Incident 001"},
            {"id": 2, "text": "Incident 002"}
        ]

        current_data = [
            {"id": 2, "text": "Incident 002 (updated)"},
            {"id": 3, "text": "Incident 003"}
        ]

        changed_items = data_processor.find_changed_items(current_data)
        self.assertCountEqual(changed_items, [
            {"id": 2, "text": "Incident 002 (updated)"},
            {"id": 3, "text": "Incident 003"}
        ])

    def test_handle_close_code(self):
        close_code = 1000
        status = handle_close_code(close_code)
        self.assertEqual(status, "Normal closure")

        unknown_code = 9999
        status = handle_close_code(unknown_code)
        self.assertEqual(
            status, f"Unknown close code: {unknown_code} or no status = code"
        )


if __name__ == "__main__":
    unittest.main()
