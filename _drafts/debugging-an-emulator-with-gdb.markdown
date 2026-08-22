---
layout: post
title: "Debugging a PlayStation with GDB" # working title, not final
description: What I learned about the GDB remote protocol while adding a debug stub to my PlayStation emulator, and why the same trick doesn't work for the SNES.
tags: [emulator, gdb, mips, playstation, snes, debugger]
---

## Draft notes — remove before publishing

**Where this came from.** While writing the PlayStation emulator I wanted
a real debugger instead of printf tracing, and found out I didn't have to
write one: GDB will talk to anything that speaks its remote protocol, and
the R3000A is MIPS, which GDB already knows. The interesting part is
comparing that to the SNES, where the same stub gets you almost nothing.

**Continues** the CPU pipelines post — same two machines, same
"I expected these to be similar and they weren't" shape.

**TODO before writing.**
- Actually implement the stub (or check what I already have) and capture a
  real packet trace to replace the invented examples below.
- Real register dump and `x/10i $pc` output from the emulator, not
  handwritten output.
- Check whether GDB needs `set architecture mips` explicitly or picks it
  up from the target description.
- Confirm how the emulator should report the stop reason for a breakpoint
  landing in a branch delay slot — this is the part I'm least sure about.

---

## What a debugger actually needs from you

A debug stub doesn't need to understand assembly. It answers questions:

- read registers
- write registers
- read memory
- write memory
- continue execution
- single-step
- report why execution stopped
- insert/remove breakpoints

That's the whole contract. Disassembly, symbols, source lines, expression
evaluation, backtraces — all of that lives on the GDB side.

```text
                ┌───────────────┐
                │     GDB       │
                │               │
                │ registers     │
                │ memory        │
                │ symbols       │
                │ disassembler  │
                └───────┬───────┘
                        │ GDB Remote Serial Protocol
                        │
             ┌──────────▼──────────┐
             │   GDB stub /        │
             │   debug server      │
             └──────────┬──────────┘
                        │
                ┌───────▼───────┐
                │   CPU / VM    │
                └───────────────┘
```

## The protocol is smaller than you'd expect

The GDB Remote Serial Protocol (RSP) is text packets over a socket.

Ask for all registers:

```text
g
```

The stub replies with the register values in hex.

Read `0x10` bytes at `0x80012340`:

```text
m80012340,10
```

Reply:

```text
8b45fc488945f8...
```

Plus `c` (continue), `s` (step), `Z`/`z` (set/clear breakpoint), and a
stop-reply packet saying why execution halted. GDB does the rest.

## What happens when a breakpoint hits

The emulator stops and reports its state. Say:

```text
PC = 0x80012340
SP = 0x801FF000
...
```

The important register is the program counter. GDB now knows where the CPU
is, asks for the bytes at that address, and runs them through its own
architecture-specific disassembler:

```text
          PC from target
               │
               ▼
        0x80012340
               │
               ▼
       read instruction bytes
               │
               ▼
          8b 45 fc
               │
               ▼
       architecture decoder
               │
               ▼
   mov eax,[rbp-0x4]
```

## Where does GDB get the program from?

Two separate sources, for different purposes.

**The local executable** gives symbols. Start GDB with a file:

```bash
gdb myprogram.elf
(gdb) target remote localhost:1234
```

and it reads symbol names, function boundaries, source file and line
information, debug info, sections, and the machine code from the ELF. That
is what turns `0x80012340` into `main()` or `game.cpp:142`.

**The emulator** gives live state: registers, memory, execution state.

```text
             GDB
              │
       ┌──────┴───────┐
       │              │
       ▼              ▼
  local ELF       emulator
       │              │
       │              ├── registers
       │              ├── memory
       │              └── execution state
       │
       ├── symbols
       ├── debug info
       └── executable sections
```

Why ask the emulator for memory if the ELF already has the code? Because
the emulator's memory may not match the file — code that modified RAM,
overlays, generated code. For a live target, target memory is the
authoritative state, so `x/10i $pc` goes and asks.

The nice consequence for an emulator: you never send a memory dump. GDB
requests exactly the bytes it needs.

```text
GDB                         Emulator

"give me registers"  ────►
                     ◄──── register values

"read 16 bytes at PC" ───►
                     ◄──── 16 bytes

"continue" ──────────────►
                     ◄──── stopped at PC=...
```

## You don't even need a file

GDB can attach with no executable at all:

```bash
gdb
```

```gdb
(gdb) target remote localhost:1234
(gdb) set architecture mips
(gdb) info registers
(gdb) x/10i $pc
(gdb) break *0x80010000
(gdb) stepi
(gdb) continue
```

