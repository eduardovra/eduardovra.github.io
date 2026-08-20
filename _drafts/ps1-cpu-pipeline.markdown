---
layout: post
title: "From the SNES to the PlayStation: Understanding CPU pipelines"
#date: 2026-08-19 00:00:00 -0300
description: The SNES CPU runs one instruction at a time. The PlayStation's runs five at once, and it refuses to hide that from you.
#img: r3000a-pipeline.png
tags: [emulator, mips, cpp, playstation, snes, cpu]
---

I came to PlayStation emulation from the SNES expecting the jump to be about scale: faster CPU, more memory, a 3D chip instead of a tile engine. Same shape of problem, more of it.

That's not what happened. The PlayStation's CPU is pipelined — five instructions in flight at once — and unlike anything I'd emulated before, it doesn't hide that from the program running on it. Get it wrong and the BIOS doesn't boot.

TL;DR [here][repository] is the emulator, if you'd rather read code than prose.

### Where I was coming from: the 65816

The SNES CPU is a Ricoh 5A22, built around a [WDC 65816][65816] core. A 16-bit descendant of the 6502, it runs the way you'd naively draw a CPU on a whiteboard: fetch, decode, execute, move on. Then the next one.

One piece of vocabulary first, since the whole post turns on it. The **program counter**, `pc`, is a register holding the address of the next instruction to execute. Executing an instruction advances it past that instruction's bytes; a jump or a branch sets it somewhere else entirely.

Here's a stretch of SNES code in memory, with `pc` sitting at the start of it. The accumulator is in 8-bit mode here — widen it to 16 and `LDA #$42` takes an extra byte and an extra cycle:

{% include diagrams/snes-memory-bytes.svg %}

Three instructions, and together they actually do something: put `$42` in the accumulator — `A`, the 65816's main working register — add one to it, and store the result at address `$2000`. `A` ends up holding `$43`, and so does memory at `$2000`.

Their lengths differ. `LDA #$42` takes two bytes, the opcode `A9` and the constant. `INC A` takes a single byte, `1A`, since it needs no operand at all. `STA $2000` takes three: the opcode `8D` and then the address, low byte first, which is why it sits in memory as `8D 00 20`.

And when `INC A` reads the accumulator, it finds the `$42` the previous instruction just put there. Of course it does. What else would it find? Hold on to that question.

No markers separate the instructions — the first byte tells you the length. Which makes the interpreter the loop everybody writes first: a switch on the opcode, each case returning a cycle count.

```c
u8 opcode = read(pc++);

switch (opcode) {
case 0xA9:                  // LDA #imm - load a constant
    a = read(pc++);
    set_nz(a);
    return 2;

case 0x1A:                  // INC A - add one to the accumulator
    a++;
    set_nz(a);
    return 2;

case 0x8D:                  // STA abs - store A at a 16-bit address
    addr = read16(pc);
    pc += 2;
    write(addr, a);
    return 4;
}
```

The important thing isn't the code, it's the shape of it. Every case is a closed box: by the time it hits that `return`, the machine is completely consistent — nothing half-finished, no value in flight. Which means you can write these opcodes one at a time, in any order, and the two hundredth one can't break the first.

### Why pipeline at all

At the hardware level, executing an instruction isn't one job, it's several, and each uses a different part of the chip. Do them strictly one at a time and most of your silicon idles. So a pipeline does what a car factory does: it doesn't wait for one car to be finished before starting the next. Five instructions are in flight at any moment, each one in a different stage. The [R3000A][r3000a] in the PlayStation has five:

```
IF   fetch the instruction from memory
RD   decode it and read its register operands
ALU  do the arithmetic
MEM  read or write data memory
WB   write the result back to the register file
```

Here's what that looks like with real instructions. I picked five that don't depend on each other, which turns out to matter:

{% include diagrams/r3000a-pipeline.svg %}

Any single instruction still takes five cycles, but from cycle 5 onward one *finishes* every cycle — a 5x throughput win for basically no extra silicon, and why this CPU gets described as roughly one instruction per cycle at 33.87 MHz.

Which sounds like a pure win. Here's where it falls apart.

### How it breaks: hazards

All of which holds up only while each instruction is independent of the ones around it. Instructions usually aren't.

Look at the shaded IF cells again — the instruction fetches. That diagonal is `pc`, moving on one instruction every cycle, whatever the instructions themselves are up to. Two cases go wrong.

