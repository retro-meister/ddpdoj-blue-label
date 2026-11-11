"""Build Blue Label and standard BPS patches from your ROMs.

python3 -I build.py --vasm /path/to/vasmm68k_mot --aseprite /path/to/aseprite
                   [--date YYYY-MM-DD]
Provide your original ddpdojblk.zip or ddpdojblk.7z beside this script, or use
--rom PATH for a ROM folder, ZIP or 7z elsewhere. Output: build/ddpdojblk.zip.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
import zlib

ROOT = Path(__file__).resolve().parent

BASE = 0x100000
CHIP = "ddb10_10_8_434f.u45"
HOOK = re.compile(
    r"^\s+HOOK\s+(before|after),\s*\$([0-9a-f]+),\s*(\d+),\s*(\w+)\s*(?:;.*)?$", re.I
)


# Assembler setup

VASM_REVISION = "a13e7e728a3dd5a9ba468bf479119e0bc23e70fd"
VASM_SHA256 = "ac4439a853a884762f65f6dbba317d72beb7abdc243e6a4f5e02f99622c92ade"


def compile_vasm(source, output, compiler, windows):
    core = "vasm atom expr symtab symbol error parse reloc hugeint cond listing source supp dwarf osdep".split()
    files = [source / (name + ".c") for name in core]
    files += [source / "cpus/m68k/cpu.c", source / "syntax/mot/syntax.c"]
    files += sorted(source.glob("output_*.c"))
    includes = [source, source / "cpus/m68k", source / "syntax/mot"]
    msvc = Path(compiler).stem.lower() in ("cl", "clang-cl")
    if msvc:
        args = [compiler, "/nologo", "/O2", "/DOUTSREC"]
        args += ["/I" + str(path) for path in includes]
        args += [str(path) for path in files] + ["/Fe:" + str(output)]
    else:
        args = [compiler, "-O2", "-DOUTSREC"]
        if not windows:
            args.append("-DUNIX")
        args += ["-I" + str(path) for path in includes]
        args += [str(path) for path in files] + ["-lm", "-o", str(output)]
    result = subprocess.run(args, cwd=source, capture_output=True, text=True)
    log = output.parent / "compiler.log"
    log.write_text(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError(f"Could not compile vasm; see {log}")


def find_vasm(root, override=None):
    if override:
        return str(Path(override).resolve()) if Path(override).is_file() else override
    installed = shutil.which("vasmm68k_mot")
    if installed:
        return installed
    windows = os.name == "nt"
    host = platform.system().lower() + "-" + platform.machine().lower()
    cache = root / "build/toolchain" / f"vasm-{VASM_REVISION[:12]}-{host}"
    executable = cache / ("vasmm68k_mot.exe" if windows else "vasmm68k_mot")
    if executable.is_file():
        return str(executable)
    compiler = os.environ.get("CC") or next(
        (
            path
            for name in (("cl", "clang", "gcc") if windows else ("cc", "clang", "gcc"))
            if (path := shutil.which(name))
        ),
        None,
    )
    if not compiler:
        raise ValueError(
            "No C compiler found to build vasm. Install a C compiler (Xcode Command Line Tools, GCC/Clang, or Visual Studio C++ developer tools), or supply --vasm PATH."
        )
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / "source.tar.gz"
    print("vasm not found; downloading and building the pinned assembler…", flush=True)
    if (
        not archive.exists()
        or hashlib.sha256(archive.read_bytes()).hexdigest() != VASM_SHA256
    ):
        url = f"https://codeload.github.com/mbitsnbites/vasm-mirror/tar.gz/{VASM_REVISION}"
        with urllib.request.urlopen(url, timeout=60) as response:
            archive.write_bytes(response.read())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != VASM_SHA256:
        raise ValueError("vasm source checksum mismatch")
    source = cache / "source"
    source.mkdir(exist_ok=True)
    with tarfile.open(archive) as bundle:
        for member in bundle:
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] != "vasm-mirror-" + VASM_REVISION or ".." in parts:
                raise ValueError("Unexpected filename in vasm source archive")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("Unexpected link in vasm source archive")
            target = source.joinpath(*parts[1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.extractfile(member) as data:
                target.write_bytes(data.read())
    temporary = cache / ("vasm-building.exe" if windows else "vasm-building")
    compile_vasm(source, temporary, compiler, windows)
    temporary.replace(executable)
    print(f"Assembler ready: {executable}")
    return str(executable)


# Program ROM encryption

PGM_KEY = bytes.fromhex(
    "74 e8 a8 64 26 44 a6 9a a5 69 a2 d3 6d ba ff f3"
    "eb 6e e3 70 72 58 27 d9 e4 9f 50 a2 dd ce 6e f6"
    "44 72 0c 7e 4d 41 77 2d 00 ad 1a 5f 6b c0 1d 4e"
    "4c 72 62 3c 32 28 43 f8 9d 52 05 7e d1 ee 82 61"
    "3b 3f 77 f3 8f 7e 3f f1 df 8f 68 43 d7 68 df 19"
    "87 ff 74 e5 3f 43 8e 80 0f 7e db 32 e8 d1 66 8f"
    "be e2 33 94 c8 32 39 fa f0 43 de 84 18 d0 6d d5"
    "74 98 f8 64 cf 84 c6 ea 55 32 e2 38 dd ea fd 6c"
    "eb 6e e3 70 ae 38 c7 d9 54 84 10 c1 fd 1e 6e 6d"
    "37 e0 03 9e 06 36 68 5b e3 f6 7f 0b 56 79 e0 a8"
    "98 77 c7 2b a5 79 ff 2f ca 15 71 7e 02 bf 87 b7"
    "7a 8e e6 64 32 62 2a ca 23 72 87 b5 0c 02 4b ee"
    "44 72 9c 7e 5d c1 a7 1d 30 38 da c9 5b d0 11 f9"
    "b1 72 6c 04 31 c9 50 60 6f c1 f2 ae 00 f4 5d 66"
    "43 0e 7a c3 76 ae 3c c2 b7 c9 52 f4 74 51 af 12"
    "19 c6 75 e8 6c 54 7e 63 dd ae 07 5a b7 00 b5 5e"
)


def pgm_pad(i):
    """XOR pad for word index i (all arithmetic on 16-bit values)."""
    x = 0
    if (i & 0x040480) != 0x000080:
        x ^= 0x0001
    if (i & 0x084008) == 0x084008:
        x ^= 0x0002
    if (i & 0x000030) == 0x000010 and (i & 0x180000) != 0x080000:
        x ^= 0x0004
    if (i & 0x000042) != 0x000042:
        x ^= 0x0008
    if (i & 0x008100) == 0x008000:
        x ^= 0x0010
    if (i & 0x022004) != 0x000004:
        x ^= 0x0020
    if (i & 0x011800) != 0x010000:
        x ^= 0x0040
    if (i & 0x004820) == 0x004820:
        x ^= 0x0080
    return x ^ (PGM_KEY[i & 0xFF] << 8)


def decrypt_rom(raw):
    """Chip bytes -> CPU-order program bytes."""
    out = bytearray(len(raw) & ~1)
    for i in range(len(out) // 2):
        x = (raw[2 * i] | (raw[2 * i + 1] << 8)) ^ pgm_pad(i)
        out[2 * i] = x >> 8
        out[2 * i + 1] = x & 0xFF
    return bytes(out)


ROM_SIZE = 0x200000


def encrypt_rom(image, size=ROM_SIZE):
    """CPU-order program bytes -> chip bytes."""
    if len(image) % 2 or len(image) > size:
        raise ValueError(f"image must be an even number of bytes up to {size:#x}")
    out = bytearray(size)
    for i in range(len(image) // 2):
        x = ((image[2 * i] << 8) | image[2 * i + 1]) ^ pgm_pad(i)
        out[2 * i] = x & 0xFF
        out[2 * i + 1] = x >> 8
    return bytes(out)


# Aseprite export and indexed pixels


def indexed_png(path):
    """Read the non-interlaced, 8-bit indexed PNGs emitted by Aseprite."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    at, compressed, transparency = 8, bytearray(), b""
    width = height = None
    while at < len(data):
        length = int.from_bytes(data[at : at + 4], "big")
        kind, payload = data[at + 4 : at + 8], data[at + 8 : at + 8 + length]
        crc = data[at + 8 + length : at + 12 + length]
        if len(crc) != 4 or zlib.crc32(kind + payload) != int.from_bytes(crc, "big"):
            raise ValueError(f"{path}: PNG checksum mismatch")
        at += length + 12
        if kind == b"IHDR":
            width, height, depth, mode, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", payload)
            )
            if (depth, mode, compression, filtering, interlace) != (8, 3, 0, 0, 0):
                raise ValueError(f"{path}: artwork must stay in Indexed mode")
        elif kind == b"IDAT":
            compressed += payload
        elif kind == b"tRNS":
            transparency = payload
        elif kind == b"IEND":
            break
    if not width or not height or width * height > 4 * 1024 * 1024:
        raise ValueError(f"{path}: invalid artwork dimensions")
    if (
        len(transparency) != 32
        or transparency[:31] != bytes([255]) * 31
        or transparency[31] != 0
    ):
        raise ValueError(f"{path}: preserve opaque slots 0–30 and transparent slot 31")
    raw = zlib.decompress(compressed)
    if len(raw) != (width + 1) * height:
        raise ValueError(f"{path}: unexpected PNG data length")
    rows, previous = [], [0] * width
    for y in range(height):
        start = y * (width + 1)
        kind, row = raw[start], list(raw[start + 1 : start + 1 + width])
        if kind > 4:
            raise ValueError(f"{path}: invalid PNG filter")
        for x in range(width):
            left, above, corner = (
                row[x - 1] if x else 0,
                previous[x],
                previous[x - 1] if x else 0,
            )
            if kind == 1:
                predictor = left
            elif kind == 2:
                predictor = above
            elif kind == 3:
                predictor = (left + above) // 2
            elif kind == 4:
                estimate = left + above - corner
                distances = [abs(estimate - v) for v in (left, above, corner)]
                predictor = (left, above, corner)[distances.index(min(distances))]
            else:
                predictor = 0
            row[x] = (row[x] + predictor) & 255
            if row[x] > 31:
                raise ValueError(f"{path}: PGM artwork supports only 32 colour slots")
        rows.append(row)
        previous = row
    return rows


