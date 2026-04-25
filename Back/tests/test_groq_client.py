import unittest
from unittest.mock import MagicMock, patch
from infrastructure.ai.groq_client import GroqClient

class TestGroqClient(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_key"
        # Mocking the internal Groq client to avoid actual initialization
        with patch("infrastructure.ai.groq_client.Groq") as mock_groq_class:
            self.client = GroqClient(api_key=self.api_key)
            self.client.client = mock_groq_class.return_value

    def test_analyze_personality_ocean(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = '{"traits": {"openness": {"score": 0.8}}}'
        self.client.client.chat.completions.create.return_value = mock_completion

        result = self.client.analyze_personality_ocean("bio test", [{"caption": "post test"}])
        
        self.assertEqual(result["traits"]["openness"]["score"], 0.8)

    def test_infer_context_and_demographics(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = '{"country": "Ecuador"}'
        self.client.client.chat.completions.create.return_value = mock_completion

        result = self.client.infer_context_and_demographics("bio test", ["caption 1"])
        
        self.assertEqual(result["country"], "Ecuador")

if __name__ == "__main__":
    unittest.main()
