import sys
import os
import unittest

# Adjust path to import backend app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml.language_detector import language_detector

class TestMultilingualDetection(unittest.TestCase):
    def test_english_detection(self):
        queries = [
            "what fertilizer is good for paddy?",
            "How can I increase banana yield?",
            "What crop is suitable for my soil?",
            "Which crop gives better profit this season?"
        ]
        for q in queries:
            lang = language_detector.detect(q)
            self.assertEqual(lang, "ENGLISH", f"Failed for query: {q}")

    def test_malayalam_detection(self):
        queries = [
            "എന്റെ നെല്ലിന് ഏത് വളമാണ് വേണ്ടത്?",
            "തെങ്ങിന്റെ കൊമ്പൻ ചെല്ലിയെ എങ്ങനെ നിയന്ത്രിക്കാം?",
            "മണ്ണിലെ അസിഡിറ്റി കുറയ്ക്കാൻ എന്തുചെയ്യണം?"
        ]
        for q in queries:
            lang = language_detector.detect(q)
            self.assertEqual(lang, "MALAYALAM", f"Failed for query: {q}")

    def test_thanglish_detection(self):
        queries = [
            "ente nellinu entha valam venam?",
            "vazhayude ila karuthayi varunnu",
            "vazhakku veetil undakkunna organic fertilizer enthokke aanu",
            "marketil innu banana price engane aanu",
            "soil acidity kurakkan entha cheyya"
        ]
        for q in queries:
            lang = language_detector.detect(q)
            self.assertIn(lang, ["THANGLISH", "MIXED"], f"Failed for query: {q}")

    def test_mixed_detection(self):
        queries = [
            "jeevamrutham/organic manure prepare cheyyan parayu",
            "ente soilil nitrogen low aanu",
            "paddy fieldil disease thടയാൻ എന്ത് ചെയ്യണം?"
        ]
        for q in queries:
            lang = language_detector.detect(q)
            self.assertIn(lang, ["MIXED", "THANGLISH"], f"Failed for query: {q}")

if __name__ == '__main__':
    unittest.main()
