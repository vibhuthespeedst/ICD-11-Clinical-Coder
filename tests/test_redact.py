import json
import unittest
from pathlib import Path

from coder.redact import redact

ROOT = Path(__file__).resolve().parent.parent


class RedactTest(unittest.TestCase):
    def test_direct_identifiers_are_removed(self):
        note = ("Name: Achieng Otieno\nIP No: 2024/1234\nTel: 0712 345 678\n"
                "Seen by Dr. Mwangi with Mrs Wanjiru Kamau, email amina.k@example.com, +254 712 345678, ID 12345678.\n"
                "DOB 12/03/1990. Patient: My name is Amina Hassan and I have fever.")
        out = redact(note)
        for gone in ("Achieng", "2024/1234", "0712", "Mwangi", "Wanjiru", "Kamau", "amina.k@", "712 345678", "12345678",
                     "12/03/1990", "Amina Hassan"):
            self.assertNotIn(gone, out)
        self.assertIn("Dr. [NAME]", out)
        self.assertIn("I have fever", out)

    def test_clinical_values_survive(self):
        note = ("BP 118/76, T 38.9, SpO2 98%, Hb 13.4, MUAC <11.5. Coartem 80/480 1 tab BD x3/7, review 4/52. "
                "G1P0 at 12/40. Doctor: This is chickenpox. Imp: HTN stage 2, start Amlodipine 5mg OD. VL 1000000.")
        self.assertEqual(redact(note), note)

    def test_dev_notes_are_unchanged(self):
        notes = [json.loads(line) for line in open(ROOT / "data" / "dev_notes.jsonl", encoding="utf-8")]
        changed = [n["id"] for n in notes if redact(n["text"]) != n["text"]]
        self.assertEqual(changed, [])


if __name__ == "__main__":
    unittest.main()