**A branch.** Suppose the first instruction were a branch. Its whole job is to decide what `pc` should be next — but the second instruction is fetched in cycle 2, while the branch is still in its second stage. `pc` runs one instruction ahead of the instruction that gets to change it.

```
beq   $t0, $zero, target   # decides where to go next...
addiu $a0, $a0, 1          # ...but this was already fetched
```

The consequence: `addiu` runs, whichever way the branch goes.

**A load.** The first instruction *is* a load. Its value arrives from memory in MEM, cycle 4 — but the instruction behind it reads its registers in RD, cycle 3, one cycle earlier. The data physically isn't there yet.

```
lw    $t0, 0($a0)     # $t0 arrives in cycle 4
addu  $t1, $t0, $t2   # but reads $t0 in cycle 3
```

The consequence: `addu` gets whatever `$t0` held before the load.

These are called *hazards*, and most CPUs fix them in hardware: interlocks that stall the pipeline, forwarding paths that shortcut a result backwards. Modern processors go much further — branch predictors that guess where a branch will go and start work on the answer, out-of-order execution, speculation they can throw away if the guess was wrong. All of it exists so that software never has to know.

The R3000A largely doesn't bother. It exposes both hazards and expects software to work around them.

### What it means if you're writing assembly

#### The branch delay slot

The instruction immediately after a branch **always executes**, taken or not. It was already fetched, and the hardware doesn't throw it away. That position is called the [*delay slot*][delay-slot]: the instruction you read *after* a jump runs *before* the jump lands.

Consider the snippet below — real BIOS code, a function returning to its caller:

```
80054190  lw      $t7, 0x0($sp)
80054194  jr      $ra              # return to the caller
80054198  addiu   $sp, $sp, 0x8    # ...and this ran too
```

`jr $ra` is an unconditional jump, so there's no question of whether it was taken. It jumped: `$ra` held `800541EC`, and that is where execution continued. But `$sp` moved as well, from `801FFD50` to `801FFD58`. The instruction sitting *after* the return ran anyway, and it did real work — it popped the stack frame on the way out.

The nice part is that this isn't purely a tax, it's a free instruction slot. Here's real BIOS code from my emulator's debugger — a byte-copy loop, `$a1` the source, `$a0` the destination, `$a2` the count:

```
BFC02B68  lbu     $t6, 0x0($a1)      # load a byte from the source
BFC02B6C  addiu   $a2, $a2, -0x1     # count--
BFC02B70  addiu   $a1, $a1, 0x1      # source++
BFC02B74  addiu   $a0, $a0, 0x1      # dest++
BFC02B78  bgtz    $a2, 0xBFC02B68    # more to do? go round again
BFC02B7C  sb      $t6, -0x1($a0)     # <- delay slot: store the byte
```

The store is in the delay slot, so it runs on every iteration — including the last one, where the branch isn't taken and the byte still needs storing. The offset is `-0x1($a0)` because `$a0` was already incremented. Whoever wrote this bent the loop around the delay slot rather than wasting it.

#### The load delay slot

The value from a load isn't in its target register for the next instruction. It lands one instruction later, and the pipeline shows you why:

{% include diagrams/load-delay-hazard.svg %}

So the rule: never use a loaded register in the instruction right after the load.

This one is nastier than the branch slot, because nothing looks wrong. The disassembly reads naturally. You just get a stale register, and a game that renders garbage twenty minutes later.

Look back at the BIOS loop and you'll see this rule obeyed too: `$t6` is loaded at `BFC02B68` and not read until `BFC02B7C`. Those three `addiu`s aren't only advancing the pointers and the counter, they're covering the load's delay.

### Does the compiler solve this when you write C?

This was the question I was most curious about, so I actually checked. Short answer: yes, completely, and you never find out it happened.

Here's about the smallest C function that trips the load delay:

```c
int add_loaded(int *p, int k)
{
    int a = *p;
    return a + k;
}
```

Compiled for MIPS I (`clang -target mipsel-unknown-elf -march=mips1 -O1`), the body comes out as:

```
lw      $1, 0($4)
nop                       # <- load delay slot, nothing to fill it with
addu    $2, $1, $5
...
jr      $ra               # <- jump to $ra: the return
addiu   $sp, $sp, 8       # <- branch delay slot, filled with real work
```

Both hazards, handled, in a four-line function. Nothing useful to put after the load, so the compiler inserted a `nop`. For the branch delay slot it *did* have something — the stack pointer adjustment — so the return costs nothing extra.

