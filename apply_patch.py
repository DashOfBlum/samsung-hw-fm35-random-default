#!/usr/bin/env python3
"""Recreate the tested Random-default firmware from an exact stock ROM.

This tool writes computer files only. It never flashes a device.
"""
import argparse
from functools import reduce
import hashlib
import json
from operator import xor
from pathlib import Path
import struct
import sys
import zlib

STOCK_SHA256 = '16b67ede5d4419fe3c560b1880f86299686cb8f0f87dacf11a249573fa7c5737'
TESTED_SHA256 = 'eb5ced460a7d9288528f0fb6cd0fb9d4cc75a1f7347d94cfa3610ae87ea28d72'
FILENAME = 'HMS-F550WWB-1006.0.ROM'


class PatchError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PatchError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def xor32(data):
    require(len(data) % 4 == 0, 'ROM is not word aligned.')
    return reduce(xor, (row[0] for row in struct.iter_unpack('>I', data)), 0)


def unpack_sections(rom):
    require(len(rom) == 2097152, 'Expected a 2,097,152-byte ROM.')
    table = int.from_bytes(rom[4:8], 'big') - 0x0ce00000
    count = int.from_bytes(rom[8:12], 'big')
    require(table == 0x16b16c and count == 83, 'Unexpected loader table.')
    macros = [struct.unpack_from('>4I', rom, table + i * 16) for i in range(count)]
    sections = {}
    for i, (kind, address, _, _) in enumerate(macros):
        if kind != 8:
            continue
        require(i + 1 < count and macros[i+1][0] == 9, 'Unexpected section macro.')
        pos = address - 0x0ce00000
        require(0 <= pos < len(rom) - 8, 'Section address outside ROM.')
        decoder = zlib.decompressobj(-15)
        payload = decoder.decompress(rom[pos+8:])
        require(decoder.eof and len(decoder.unused_data) >= 4, 'Incomplete compressed section.')
        require(zlib.crc32(payload) == struct.unpack_from('<I', decoder.unused_data)[0],
                'Section CRC32 mismatch.')
        sections[i] = payload
    require(len(sections) == 9, 'Expected nine compressed sections.')
    return sections


def make_patched_rom(stock, spec):
    require(sha256(stock) == STOCK_SHA256, 'Stock SHA-256 does not match the supported Samsung ROM. Nothing was written.')
    require(spec['source_sha256'] == STOCK_SHA256 and spec['target_sha256'] == TESTED_SHA256,
            'Unexpected patch manifest hashes.')
    require(xor32(stock) == 0, 'Stock ROM checksum mismatch.')
    sections = unpack_sections(stock)
    section = spec['segment']
    require(section == {'macro':42, 'destination':'0x3ba7c', 'rom_offset':'0x3a5d4',
                        'next_rom_offset':'0x83a3c', 'decoded_bytes':578892},
            'Unexpected patch segment.')
    payload = bytearray(sections[42])
    require(len(payload) == section['decoded_bytes'], 'Unexpected decoded section size.')
    for change in spec['instructions']:
        offset = int(change['address'], 16) - 0x3ba7c
        require(0 <= offset <= len(payload)-4 and offset % 4 == 0, 'Patch instruction outside section.')
        require(struct.unpack_from('>I', payload, offset)[0] == int(change['before'], 16),
                'Original instruction differs from expected bytes.')
        struct.pack_into('>I', payload, offset, int(change['after'], 16))
    require(sum(a != b for a,b in zip(payload, sections[42])) == 6,
            'Expected six changed decoded bytes.')
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    stream = compressor.compress(payload) + compressor.flush()
    encoded = stream + struct.pack('<II', zlib.crc32(payload), len(payload))
    start, limit = 0x3a5dc, 0x83a3c
    balance = (start + len(encoded) + 3) & ~3
    require(balance + 4 <= limit, 'Rebuilt compressed section does not fit.')
    result = bytearray(stock)
    result[start:start+len(encoded)] = encoded
    previous = struct.unpack_from('>I', result, balance)[0]
    struct.pack_into('>I', result, balance, previous ^ xor32(result))
    require(xor32(result) == 0, 'Rebuilt ROM checksum mismatch.')
    require(result[:start] == stock[:start] and result[limit:] == stock[limit:],
            'Bytes outside the section allocation changed.')
    decoded = unpack_sections(result)
    for index, original in sections.items():
        require(decoded[index] == (payload if index == 42 else original),
                'Rebuilt decoded contents do not match the intended patch.')
    require(sha256(result) == TESTED_SHA256,
            f'Output differs from the tested ROM (runtime zlib {zlib.ZLIB_RUNTIME_VERSION}; '
            'reference zlib 1.2.13). Nothing was written. Use a Python installation '
            'with zlib 1.2.13; do not disable this hash check.')
    return bytes(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stock_rom', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('patched'))
    parser.add_argument('--verify-only', action='store_true', help='Build and validate in memory without writing an output ROM.')
    args = parser.parse_args(argv)
    try:
        spec = json.loads(Path(__file__).with_name('patch.json').read_text())
        output = args.output_dir / FILENAME
        require(output.resolve() != args.stock_rom.resolve(), 'Refusing to overwrite the stock input.')
        require(args.verify_only or not output.exists(), 'Output already exists; choose a new output directory.')
        patched = make_patched_rom(args.stock_rom.read_bytes(), spec)
        if not args.verify_only:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            with output.open('xb') as handle:
                handle.write(patched)
            print(f'Created: {output}')
        print(f'SHA-256: {sha256(patched)}')
        print('Verified: exact tested ROM, nine section CRCs, six decoded bytes, whole-ROM XOR.')
        print('Experimental firmware. Read README.md before any USB update.')
        return 0
    except (OSError, ValueError, KeyError, struct.error, zlib.error) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
