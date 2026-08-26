---
layout: post
title: "Taking Final Fantasy VII apart: overlays, matching, and the PlayStation toolchain" # working title, not final
description: Research notes on how FF7's PSX binary is structured, how a matching decompilation actually works, and the failure modes nobody warns you about.
tags: [playstation, mips, decompilation, reverse-engineering, c, ff7]
---

## Draft notes — remove before publishing

Raw research material, not a write-up. Everything here was verified
directly against the `ff7-decomp` repo and the built binaries during one
working session, so the numbers and addresses are real rather than
remembered. Inferences are marked as such.

Companion to [From the SNES to the PlayStation]({% post_url 2026-08-22-from-the-snes-to-the-playstation-understanding-cpu-pipelines %})
— that one is about emulating the hardware, this one is about taking
apart software that ran on it.

There are probably three separate posts in here:

1. The architecture tour (overlays, memory map, entry points)
2. The matching war stories — most likely to be interesting to people
   who don't care about FF7 specifically
3. The toolchain failure modes — short, punchy, useful to anyone doing
   this on a modern Linux box

---

## 1. What a matching decompilation is

The goal is not "C code that behaves like the game". The goal is C code
that, compiled with the original 1997 toolchain and flags, produces
**byte-identical** output to the disc. The build ends with `sha1sum -c`
over every binary. If one byte differs, the build fails. There is no
partial credit, and "it looks right" is not a state the project has.

That constraint is what makes it interesting. You are not writing code,
you are solving for the code that a specific old compiler must have been
fed to emit exactly these instructions.

## 2. The architecture: one executable, three overlay slots

The PlayStation has 2 MB of main RAM, `0x80000000`–`0x80200000`. FF7
tiles it in four tiers.

`main` is the resident executable — the file `SCUS_941.63` on the disc,
397,312 bytes, loaded at `0x80010000` and never unloaded. Everything
else is an overlay: a headerless raw code image the engine reads into a
fixed address on demand.

Grouping the fourteen build targets by load address:

| Load address | Overlays |
|---|---|
| `0x800A0000` | `field`, `battle`, `world`, `ending`, `brom`, `dschange` |
| `0x801B0000` | `batini`, `barrier`, `lv5deth`, + ~287 more spell effects |
| `0x801D0000` | `bginmenu`, `cnfgmenu`, `savemenu`, `itemmenu` |

Anything sharing an address is mutually exclusive. Different rows can be
resident simultaneously. So the big slot holds whichever *mode* you're
in — a field screen, the world map, a battle — while menus live in their
own slot and can open on top of a running mode.

The `0x801B0000` slot is the interesting one: `batini` (battle
initialisation, inferred from the name and link order) shares it with
every magic effect. Once battle setup is done, its memory becomes the
load area for spell animations.

**Good detail for the post:** the symbol wiring independently confirms
this. `main` exports its symbols to `sym_export.us.txt` (1,081 of them)
and every overlay links against it. `battle` additionally exports
`sym_export_battle.us.txt`, and the build feeds that *only* to `batini`
and the magic overlays. Which is exactly the dependency you'd predict if,
mid-spell, three things are in memory at once: main, battle, and the
effect overlay.

### Entry points

`main` is a conventional PS-X EXE. The header records:

```
Initial PC   0x800110C0
.text start  0x80010000
.text size   0x00060800
Initial $sp  0x801FFFF0
```

`0x800110C0` resolves to `__SN_ENTRY_POINT` — the SN Systems / Psy-Q C
runtime stub, i.e. the crt0 that sets up the stack and calls into the
game. It's the only one of the fourteen with a header at all.

Overlays have no header, so how does the engine find their entry point?
Only one overlay in the project has a named entry: `barrier`, where
`MAGIC_Barrier` sits at offset `0` and is a two-argument forwarder into
the real setup function.

There's a nice technique here worth writing up. For `lv5deth`, you can
find the entry by counting **which functions nothing else in the overlay
references**:

