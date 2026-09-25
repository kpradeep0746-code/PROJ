import unittest
from unittest.mock import patch
from app import app


class TestBackendAPI(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home_endpoint(self):
        """Verify home endpoint returns 200 and success status."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("running", data["message"])

    def test_transcript_missing_url(self):
        """Verify 400 when URL is missing."""
        response = self.client.post("/api/transcript", json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    @patch("app.get_transcript")
    @patch("app.format_transcript_with_gemini")
    def test_transcript_success(self, mock_format, mock_get_trans):
        """Verify successful transcript fetching and formatting."""
        mock_get_trans.return_value = {
            "success": True,
            "video_id": "dQw4w9WgXcQ",
            "transcript": "Hello world"
        }
        mock_format.return_value = {
            "success": True,
            "transcript": "# Hello World"
        }

        response = self.client.post(
            "/api/transcript",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["transcript"], "# Hello World")

    def test_translate_missing_params(self):
        """Verify 400 when missing target_language."""
        response = self.client.post("/api/translate", json={"transcript": "Hello"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])


if __name__ == "__main__":
    unittest.main()
