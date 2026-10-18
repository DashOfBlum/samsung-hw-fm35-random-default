# Validation record

The stock and patched hashes are recorded in the main README and patch manifest.
Tests below used the exact patched hash published there. Counts describe bounded
test cases or interpreted instructions, not independent soundbar trials.

## Hardware report — October 18, 2026

The owner confirmed HW-FM35/ZA, M 1004.1, and D 1006.0. The owner reported that an
official same-version USB reinstall worked, then that the modified firmware
worked. The first song stays the same; subsequent songs play randomly. The
owner explicitly accepted that behavior.

Only one soundbar has been reported. Separate standby/AC-cycle, source re-entry,
manual-repeat, and recovery-from-failed-boot results have not been recorded.

## Offline checks

* Nine stock and nine candidate sections decoded by the firmware's own native
  decompressor under a self-written ESS instruction interpreter. All outputs
  matched expected bytes: **18 runs, 137,867,746 interpreted instructions**.
* The unmodified filename validator recognized the original same-version backend
  filename and rejected unrelated model/extension examples.
* The native updater checksum helper returned zero. Deliberately changing one
  bit produced a nonzero checksum.
* **2,259 bounded cases** covered both initializers, preserved initialization
  writes/registers, the repeat getter, and stock manual-mode mapping.
* **54 selector scenarios** compared startup Random with stock manually selected
  Random, with four sequential-play controls. Track tables, filesystem metadata,
  and RNG return values were synthetic. This verifies selection control flow,
  not the real RNG distribution or USB filesystem.
* The actual status builder produced `46 03 31`. Its payload was supplied to the
  original controller running in the independent GNU RL78 simulator. The parser
  accepted Random/Play, then four Repeat presses queued Off/File/All/Random:
  `19 00`, `19 01`, `19 02`, `19 03`.
* A native decompressor access audit covered **14,433,959 instructions** and
  **1,212,890 writes**. The checksum-balancing word was not read. Writes stayed
  in the output and loader temporary-memory regions.
* The distributed archive and ROM were compared before and after that round;
  neither firmware artifact changed.

The ESS interpreter is project-authored, not an independently validated CPU
emulator. The native routines are real firmware code, but peripherals, full boot,
UART delivery, and flash erase/write operations were not emulated. Only the
controller checks used the independently maintained GNU CPU simulator.

## Public patcher checks

Run guard tests without Samsung firmware:

```sh
python3 -m unittest discover -s tests -v
```

To also test exact reconstruction locally, set `FM35_STOCK_ROM` to the unchanged
official ROM's path before running the same command. This adds exact-output,
input-preservation, corruption-rejection, and repeatability checks. The GitHub
workflow runs the guard tests; it does not distribute or fetch Samsung firmware.

Generating a ROM is not a flash operation. A valid hash and checksum do not
guarantee device compatibility or recovery from an interrupted update.
