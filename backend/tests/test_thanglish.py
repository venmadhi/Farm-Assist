import sys
import os
import unittest

# Adjust path to import backend app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml.thanglish_normalizer import thanglish_normalizer

class TestThanglishNormalization(unittest.TestCase):
    def test_spelling_variations(self):
        # vaazha, vaza, vazhakk should normalize to vazha
        self.assertEqual(thanglish_normalizer.normalize("vaazha krishi"), "vazha krishi")
        self.assertEqual(thanglish_normalizer.normalize("vaza leaf"), "vazha ila")
        
        # vellom, velam should normalize to vellam
        self.assertEqual(thanglish_normalizer.normalize("vellom venam"), "vellam venam")
        
        # vlam should normalize to valam
        self.assertEqual(thanglish_normalizer.normalize("paddykk eth vlam nallath"), "nellu eth valam nallath")

    def test_suffix_stripping(self):
        # Suffixes like -inu, -il, -ude, -nte should be stripped when mapping key terms
        self.assertEqual(thanglish_normalizer.normalize("nellinu valam"), "nellu valam")
        self.assertEqual(thanglish_normalizer.normalize("soilil nitrogen"), "soil nitrogen")
        self.assertEqual(thanglish_normalizer.normalize("vazhayude ila"), "vazha ila")
        
    def test_english_insertion_standardization(self):
        # English terms like leaf, low, price should map to unified labels
        self.assertEqual(thanglish_normalizer.normalize("banana leaf yellow color"), "banana ila manja color")
        self.assertEqual(thanglish_normalizer.normalize("potassium low aanu"), "potassium kuravu aanu")
        self.assertEqual(thanglish_normalizer.normalize("market price rate"), "market vila vila")

if __name__ == '__main__':
    unittest.main()
