# Technical notes

This patch changes the playback processor's initialization. It does not simulate
remote-control presses or change Repeat labels without changing playback state.

## Instruction changes

These are addresses in the decoded backend memory map, not ROM file offsets.

| Address | Original word | Patched word | Reason |
| --- | --- | --- | --- |
| `0x877b4` | `e0040002` | `e0040007` | Generic media default: internal mode 2 to 7 |
| `0x98418` | `e0060002` | `e0060007` | USB/browser default: internal mode 2 to 7 |
| `0x98440` | `e0044e0c` | `e0040003` | Prepare external mode 3 in r2 |
| `0x98454` | `96447198` | `964a7198` | Preserve the pointer store using r5 |
| `0x9845c` | `96406ee0` | `96446ee0` | Initialize reported mode from r2, now 3 |

The pointer `0x4e0c` is already in r5 at `0x98448`. Reusing it permits r2 to hold
the reported default without adding an instruction. The next callee overwrites
r2 at `0x17a2c8` before reading it. The callee after the generic media initializer
likewise overwrites r2 at `0x1833f0` before reading it.

## Mode mapping

Controller command `0x19` stores its parameter at `[r25+0x6ee0]`. Stock setter
`0x98bf4` indexes a table at `[r25-0x40c0]` and writes the resulting internal
playback mode at `[r25+0x6ee8]`:

| Mode | External value | Internal value |
| --- | --- | --- |
| Off | 0 | 2 |
| File | 1 | 1 |
| All | 2 | 3 |
| Random | 3 | 7 |

The getter at `0x98d88` returns the external mode. Playback status encodes it
in the upper nibble. Internal mode 7 takes the Random branch of the stock track
selector at `0x978c4..0x978c8`, calling the RNG helper through `0x97964`.

The initial request described the factory behavior as Repeat All. The inspected
initializers actually use external 0/internal 2. Local initialization alone does
not explain every startup/display transition. The recorded hardware result is
a fixed first song followed by random playback; it is the practical outcome
confirmed for this patch.

## Container and checksum

The 2 MiB image has 83 loader macros and nine raw-DEFLATE sections. Macro 42 loads
578,892 decoded bytes at `0x3ba7c`, from ROM section `0x3a5d4`. Its compressed
stream starts eight bytes later. The next section starts at `0x83a3c`.

The stock compressed stream is 300,121 bytes; the patched stream is 299,793
bytes with reference zlib 1.2.13. The original eight-byte section prefix is kept.
A CRC32/length trailer follows the new stream. All other decoded sections remain
byte-for-byte identical.

The updater XOR helper at `0x166424` computes the 32-bit file checksum. Its caller
at `0x1667f8` rejects a nonzero value. The new stream's trailing allocation has
enough unused space to balance that checksum at ROM offset `0x838f8`; the native
decompressor did not read that word during the audited run. The complete file
XOR becomes zero without modifying the updater or its validation branches.

No model/version spoofing, signature bypass, or controller patch is involved.
The exact resulting SHA-256 is enforced by the patcher.

## References

The original format investigation used the
[DVD Patcher source](https://sourceforge.net/projects/dvd-patcher/) and the
[MAME MIPS-X disassembler](https://github.com/mamedev/mame/blob/master/src/devices/cpu/mipsx/mipsxdasm.cpp).
The CPU used here has ESS extensions; call encoding was inferred from loader
bases, function prologues/returns, and jump-table consistency. Those tools are
not required to run this public patcher and their sources are not bundled here.