Give it more to work with and it does better:

```c
int sum3(int *p)
{
    return p[0] + p[1] + p[2];
}
```

becomes:

```
lw      $1, 0($4)
lw      $2, 4($4)         # <- fills the first load's delay slot
nop                       # <- nothing available for the second's
addu    $1, $2, $1
lw      $2, 8($4)
nop
addu    $2, $1, $2
```

The second load slots neatly into the first load's shadow, because it doesn't depend on it — the scheduler doing what a careful assembly programmer would do by hand.

The compiler also wraps every function body in these:

```
.set noreorder
...
.set reorder
```

[`.set noreorder`][gas-mips] tells the assembler *don't touch my instruction order, I've handled the delay slots myself*. It exists because the assembler will do this job too, dropping in `nop`s to keep hand-written assembly correct.

So the abstraction never really disappeared. It moved. The hardware declined to hide the pipeline, and the toolchain hides it instead — and you can switch that off when you're writing a boot ROM and you want the raw machine.

### Show me the code

So what does any of this mean for an emulator?

The good news, and the thing that took me longest to believe: **you do not have to simulate five pipeline stages.** Only the two places where the overlap is *observable*. Everything else is invisible, and you keep the one-instruction-at-a-time interpreter loop you'd write for a 65816 — about ten lines of extra state.

#### Two program counters

The branch delay slot means you can't have a single `pc`. You need both what's executing now and what's queued behind it:

```cpp
u32 pc = 0;          // instruction about to execute
u32 next_pc = 0;     // the one after it; a branch rewrites this
u32 current_pc = 0;  // the one executing now, kept for exceptions
```

The whole trick is the ordering in `step()`. Advance both counters *before* executing the instruction:

```cpp
pc = next_pc;
next_pc += 4;

execute(instr);
```

Now a branch writes to `next_pc`, and `pc` — which already points at the delay slot instruction — is left alone. The delay slot runs next, then the branch target. The behaviour falls out of the data structure instead of a special case, and branching becomes just:

```cpp
void Cpu::branch(u32 offset)
{
    next_pc = pc + (offset << 2);
    branching = true;
}
```

#### Two register files

The load delay slot means a write can't be visible to the instruction immediately after the one that issued it. So instructions read from one array and write to another:

```cpp
// regs holds the values instructions read; writes go to out_regs
// and become visible after the step.
std::array<u32, 32> regs{};
std::array<u32, 32> out_regs{};

// The load issued by the previous instruction, waiting out its
// delay slot. Register 0 means "none" - a load into $zero is a
// no-op anyway, so it needs no separate flag.
u32 load_reg = 0;
u32 load_value = 0;
```

And `step()` gets a shape that mirrors the hardware:

```cpp
u32 Cpu::step()
{
    current_pc = pc;

    // the load issued by the previous instruction lands now
    set_reg(load_reg, load_value);
    load_reg = 0;
    load_value = 0;

    pc = next_pc;
    next_pc += 4;

    execute(instr);

    // writes made by this instruction become readable from here on
    regs = out_regs;

    return CYCLES_PER_INSTRUCTION + bus.stall_cycles;
}
```

Read that in order and it's exactly the rule: the previous instruction's load lands before this one runs, and this one's own writes don't become visible until it's over. Two arrays and a copy, and every load is correct — including the ones you haven't written yet. The alternative is handling the delay in each load opcode individually, which works right up until you add the twentieth one at midnight.

### Wrapping-up

That was the surprise for me. I didn't expect a CPU to make that kind of trade-off, handing a hardware problem over to whoever writes the instructions. It's one of the most interesting things I've found writing this emulator so far.

The emulator is [here][repository], and the CPU is one file. [psx-spx][psx-spx] is the hardware reference I kept open the whole time, and the [ps1-tests][ps1-tests] suite caught most of my mistakes.

[repository]: https://github.com/eduardovra/wobble-psx
[r3000a]: https://en.wikipedia.org/wiki/R3000
[65816]: https://en.wikipedia.org/wiki/WDC_65C816
[psx-spx]: https://psx-spx.consoledev.net/cpuspecifications/
[delay-slot]: https://en.wikipedia.org/wiki/Delay_slot
[gas-mips]: https://sourceware.org/binutils/docs/as/MIPS_002dDependent.html
[ps1-tests]: https://github.com/JaCzekanski/ps1-tests