What you lose without an ELF is names — no `main()`, no source lines, no
symbols. What still works is everything mechanical: registers, memory,
breakpoints, stepping, and disassembly, as long as GDB knows the
architecture.

The emulator can describe its registers to GDB with a target description:

```xml
<target>
  <architecture>mips</architecture>

  <feature name="org.gnu.gdb.mips.cpu">
    <!-- TODO: real R3000A register list -->
  </feature>
</target>
```

## The PlayStation case: it just works

The PS1's CPU is a MIPS R3000A, and GDB has had mature MIPS support for
decades. So there is no new architecture to teach it.

```text
                 GDB
                  │
          built-in MIPS support
                  │
         GDB Remote Protocol
                  │
                  ▼
          PS1 emulator GDB stub
                  │
        ┌─────────┴─────────┐
        │                   │
     R3000A CPU          PS1 memory
        │                   │
   registers/PC         RAM/ROM/etc.
```

If the emulator reports `PC = 0x80012340` and memory there holds:

```text
8C 82 00 10
24 42 00 01
AC 82 00 10
```

GDB disassembles it as MIPS with no help:

```asm
80012340: lw    v0,16(a0)
80012344: addiu v0,v0,1
80012348: sw    v0,16(a0)
```

And since the stub exposes the PS1 address space, the BIOS is inspectable
too:

```text
80000000 ─────────── RAM
A0000000 ─────────── uncached RAM
BFC00000 ─────────── BIOS
```

```gdb
(gdb) x/20i 0xbfc00000
(gdb) break *0x80010000
(gdb) continue
```

What the stub must handle:

| Capability | Purpose |
|---|---|
| Read registers | GDB knows CPU state |
| Write registers | Debugger can modify CPU state |
| Read memory | `x/i`, `x/x`, etc. |
| Write memory | Modify RAM |
| Continue | Resume emulation |
| Single step | Execute one instruction |
| Breakpoints | Stop at an address |
| Stop reason | Tell GDB why execution stopped |

### Branch delay slots

MIPS has branch delay slots:

```asm
beq   t0,zero,target
addiu t1,t1,1
```

The `addiu` executes before the branch takes effect. GDB's MIPS support
already knows this, so there's nothing to teach it — but the *emulator's*
single-step has to report the resulting CPU state correctly, and this ties
straight back to the pipeline post.

## The SNES case: the same stub gets you nothing

Stock GDB has no 65C816 backend. You can still attach, read registers, set
breakpoints, and step — but ask it to disassemble and you get:

```text
(gdb) x/10i $pc

   0x800123:     .byte 0xa9
   0x800124:     .byte 0x42
   ...
```

instead of:

```asm
800123:    LDA #$42
800125:    STA $1234
```

And the reason it's not just a missing table is the interesting part:
**on the 65816, instruction length depends on processor state.**

```text
A9 12 34
```

is either:

```asm
LDA #$12
```

or:

```asm
LDA #$3412
```

depending on the accumulator width — the M and X flags in the P register.
A decoder that only sees bytes cannot know where the next instruction
starts. Dedicated SNES disassemblers (`65816disasm`, Asar) track those
flags as they go.

So a 65816 stub has to expose `P` along with the rest — `A`, `X`, `Y`,
`S`, `D`, `DB`, `PB`, `PC`, memory, breakpoints, step, continue — and
something on the GDB side has to use it.

### Two ways to extend GDB

**A Python disassembler.** Modern GDB exposes a Python API for registering
one. It receives an address, reads the instruction bytes and the processor
status from the target, decodes per 65816 rules, and returns the
instruction text.

```text
GDB
 │
 │ x/10i $pc
 ▼
Python 65816 disassembler
 │
 │ read memory
 ▼
GDB target
 │
 ▼
SNES emulator
```

Good enough to prototype without maintaining a GDB fork.

**A real architecture.** The proper route is `gdbarch` — a `65816-tdep.c`
describing registers, register sizes, PC, SP, breakpoint and single-step
behaviour, disassembly, and frame unwinding, with the disassembler
ideally living in binutils' opcodes library so every tool shares it. Then:

```gdb
(gdb) set architecture 65816
```

## The comparison

SNES:

```text
GDB
 │
 │ doesn't understand 65C816
 ▼
Need custom architecture/disassembler
 │
 ▼
GDB stub
 │
 ▼
Emulator
```

PS1:

```text
GDB
 │
 │ already understands MIPS
 ▼
GDB stub
 │
 ▼
Emulator
```

Same protocol, same amount of work in the emulator, completely different
payoff — and the thing that decides it is a design detail of a CPU from
1990.