def export_aseprite(source, directory, executable):
    directory.mkdir(parents=True, exist_ok=True)
    png, metadata = directory / "sheet.png", directory / "sheet.json"
    subprocess.run(
        [
            str(executable),
            "--batch",
            str(source),
            "--list-slices",
            "--format",
            "json-array",
            "--data",
            str(metadata),
            "--sheet",
            str(png),
        ],
        check=True,
    )
    return indexed_png(png), json.loads(metadata.read_text())


def slice_image(rows, metadata, name):
    slices = [
        item for item in metadata["meta"].get("slices", []) if item["name"] == name
    ]
    if len(slices) != 1 or len(slices[0]["keys"]) != 1:
        raise ValueError(f"Missing or ambiguous Aseprite slice: {name}")
    bounds = slices[0]["keys"][0]["bounds"]
    x, y, width, height = (bounds[key] for key in ("x", "y", "w", "h"))
    if (
        x < 0
        or y < 0
        or width < 1
        or height < 1
        or y + height > len(rows)
        or x + width > len(rows[0])
    ):
        raise ValueError(f"Aseprite slice outside artwork: {name}")
    return [row[x : x + width] for row in rows[y : y + height]]


# PGM sprite encoding


def encode_sprites(images, mask_at, colour_at):
    masks, colours, records = bytearray(), bytearray(), []
    for image in images:
        height, width = len(image), len(image[0])
        if any(len(row) != width for row in image):
            raise ValueError("Sprite rows must have equal widths")
        native_width = (height + 15) // 16 * 16
        native_height = width
        if native_width > 1008 or native_height > 511:
            raise ValueError("Sprite exceeds the PGM draw-record dimensions")
        # Portrait artwork rotated clockwise into native landscape storage.
        pixels = [
            image[height - 1 - x][y] if x < height else 31
            for y in range(native_height)
            for x in range(native_width)
        ]
        offset = mask_at + len(masks)
        start = (0x800000 + colour_at + len(colours)) // 2 * 4
        masks += start.to_bytes(4, "little")
        pens = []
        for i in range(0, len(pixels), 8):
            mask = 0
            for bit, pen in enumerate(pixels[i : i + 8]):
                if not 0 <= pen <= 31:
                    raise ValueError("PGM colour-slot index outside 0–31")
                if pen == 31:
                    mask |= 1 << bit
                else:
                    pens.append(pen)
            masks.append(mask)
        while len(pens) % 3:
            pens.append(0)
        for i in range(0, len(pens), 3):
            colours += (pens[i] | pens[i + 1] << 5 | pens[i + 2] << 10).to_bytes(
                2, "little"
            )
        records.append((offset // 2, (native_width // 16) << 9 | native_height))
    return bytes(masks), bytes(colours), records


# HUD artwork

MASK_ROM = "cave_b04401w064.u1"
COLOUR_ROM = "cave_a04402w064.u8"
HUD_MASK_AT = 0x7F0000
HUD_COLOUR_AT = 0x7E0000
ASSETS = ROOT / "assets/hud"

# Existing palette slots; 29 is the shadow and 31 is transparency.
COLOURS = {
    "red": (16, 17, 18, 19, 20, 21, 22),
    "green": (10, 10, 9, 9, 9, 9, 9),
    "gold": (19,) * 7,
    "flash": (23, 23, 24, 24, 25, 25, 26),
    "fade": (24, 24, 25, 25, 26, 26, 27),
}


def build_hud(romset, program, workdir, executable):
    workdir = Path(workdir)
    artwork = {}
    for source in ("brk", "digits", "times"):
        artwork[source] = export_aseprite(
            ASSETS / (source + ".aseprite"), workdir / source, executable
        )

    if any(len(metadata["frames"]) != 1 for _, metadata in artwork.values()):
        raise ValueError("Each HUD Aseprite file must contain one frame")

    def piece(source, name, width):
        image = slice_image(*artwork[source], name)
        if len(image) != 16 or any(len(row) != width for row in image):
            raise ValueError(
                f"{name}: preserve its {width}×16 slice; resizing also requires a HUD layout change"
            )
        return image

    frame = piece("brk", "brk", 40)
    times = piece("times", "times", 4)
    digits = [piece("digits", f"digit-{digit}", 6) for digit in range(10)]
    if any(
        pen not in (*range(16, 23), 29, 31)
        for image in digits
        for row in image
        for pen in row
    ):
        raise ValueError(
            "Digits must use red slots 16–22, shadow 29 and transparency 31"
        )

    def number(digit, column, colour):
        # The native thousands-zero slot is blank; keep their draw records exact.
        if digit == 0 and column == 0:
            return [[31] * 6 for _ in range(16)]
        return [
            [COLOURS[colour][pen - 16] if 16 <= pen <= 22 else pen for pen in row]
            for row in digits[digit]
        ]

    images = [frame]
    for colour in ("red", "green"):
        for column in range(4):
            images.extend(number(digit, column, colour) for digit in range(10))
    images.append(times)
    images.extend(number(digit, 3, "gold") for digit in range(10))
    for colour in ("flash", "fade"):
        for column in range(4):
            images.extend(number(digit, column, colour) for digit in range(10))
    masks, colours, records = encode_sprites(images, HUD_MASK_AT, HUD_COLOUR_AT)
    for name, at, data in (
        (MASK_ROM, HUD_MASK_AT, masks),
        (COLOUR_ROM, HUD_COLOUR_AT, colours),
    ):
        original = romset[name]
        if at + len(data) > len(original) or any(original[at:]):
            raise ValueError(name + ": expected unused zero padding for the HUD")
        romset[name] = original[:at] + data + original[at + len(data) :]
    # Engine records contain a mask address in word units and hardware size.
    lines = ["; generated from assets/hud/*.aseprite", "blue_hud_pictures:"]
    for i, (address, size) in enumerate(records):
        if i == 81:
            lines.append("blue_hud_times:")
        if i == 82:
            lines.append("blue_hud_life_numbers:")
        if i == 92:
            lines.append("blue_hud_flash_numbers:")
        if i == 132:
            lines.append("blue_hud_fade_numbers:")
        lines.append("\tdc.l\t$%x\n\tdc.w\t$%x" % (address, size))
    lines.append("blue_hud_ship_icons:")
    for at in (0x2881D2, 0x2881D6, 0x2881DA, 0x2881DE):
        address = int.from_bytes(program[at - 0x100000 : at - 0x100000 + 4], "big")
        lines.append("\tdc.l\t$%x\n\tdc.w\t$208" % address)
    Path(workdir, "blue_hud_assets.inc").write_text("\n".join(lines) + "\n")
    return len(masks), len(colours)


# BPS patches


def bps_number(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if not value:
            out.append(byte | 0x80)
            return bytes(out)
        out.append(byte)
        value -= 1


def create_bps(before, after):
    """Create a fixed-size delta from the original and built ROM files."""
    if len(before) != len(after):
        raise ValueError("Blue Label never resizes a ROM")
    out = bytearray(
        b"BPS1" + bps_number(len(before)) + bps_number(len(after)) + bps_number(0)
    )
    at = 0
    while at < len(after):
        changed = before[at] != after[at]
        end = at + 1
        while end < len(after) and (before[end] != after[end]) == changed:
            end += 1
        out += bps_number(((end - at - 1) << 2) | int(changed))
        if changed:
            out += after[at:end]
        at = end
    source_crc, target_crc = zlib.crc32(before), zlib.crc32(after)
    out += struct.pack("<II", source_crc, target_crc)
    out += struct.pack("<I", zlib.crc32(out))
    return bytes(out), target_crc


def apply_bps(source, patch):
    """Validate and apply the BPS actions emitted by create_bps()."""
    if len(patch) < 19 or patch[:4] != b"BPS1":
        raise ValueError("Not a BPS patch")
    source_crc, target_crc, patch_crc = struct.unpack("<III", patch[-12:])
    if zlib.crc32(patch[:-4]) != patch_crc:
        raise ValueError("Patch checksum mismatch")
    at = 4

    def read_number():
        nonlocal at
        value, shift = 0, 1
        for _ in range(10):
            if at >= len(patch) - 12:
                break
            byte = patch[at]
            at += 1
            value += (byte & 0x7F) * shift
            if byte & 0x80:
                return value
            shift <<= 7
            value += shift
        raise ValueError("Invalid BPS number")

    source_size, target_size, metadata_size = (
        read_number(),
        read_number(),
        read_number(),
    )
    if len(source) != source_size or zlib.crc32(source) != source_crc:
        raise ValueError("Original ROM checksum or size mismatch")
    at += metadata_size
    out = bytearray()
    while len(out) < target_size:
        action = read_number()
        length, kind = (action >> 2) + 1, action & 3
        if len(out) + length > target_size:
            raise ValueError("BPS output exceeds declared size")
        if kind == 0:
            chunk = source[len(out) : len(out) + length]
        elif kind == 1:
            if at + length > len(patch) - 12:
                raise ValueError("Truncated BPS literal")
            chunk = patch[at : at + length]
            at += length
        else:
            raise ValueError("Unsupported BPS action in generated patch")
        if len(chunk) != length:
            raise ValueError("Truncated BPS source")
        out += chunk
    if at != len(patch) - 12 or zlib.crc32(out) != target_crc:
        raise ValueError("Patched ROM checksum mismatch")
    return bytes(out)


# Assembly, ROM input and build outputs


def hooks_and_patches(build_date):
    hooks, lines = [], []
    for n, line in enumerate((ROOT / "src/patches.asm").read_text().splitlines(), 1):
        if line.split(";", 1)[0].strip() == "BUILD_DATE":
            lines.append(f'\tdc.b\t"  {build_date:%Y.%m.%d}.BLUE VER BETA  "')
            continue
        match = HOOK.match(line)
        if not match:
            if line.lstrip().startswith("HOOK"):
                raise ValueError(f"patches.asm:{n}: invalid hook")
            lines.append(line)
            continue
        kind, address, length, routine = match.groups()
        site, length = int(address, 16), int(length)
        if length < 6 or length % 2:
            raise ValueError(f"patches.asm:{n}: hook length must be even and >= 6")
        index = len(hooks)
        hooks.append((kind, site, length, routine))
        lines += [f"\torg ${site:x}", f"\tjmp blue_hook_{index}"]
        if length > 6:
            lines.append(f"\tdcb.w {(length - 6) // 2},$4e71")
    return hooks, "\n".join(lines)


def stubs(hooks, program):
    lines = []
    for index, (kind, site, length, routine) in enumerate(hooks):
        start = site - BASE
        if start < 0 or start + length > len(program):
            raise ValueError(f"Hook outside the program ROM at ${site:x}")
        moved = program[start : start + length]
        words = ",".join(
            f"${int.from_bytes(moved[i:i + 2], 'big'):04x}" for i in range(0, length, 2)
        )
        lines.append(f"blue_hook_{index}:")
        if kind == "before":
            lines.append(f"\tjsr {routine}")
        lines.append(f"\tdc.w {words} ; displaced instructions at ${site:x}")
        if kind == "after":
            lines.append(f"\tjsr {routine}")
        lines.append(f"\tjmp ${site + length:x}")
    return "\n".join(lines)


def srecords(path):
    for line in path.read_text().splitlines():
        if line[:2] not in ("S1", "S2", "S3"):
            continue
        raw = bytes.fromhex(line[2:])
        size = {"S1": 2, "S2": 3, "S3": 4}[line[:2]]
        if raw[0] != len(raw) - 1 or sum(raw) & 255 != 255:
            raise ValueError("Invalid assembler S-record")
        yield int.from_bytes(raw[1 : 1 + size], "big"), raw[1 + size : -1]


def assemble(program, vasm, work, build_date):
    hooks, patches = hooks_and_patches(build_date)
    main = work / "assemble.asm"
    main.write_text(
        '\tinclude "game.inc"\n\torg BLUE_ROM\n\tinclude "main.asm"\n'
        f'\tinclude "{work / "blue_hud_assets.inc"}"\n'
        + stubs(hooks, program)
        + '\nblue_rom_end:\n\tifgt blue_rom_end-$300000\n\tfail "ROM overflow"\n\tendc\n'
        + '\tifgt BLUE_RAM_END-$81f000\n\tfail "RAM overflow"\n\tendc\n'
        + patches
        + "\n"
    )
    output = work / "blue.srec"
    subprocess.run(
        [
            vasm,
            "-quiet",
            "-m68000",
            "-no-opt",
            "-Fsrec",
            "-s28",
            "-I",
            str(ROOT / "src"),
            "-o",
            str(output),
            str(main),
        ],
        check=True,
    )
    result = bytearray(program)
    written = bytearray(len(program))
    for address, data in srecords(output):
        start, end = address - BASE, address - BASE + len(data)
        if start < 0 or end > len(result):
            raise ValueError(f"Assembly write outside the program ROM at ${address:x}")
        if any(written[start:end]):
            raise ValueError(f"Overlapping assembly writes at ${address:x}")
        result[start:end] = data
        written[start:end] = bytes([1]) * len(data)
    return bytes(result), len(hooks)


def read_set(path):
    """Read a ROM folder, ZIP or 7z, retaining all unchanged set files."""
    if path.is_dir():
        entries = [
            (p.name, p.read_bytes()) for p in sorted(path.rglob("*")) if p.is_file()
        ]
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            entries = [
                (Path(i.filename).name, archive.read(i))
                for i in archive.infolist()
                if not i.is_dir()
            ]
    else:
        with path.open("rb") as source:
            signature = source.read(6)
        if signature != b"7z\xbc\xaf\x27\x1c":
            raise ValueError(f"{path}: expected a ROM folder, ZIP or 7z")
        tool = shutil.which("7zz") or shutil.which("7z") or shutil.which("7za")
        if not tool:
            raise ValueError(
                "7z input requires 7-Zip (7zz, 7z or 7za on PATH); alternatively extract it first and use --rom FOLDER"
            )
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    tool,
                    "x",
                    "-y",
                    "-bso0",
                    "-bsp0",
                    f"-o{directory}",
                    str(path.resolve()),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                raise ValueError(
                    f"Could not extract {path}: {result.stderr.strip() or result.stdout.strip()}"
                )
            return read_set(Path(directory))
    result = {}
    for name, data in entries:
        if name in result:
            raise ValueError(f"Duplicate ROM filename: {name}")
        result[name] = data
    return result


def validate_roms(roms):
    expected = {
        CHIP: (0x200000, 0xD21561DB),
        MASK_ROM: (0x800000, 0x17731C9D),
        COLOUR_ROM: (0x800000, 0x752167B0),
    }
    for name, (size, crc) in expected.items():
        if name not in roms:
            raise ValueError(
                f"Missing {name}; provide the complete Black Label ROM set"
            )
        data = roms[name]
        if len(data) != size or zlib.crc32(data) != crc:
            raise ValueError(
                f"Original ROM mismatch: {name}; expected Black Label 2002.10.07"
            )


def write_rom_zip(roms, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        temporary = Path(directory) / "ddpdojblk.zip"
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(roms.items()):
                archive.writestr(name, data)
        temporary.replace(destination)


def build(before, vasm, build_date, out, aseprite):
    program = decrypt_rom(before[CHIP])
    after = dict(before)
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        build_hud(after, program, work, aseprite)
        after[CHIP] = encrypt_rom(assemble(program, vasm, work, build_date)[0])
    patches, files = {}, []
    out.mkdir(parents=True, exist_ok=True)
    for name in (CHIP, MASK_ROM, COLOUR_ROM):
        patch, target_crc = create_bps(before[name], after[name])
        patches[name] = patch
        filename = name + ".bps"
        (out / filename).write_bytes(patch)
        files.append(
            dict(
                file=name,
                patch=filename,
                source_crc32=f"{zlib.crc32(before[name]):08x}",
                target_crc32=f"{target_crc:08x}",
                size=len(before[name]),
            )
        )
    manifest = dict(
        name="DoDonPachi Dai-Ou-Jou Blue Label",
        build_date=build_date.isoformat(),
        version="beta",
        edition="original-art",
        files=files,
    )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(
        out / "ddpdoj-blue-label-patches.zip", "w", zipfile.ZIP_DEFLATED
    ) as archive:
        for path in sorted(out.iterdir()):
            if path.suffix == ".bps" or path.name == "manifest.json":
                info = zipfile.ZipInfo(
                    path.name,
                    (build_date.year, build_date.month, build_date.day, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
    # Verify the standard patches reproduce every built ROM before packaging it.
    for name, patch in patches.items():
        if apply_bps(before[name], patch) != after[name]:
            raise ValueError(f"Patch verification failed: {name}")
    return after


def find_aseprite():
    executable = os.environ.get("ASEPRITE") or shutil.which("aseprite")
    if executable:
        return executable
    candidates = []
    if sys.platform == "win32":
        for variable, fallback in (
            ("ProgramFiles", r"C:\Program Files"),
            ("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        ):
            directory = Path(os.environ.get(variable) or fallback)
            candidates += [
                directory / "Aseprite/aseprite.exe",
                directory / "Steam/steamapps/common/Aseprite/aseprite.exe",
            ]
    elif sys.platform == "darwin":
        candidates += [
            Path("/Applications/Aseprite.app/Contents/MacOS/aseprite"),
            Path.home() / "Library/Application Support/Steam/steamapps/common/Aseprite/Aseprite.app/Contents/MacOS/aseprite",
        ]
    return next((str(path) for path in candidates if path.is_file()), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vasm",
        default=os.environ.get("VASM"),
        help="Override the automatically located/built assembler",
    )
    parser.add_argument(
        "--aseprite",
        default=find_aseprite(),
    )
    parser.add_argument(
        "--date",
        type=datetime.date.fromisoformat,
        default=datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ).date(),
    )
    parser.add_argument("--output", type=Path, default=ROOT / "build/patches")
    parser.add_argument(
        "--rom",
        type=Path,
        help="Original ROM folder, ZIP or 7z; otherwise auto-detect ddpdojblk.zip or ddpdojblk.7z",
    )
    args = parser.parse_args()
    candidates = [ROOT / "ddpdojblk.zip", ROOT / "ddpdojblk.7z"]
    originals = [path for path in candidates if path.exists()]
    if not args.rom and len(originals) > 1:
        parser.error("Both ddpdojblk.zip and ddpdojblk.7z exist; select one with --rom")
    original = args.rom or (originals[0] if originals else None)
    if original is None:
        parser.error(
            "Place your original ddpdojblk.zip or ddpdojblk.7z in the repo root, or pass --rom PATH"
        )
    destination = ROOT / "build/ddpdojblk.zip"
    if original.resolve() == destination.resolve():
        parser.error("Original ROM input must differ from build/ddpdojblk.zip")
    roms = read_set(original)
    validate_roms(roms)
    if not args.aseprite:
        parser.error("Set ASEPRITE or pass --aseprite /path/to/aseprite")
    vasm = find_vasm(ROOT, args.vasm)
    patched = build(roms, vasm, args.date, args.output, args.aseprite)
    write_rom_zip(patched, destination)
    print(f"Blue Label ZIP created successfully: {destination}")
    print(f"Built 3 BPS patches: {args.output.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (
        ValueError,
        OSError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        sys.exit(str(error))
