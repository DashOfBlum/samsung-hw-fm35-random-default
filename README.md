# Samsung HW-FM35 Random startup default

An experimental firmware patch for the **Samsung HW-FM35/ZA** soundbar that makes
USB playback start in Repeat Random mode.

> **Use at your own risk.** This unofficial patch is provided as is, without any warranty. I accept no responsibility for hardware damage, an unusable device, data loss, or other harm resulting from its use. You are responsible for deciding whether to install it and for any consequences.

**Reported working on one HW-FM35/ZA on October 18, 2026:** the first song stays
the same, then following songs play randomly. The owner accepts that behavior.
The first song is not randomized by this patch. Separate standby/AC-cycle and
manual-mode hardware results have not been recorded.

This is an unofficial project, unaffiliated with Samsung. A failed update or boot
can leave the soundbar unusable and require opening it for recovery. The ordinary
stock USB reinstall worked on the tested unit, but recovery from an unbootable
modified backend has **not** been demonstrated.

## Supported firmware

| Item | Tested value |
| --- | --- |
| Model label | HW-FM35/ZA |
| Controller display | M 1004.1 |
| Backend display | D 1006.0 |
| Backend filename | `HMS-F550WWB-1006.0.ROM` |
| Stock ROM size | 2,097,152 bytes |

Other models and versions are not validated. Do not infer compatibility from the
shared F550 filename. The patcher accepts only the exact stock SHA-256 below.

## Download and generate the firmware

Get the [latest patch release](https://github.com/DashOfBlum/samsung-hw-fm35-random-default/releases/latest)
or clone this repository. It contains the patch instructions and Python patcher;
Samsung's full firmware is not included. Obtain the original backend from
[Samsung's HW-FM35/ZA support page](https://www.samsung.com/ca/support/model/HW-FM35/ZA/)
or its [official 1006.0 backend ZIP](https://org.downloadcenter.samsung.com/content/FM/201308/20130807175755928/HMS-F550WWB-1006.0.zip).
Extract Samsung's ZIP first.

Use Python 3.9 or later; there are no third-party Python dependencies:

```sh
python3 apply_patch.py /path/to/HMS-F550WWB-1006.0.ROM --output-dir patched
```

On Windows, use `py -3` in place of `python3` if needed. The result is
`patched/HMS-F550WWB-1006.0.ROM`. The patcher refuses to overwrite the original
or an existing output. It checks all nine section CRCs, the whole-ROM checksum,
and the exact hash of the hardware-tested result before saving anything.

The reference build used zlib 1.2.13. If your Python's compression produces
different bytes, the patcher stops without writing a ROM. Use Python with that
zlib version; do not remove the final hash check. To validate without saving:

```sh
python3 apply_patch.py /path/to/HMS-F550WWB-1006.0.ROM --verify-only
```

## Verify hashes

Stock input SHA-256:

```text
16b67ede5d4419fe3c560b1880f86299686cb8f0f87dacf11a249573fa7c5737
```

Tested patched output SHA-256:

```text
eb5ced460a7d9288528f0fb6cd0fb9d4cc75a1f7347d94cfa3610ae87ea28d72
```

Check the copied USB file with `sha256sum` on Linux, `shasum -a 256` on macOS,
or `Get-FileHash -Algorithm SHA256` in Windows PowerShell.

## Install over USB

Keep an unchanged copy of the official stock ROM. For another soundbar, first
confirm the exact model/version and that an official same-version backend USB
reinstall actually completes. This checks the normal update procedure; it does
not establish recovery from an unbootable modified image.

1. Use a USB drive known to work with the soundbar. Put only the generated
   `HMS-F550WWB-1006.0.ROM` in the drive's root. Do not rename it, copy the ZIP
   or `patched` folder, or include other ROM/`.ssp` firmware files.
2. Verify the copied file's hash against the patched hash above and safely eject
   the drive from your computer.
3. Power on the soundbar and select USB mode. Insert the update drive. Insertion
   can start updating automatically.
4. Keep reliable power and leave the USB drive connected until the update
   completes and the soundbar switches off automatically. **Do not interrupt
   an active update.**
5. After completion and automatic power-off, remove the update drive. In standby,
   hold Stop for about five seconds and look for `INI`, following Samsung's guide.
6. Use a music-only USB drive to test playback. Expect the same first song,
   followed by random playback. Check manual Repeat choices and both standby
   and AC power cycles on your unit.

The displayed firmware version remains D 1006.0. It does not distinguish the
patched image. This changes the backend only; leave the controller stock.

[Samsung's USB upgrade guide](https://org.downloadcenter.samsung.com/content/FM/201308/20130807195910364/USB_Upgrade_Guide_English.pdf)
describes the update and initialization procedure. `INI` resets settings; it
does not restore stock firmware. Returning to stock through USB requires a
soundbar that still boots and accepts an update.

## What changes

Five existing instructions change, totaling **six decoded bytes**, in one
compressed backend section. Both internal default assignments become Random;
the reported mode also becomes Random. One existing pointer initialization
uses another register that already holds the same value. No extra startup
command, code stub, RAM allocation, or stack space is added.

Recompression plus a checksum-balancing word changes **298,542 file bytes**.
The balancing word sits after the new compressed stream and complete trailer,
inside the original section allocation. The updater's XOR checksum is restored
to zero. No validation check is disabled.

See [technical notes](docs/technical-notes.md), [validation](docs/validation.md),
and the machine-readable [patch instructions](patch.json).

## License

The authored patcher and documentation are provided under the [MIT license](LICENSE).
Samsung firmware remains separate and is not covered by that license.