```
func_801B0000: refs=1     (registered via BattleEffectRegister)
func_801B0054: refs=0     <-- nothing internal reaches it
func_801B0074: refs=1     (registered as an effect callback)
func_801B01BC: refs=1     (registered as an effect callback)
func_801B0310: refs=1     (registered as an effect callback)
func_801B0414: refs=1     (passed to MagicAnimationRegister)
func_801B0508: refs=1     (called by func_801B0054)
```

Six of seven have a visible internal caller. The seventh is the only
address the engine can be calling from outside — and it turns out to be
a two-argument forwarder, structurally identical to `MAGIC_Barrier`.
Running the same analysis on `barrier` as a control correctly flags
`MAGIC_Barrier` and nothing else, which is what makes the method
trustworthy.

Caveat to keep honest in the write-up: this proves it's the only
*candidate*, not that the engine calls it. Confirming needs the
battle-side overlay loader, which isn't decompiled yet. Also, barrier's
entry is at offset `0` and this one is at `0x54`, so if there's a
fixed-offset convention, one of them breaks it.

## 3. The MAGIC overlays: 289 tiny programs

The disc's `MAGIC/` directory has 318 files, 46 MB: 289 `.BIN` overlays
plus 29 `.LZS`. One binary per spell or enemy attack. Sizes run from
**448 bytes to 315 KB**.

Names are a mix of English and romaji — recognisable spell tiers
alongside development names that survived localisation. Nice colour for
the post: the internal naming is a window into the original dev process.

**They're animation only.** This surprised me and is probably the most
blog-worthy single finding. Nothing in a spell overlay touches HP, MP,
or status. Every function either builds GPU primitives, sets colours, or
advances an animation frame counter. What the overlay *does* have is a
timing hook back into the engine — on one specific frame it calls a
battle function that pushes an event carrying the target index onto a
queue:

```c
if (D_80062D98 == 0) {
    if (effect->AnimationFrame == 35) {
        func_800D5774(effect->unkE);   // queue the gameplay event
    }
    effect->AnimationFrame++;
}
```

So the division of labour is: the battle overlay owns damage formulas,
targeting and the event queue; the effect overlay owns what you see and
hear, plus *when* the engine should act. The spell says "the skull has
landed, now do the thing."

Consequence worth stating: the remaining 287 overlays are low-risk to
decompile. They can't regress combat behaviour, and they don't link
against each other.

## 4. The toolchain

The compile pipeline is a shell pipeline, which matters later:

```
mipsel-linux-gnu-cpp        # preprocess
  | bin/str                 # convert _S("FOO") into the game's string encoding
  | iconv -t Shift-JIS      # yes, really
  | bin/cc1-psx-26          # the original 1997 GCC 2.6.3 cc1
  | maspsx.py               # emulate ASPSX quirks
  | mipsel-linux-gnu-as     # modern GNU as
```

Two things stand out. The original `cc1` binaries are used directly —
this is real GCC 2.6.3 and 2.7.2, not a modern compiler in compatibility
mode. And `maspsx` exists to massage GCC's assembly output so modern GNU
`as` produces the same object the original PSYQ assembler would have,
with a `--aspsx-version` flag to select which era's quirks to emulate.

Per-file compiler selection is done with a magic comment on line 1:

```c
//! PSYQ=3.3 CC1=2.6.3
```

Different translation units in the same game were built with different
compiler versions, and matching requires reproducing that per file.
Flags are `-O2 -G0 -g -gcoff`, with a couple of files deviating.

### splat and the config

`splat` slices the binary into asm and C stubs full of `INCLUDE_ASM`
macros; you replace them one function at a time. The manifest is a YAML
file per version, with an entry per binary:

```yaml
  - name: lv5deth
    disk_path: disks/us/MAGIC/LV5DETH.BIN   # the thing you must match
    sha1: 860f9495...                       # checked at the end of every build
    vram_start: 0x801B0000
    segments:
      - [0, c, lv5deth]                     # code -> src/magic/lv5deth.c
      - [0x5e0, data, lv5deth]              # data -> standalone .s
```

Subtle but important: segment kind `data` (bare) emits a standalone
assembly file, while `.data` (dot-prefixed, bound to a C file) migrates
the data *into* the C source as arrays you can document. That one
character is the difference between `barrier.c` having its model data
inline as readable, commented C, and `lv5deth`'s data living in a
41,541-line, 2.1 MB `.s` file.

Symbol names come from plain text files:

```
D_801C0E44 = 0x801C0E44; // size:0xC
```

That `size:0xC` looks like a comment but is a directive — it tells splat
those 12 bytes are one symbol rather than several, which is what lets
you model them as a struct.

### The diff loop

`asm-differ` compares the target against your build, function by
function, and gives a **score**. Zero means byte-identical. You edit C,
rebuild, watch the number move. It's oddly addictive and makes a good
narrative spine for the post — see the war stories below, where a single
function goes 140 → 125 → 200 → 0.

Nice touch in this project's setup: the "expected" side is a snapshot
copied from the last *successful* build. Since a build only succeeds
when the checksums match, and an undecompiled function is still the
original assembly, you're always diffing your new C against the real
thing. A failing build never poisons the baseline.

## 5. Matching war stories

This is the section I'd actually want to read. Four of them, all from
one afternoon on one small file.

### Chained assignment and the register base

Three consecutive bytes had to be set to the same value. The obvious C
didn't match; the original clearly reached the first byte through a
*register base* while addressing the other two absolutely.

The fix is a chained assignment, but the direction matters and it's
counter-intuitive:

```c
D_801C0E44.color.r = D_801C0E44.color.g = D_801C0E44.color.b = color;
```

Chained assignment evaluates right to left, so the **rightmost** target
is stored first and the **leftmost** gets the register base. Getting
this backwards scored 140. Reversing it: 125. Still one instruction off.

### The type of the destination

That last instruction was a stray register move — the `s32 → u8`
conversion the chain performs, materialised into a second register. The
fix was making the branches write into a `u8` directly rather than
computing an `s32` and converting at the end. Adding a `u8` temporary at
the end does *not* work; the conversion has to not exist. Score 0.

### Two identical-looking workarounds, two different causes

The file had two `do { ... } while (0)` blocks, both with comments
saying they stopped a load being scheduled above some stores. They
looked like the same problem. They weren't.

The first was really an *addressing* problem, and the chained assignment
above fixed it — the ordering came along for free.

The second was genuinely a *scheduling barrier*. Chained assignment made
it worse (160), because the original addressed everything absolutely
with no register base. Removing the barrier let the compiler hoist a
load ten instructions earlier. `volatile` was worse still (750).

What actually fixed it was consistency: routing **every** store through
one typed pointer instead of mixing pointer access with absolute address
casts. That removed the `do`/`while` *and* a `goto` in the same move —
but only when both changes were made together. Doing half of it scored
545, worse than either.

**The lesson, and probably the thesis of the post:** you cannot reason
your way to these. Superficially identical symptoms had unrelated
causes, and my confident explanation of the second one was wrong. The
loop is: form a hypothesis, test it, read the actual diff. Three of my
four hypotheses that afternoon were wrong, and the diff said so in
about twenty seconds each time.

### The 64-bit index

Best "what on earth" moment. The previous author had needed a
`long long` index variable to defeat constant folding and force an array
base into a register, with a three-line comment apologising for it. The
chained assignment replaced the whole thing. Worth showing before/after.

## 6. Failure modes nobody warns you about

Short, self-contained, and the most immediately useful section for
anyone starting out.

### The silent pipeline failure

Best story of the session. The build "succeeded" for every compile, then
the link produced hundreds of undefined references. The objects were
**776 bytes with an empty symbol table** — every single one.

