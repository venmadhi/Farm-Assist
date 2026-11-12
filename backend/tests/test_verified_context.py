import unittest
import sys
import os

# Add the backend directory to the path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chatbot.response_generator import ResponseGenerator

class TestVerifiedContext(unittest.TestCase):
    def setUp(self):
        self.rg = ResponseGenerator()

    def test_intent_matching(self):
        # A document about Rice Stem Borer
        kb_block = """Document Title: Rice Stem Borer Treatment
Crop: rice
Intent: PEST_CONTROL, PEST_IDENTIFICATION
English Content: Stem borer is a major pest of rice..."""
        
        # Verify that PEST_MANAGEMENT correctly matches PEST_CONTROL via intent mapping
        result = self.rg._verified_context(
            kb_context=kb_block, 
            intent="PEST_MANAGEMENT", 
            query="how to control pests in rice", 
            crop_entity="rice"
        )
        self.assertTrue(bool(result), "PEST_MANAGEMENT should match PEST_CONTROL document intent")

        # Verify that a completely different intent (e.g. FERTILIZER) is rejected
        result_fail = self.rg._verified_context(
            kb_context=kb_block, 
            intent="FERTILIZER", 
            query="what fertilizer for rice", 
            crop_entity="rice"
        )
        self.assertFalse(bool(result_fail), "FERTILIZER intent should reject PEST_CONTROL document")

    def test_keyword_fallback(self):
        # A document without explicit Intent field
        kb_block = """Document Title: General Storage Guidelines
Crop: general
English Content: Ensure proper drying and storage to prevent spoilage."""
        
        # POST_HARVEST_STORAGE should match via keyword fallback ("drying", "storage", "spoilage")
        result = self.rg._verified_context(
            kb_context=kb_block, 
            intent="POST_HARVEST_STORAGE", 
            query="how to store", 
            crop_entity=None
        )
        self.assertTrue(bool(result), "POST_HARVEST_STORAGE should match via keyword fallback")

        # PEST_MANAGEMENT should fail via keyword fallback
        result_fail = self.rg._verified_context(
            kb_context=kb_block, 
            intent="PEST_MANAGEMENT", 
            query="how to control pests", 
            crop_entity=None
        )
        self.assertFalse(bool(result_fail), "PEST_MANAGEMENT should fail via keyword fallback on storage doc")

if __name__ == '__main__':
    unittest.main()
