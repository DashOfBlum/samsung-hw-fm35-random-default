import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location('fm35_patcher', ROOT/'apply_patch.py')
patcher = importlib.util.module_from_spec(loader)
loader.loader.exec_module(patcher)
SPEC = json.loads((ROOT/'patch.json').read_text())
STOCK_PATH = os.environ.get('FM35_STOCK_ROM')


class GuardTests(unittest.TestCase):
    def test_empty_input_rejected(self):
        with self.assertRaises(patcher.PatchError):
            patcher.make_patched_rom(b'', SPEC)

    def test_same_size_wrong_image_rejected(self):
        with self.assertRaises(patcher.PatchError):
            patcher.make_patched_rom(bytes(2097152), SPEC)

    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            stock = folder/'source.ROM'
            stock.write_bytes(b'not firmware')
            output = folder/patcher.FILENAME
            output.write_bytes(b'keep existing file')
            self.assertEqual(patcher.main([str(stock), '--output-dir', str(folder)]), 1)
            self.assertEqual(output.read_bytes(), b'keep existing file')

    def test_source_path_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            stock = folder/patcher.FILENAME
            stock.write_bytes(b'preserve source')
            self.assertEqual(patcher.main([str(stock), '--output-dir', str(folder)]), 1)
            self.assertEqual(stock.read_bytes(), b'preserve source')

    def test_invalid_input_creates_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            stock = folder/'source.ROM'
            stock.write_bytes(b'invalid')
            destination = folder/'output'
            self.assertEqual(patcher.main([str(stock), '--output-dir', str(destination)]), 1)
            self.assertFalse(destination.exists())


@unittest.skipUnless(STOCK_PATH, 'Set FM35_STOCK_ROM for exact reconstruction tests.')
class ReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = Path(STOCK_PATH).read_bytes()

    def test_exact_hardware_tested_output_and_input_preserved(self):
        original_hash = hashlib.sha256(self.stock).hexdigest()
        result = patcher.make_patched_rom(self.stock, SPEC)
        self.assertEqual(hashlib.sha256(result).hexdigest(), patcher.TESTED_SHA256)
        self.assertEqual(hashlib.sha256(self.stock).hexdigest(), original_hash)

    def test_corrupted_source_rejected(self):
        corrupted = bytearray(self.stock)
        corrupted[0x40000] ^= 1
        with self.assertRaises(patcher.PatchError):
            patcher.make_patched_rom(corrupted, SPEC)

    def test_reconstruction_repeatable(self):
        self.assertEqual(patcher.make_patched_rom(self.stock, SPEC),
                         patcher.make_patched_rom(self.stock, SPEC))

    def test_altered_patch_cannot_emit_untested_rom(self):
        altered = copy.deepcopy(SPEC)
        altered['instructions'][0]['after'] = '0xe0040006'
        with self.assertRaises(patcher.PatchError):
            patcher.make_patched_rom(self.stock, altered)


if __name__ == '__main__':
    unittest.main()