Cause: an uninitialised git submodule meant `maspsx.py` didn't exist.
Python printed "can't open file" to stderr and nothing to stdout. `as`
cheerfully assembled *empty input* into a valid empty object and exited
0. Because a shell pipeline reports only the **last** command's status,
ninja recorded every compile as a success.

`set -o pipefail` would have turned this into an immediate, obvious
error instead of a wall of link failures with no apparent cause. General
lesson about pipelines in build systems.

The misleading clue: the undefined symbols were mostly local `.L` jump
table labels, which sent me chasing an assembler theory for a while.
Which leads to…

### GNU as silently drops `.L` symbols

Verified experimentally, and worth including because it's genuinely
surprising:

```asm
.global .L800115D4
.L800115D4: nop
.global normal
normal: nop
```

Assemble that and `nm` shows only `normal`. The `.L`-prefixed symbol is
dropped from the symbol table **despite the explicit `.global`**, and
`--keep-locals` doesn't bring it back. Same behaviour on binutils 2.42
and 2.45. It was a red herring for my actual bug, but it's a real
property worth knowing.

### The toolchain version trap

Ubuntu 24.04 ships binutils 2.42, whose `mipsel-linux-gnu-ld` produces
output that doesn't byte-match the game. The project's CI works around
it by pulling binutils from a *newer* Ubuntu release. If you're doing
matching decompilation, your linker version is part of the build inputs,
the same way the compiler is.

### Your `python3` may not be the Python you think

The venv had been created from whatever `python3` resolved to first on
`PATH` — which was a PyPy 3.10 installed by `uv`. The build then died on
a nested-quote f-string, which is PEP 701 and needs CPython 3.12+. The
error looked like broken source code. It was a broken interpreter
choice.

General principle: create venvs with an explicit interpreter, never a
bare `python3`.

## 7. Naming, evidence, and working with other people

Softer material, might be its own short post or might get cut.

When you decompile, you invent names. The interesting question is which
names are *evidence-based* and which are guesses wearing a confident
face.

A worked example. Three bytes at consecutive addresses, zeroed together.
Are they a colour? Following the references, a function in the battle
overlay loads exactly those three bytes into the argument registers and
calls `SetFarColor` — the GTE far-colour function. That's proof, not a
guess. And a fourth byte immediately after gets a *different* value,
which fits the PSX SDK's `CVECTOR` layout of `r, g, b, cd`. So the
right move isn't to invent names at all; it's to use the SDK type that
already exists.

Contrast with names that arrive from outside. Some names in this project
came from source material for the PC version, and you can spot them by
**style break**: a codebase that's uniformly CamelCase suddenly containing
`light_1_rdx` and `lv5deth_tim`. Nobody invents those. Lowercase
underscores in a CamelCase codebase is a fingerprint of transcription
rather than inference.

And a caution I got wrong in the other direction: a name can be
internally inconsistent in a way that gives it away — a struct field
called `field_C` sitting at offset `0x8` is a tool's auto-name carried
over from somewhere else, not something derived from this struct.

## Open questions / TODO before writing

- Find the battle-side overlay loader to confirm the entry-point theory.
  It's the missing piece for section 2.
- Check whether the `0xC000` zero-filled buffers could move to `.bss`.
  They're in the file so they can't just vanish, but this overlay builds
  with bss emitted rather than NOLOAD, so it might work and would delete
  ~24,500 lines of assembly. Untested.
- Would the PC version help? Provisional answer: as a *naming* oracle
  yes, as a *code* oracle no — it's x86 and the whole rendering layer was
  rewritten, so there's nothing to diff. Contrast with Symphony of the
  Night, where PSX and PSP are both MIPS and functions can be diffed
  directly. That contrast might be worth a paragraph.
- Decide how much FF7-specific detail to keep. The matching stories and
  the failure modes stand alone; the architecture tour probably needs
  the game as a hook.
