import unittest

from coder.offline import OfflineCoder
from coder.text import is_english


class LanguageTest(unittest.TestCase):
    def test_english_notes_and_terms(self):
        self.assertTrue(is_english("Pt c/o fever x3/7. O/E: T 38.9. A: malaria. Plan: Coartem."))
        self.assertTrue(is_english("falciparum malaria"))

    def test_other_languages(self):
        self.assertFalse(is_english("Paciente de 34 años que presenta dolor abdominal desde hace tres días."))
        self.assertFalse(is_english("Patient se plaint de douleur depuis deux jours avec fièvre."))
        self.assertFalse(is_english("Mgonjwa ana homa kwa siku tatu na kikohozi."))
        self.assertFalse(is_english("المريض يعاني من حمى وسعال منذ ثلاثة أيام"))

    def test_spanish_notes_use_spanish_who_terms(self):
        coder = OfflineCoder()
        for note, gold in [
            ("Mujer de 54 años con capsulitis adhesiva del hombro derecho, dolor y rigidez de cuatro meses.", "FB53.0"),
            ("Varón de 30 años con esquistosomiasis urinaria, hematuria terminal tras bañarse en el lago.", "1F86.0"),
            ("Niño de 8 años con tungiasis en los dedos de los pies, se extraen las pulgas.", "1G05"),
        ]:
            self.assertEqual(coder.predict(note)[0], gold)
        self.assertIsNotNone(coder.multi)


if __name__ == "__main__":
    unittest.main()
