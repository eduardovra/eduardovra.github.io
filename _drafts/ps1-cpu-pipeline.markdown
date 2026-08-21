---
layout: post
title: "From the SNES to the PlayStation: Understanding CPU pipelines"
#date: 2026-08-19 00:00:00 -0300
description: What I learned about CPU pipelines when moving from SNES to PlayStation emulation, and what it takes to emulate the R3000A correctly.
#img: r3000a-pipeline.png
tags: [emulator, mips, cpp, playstation, snes, cpu]
---

After spending some time writing a SNES emulator, I decided to move on to the PlayStation. I was expecting the jump to be mostly about scale: a faster CPU, more memory, and a 3D chip instead of a tile engine. The same shape of problem, just more of it.

That's not quite what I found. The PlayStation's CPU is pipelined, meaning it can have five instructions executing at the same time, and unlike anything I had emulated before, it doesn't hide that fact from the programs running on it. If the emulator doesn't get this behavior right, the BIOS won't even boot.

As always, you can choose to jump right into the [repository][repository] and see the code for yourself, or read this article first. It's up to you.

### The SNES CPU: the 65816

The SNES CPU is a Ricoh 5A22, built around a [WDC 65816][65816] core. It's a 16-bit descendant of the famous 6502, and it works the way you would naively draw a CPU on a whiteboard: fetch an instruction, decode it, execute it, and move on to the next one.

Before proceeding, it's important to cover one piece of vocabulary, since the whole post depends on it. The **program counter** (`pc`) is a register that holds the address of the next instruction to be executed. Executing an instruction advances it past that instruction's bytes, while a jump or a branch sets it to somewhere else entirely.

Consider the stretch of SNES code below, with `pc` sitting at the start of it. The accumulator is in 8-bit mode here (in 16-bit mode, `LDA #$42` would take an extra byte and an extra cycle):

{% include diagrams/snes-memory-bytes.svg %}

We have three instructions, and together they do something useful: put the value `$42` in the accumulator (`A`, the 65816's main working register), add one to it, and store the result at address `$2000`. In the end, `A` holds `$43`, and so does the memory at `$2000`.

Notice that the instructions have different lengths. `LDA #$42` takes two bytes: the opcode `A9` and the constant. `INC A` takes a single byte (`1A`), since it needs no operand at all. `STA $2000` takes three: the opcode `8D` followed by the address, low byte first, which is why it appears in memory as `8D 00 20`.

Also notice that when `INC A` reads the accumulator, it finds the `$42` that the previous instruction just put there. This seems too obvious to even mention, but keep it in mind, because we'll come back to it later.

There are no markers separating the instructions: the first byte tells you the length. That's why the first interpreter everybody writes is a loop with a switch on the opcode, where each case returns a cycle count:

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

The important thing here is not the code itself, but the shape of it. Every case is a closed box: by the time it hits the `return` statement, the machine is in a completely consistent state. Nothing is half-finished, and no value is in flight. This means you can write these opcodes one at a time, in any order, and the two hundredth one can't break the first.

### Why pipeline at all

At the hardware level, executing an instruction is not a single job, but several, and each of them uses a different part of the chip. If we do them strictly one at a time, most of the silicon stays idle. A pipeline works like a car factory assembly line: it doesn't wait for one car to be finished before starting the next. At any given moment, five instructions are in flight, each one in a different stage. The [R3000A][r3000a] CPU used in the PlayStation has five stages:

```
IF   fetch the instruction from memory
RD   decode it and read its register operands
ALU  do the arithmetic
MEM  read or write data memory
WB   write the result back to the register file
```

Here's what this looks like with real instructions. I picked five that don't depend on each other, and as we'll see soon, this detail matters:

{% include diagrams/r3000a-pipeline.svg %}

Any single instruction still takes five cycles to complete, but from cycle 5 onward, one instruction *finishes* every cycle. That's a 5x gain in throughput for almost no extra silicon, and it's the reason this CPU is usually described as executing roughly one instruction per cycle at 33.87 MHz.

This sounds like a pure win, right? Now let's see where it falls apart.

### Pipeline hazards

All of this only holds up while each instruction is independent of the ones around it. In practice, instructions usually aren't.

Take a look at the shaded IF cells in the diagram again (the instruction fetches). That diagonal is `pc` moving on to the next instruction every cycle, no matter what the instructions themselves are doing. There are two cases where this goes wrong.

**A branch.** Suppose the first instruction is a branch. Its whole job is to decide what `pc` should be next, but the second instruction is fetched in cycle 2, while the branch is still in its second stage. In other words, `pc` runs one instruction ahead of the instruction that is supposed to change it.

```
beq   $t0, $zero, target   # decides where to go next...
addiu $a0, $a0, 1          # ...but this was already fetched
```

The consequence: `addiu` runs no matter which way the branch goes.

**A load.** Now suppose the first instruction is a load. Its value arrives from memory in the MEM stage, at cycle 4. But the instruction behind it reads its registers in the RD stage, at cycle 3, one cycle earlier. The data simply isn't there yet.

```
lw    $t0, 0($a0)     # $t0 arrives in cycle 4
addu  $t1, $t0, $t2   # but reads $t0 in cycle 3
```

The consequence: `addu` gets whatever value `$t0` held before the load.

These situations are called *hazards*, and most CPUs fix them in hardware: interlocks that stall the pipeline, and forwarding paths that shortcut a result backwards. Modern processors go much further, with branch predictors that guess where a branch will go, out-of-order execution, and speculation that can be thrown away if the guess was wrong. All of this exists so that software never has to know about the pipeline.

The R3000A largely doesn't bother. It exposes both hazards and expects the software to work around them.

### What this means when writing assembly

#### The branch delay slot

The instruction immediately after a branch **always executes**, whether the branch is taken or not. It was already fetched, and the hardware doesn't throw it away. This position is called the [*delay slot*][delay-slot]: the instruction you read *after* a jump actually runs *before* the jump lands.

Consider the snippet below. It's real BIOS code, from a function returning to its caller:

```
80054190  lw      $t7, 0x0($sp)
80054194  jr      $ra              # return to the caller
80054198  addiu   $sp, $sp, 0x8    # ...and this ran too
```

`jr $ra` is an unconditional jump, so there's no question about whether it was taken or not. It jumped: `$ra` held `800541EC`, and that's where execution continued. But `$sp` was updated as well, from `801FFD50` to `801FFD58`. The instruction sitting *after* the return ran anyway, and it did real work: it popped the stack frame on the way out.

The nice part is that this is not just a tax to be paid, it's a free instruction slot. Below is another piece of real BIOS code, taken from my emulator's debugger. It's a byte-copy loop, where `$a1` is the source, `$a0` the destination, and `$a2` the count:

```
BFC02B68  lbu     $t6, 0x0($a1)      # load a byte from the source
BFC02B6C  addiu   $a2, $a2, -0x1     # count--
BFC02B70  addiu   $a1, $a1, 0x1      # source++
BFC02B74  addiu   $a0, $a0, 0x1      # dest++
BFC02B78  bgtz    $a2, 0xBFC02B68    # more to do? go round again
BFC02B7C  sb      $t6, -0x1($a0)     # <- delay slot: store the byte
```

The store is placed in the delay slot, so it runs on every iteration, including the last one, where the branch isn't taken and the byte still needs to be stored. The offset is `-0x1($a0)` because `$a0` was already incremented at that point. Whoever wrote this bent the loop around the delay slot instead of wasting it.

#### The load delay slot

The value from a load isn't available in its target register for the next instruction. It lands one instruction later, and the pipeline diagram shows why:

{% include diagrams/load-delay-hazard.svg %}

So the rule is: never use a loaded register in the instruction right after the load.

This one is nastier than the branch slot, because nothing looks wrong. The disassembly reads naturally. You just get a stale register value, and a game that renders garbage twenty minutes later.

If you look back at the BIOS loop, you'll see this rule being obeyed too: `$t6` is loaded at `BFC02B68` and it's not read until `BFC02B7C`. Those three `addiu` instructions are not only advancing the pointers and the counter, they're also covering the load's delay.

### Does the compiler handle this when you write C?

This was the question I was most curious about, so I checked it myself. The short answer is: yes, completely, and you never find out it happened.

Here's about the smallest C function that trips the load delay:

```c
int add_loaded(int *p, int k)
{
    int a = *p;
    return a + k;
}
```

Compiled for MIPS I (using `clang -target mipsel-unknown-elf -march=mips1 -O1`), the body comes out as:

```
lw      $1, 0($4)
nop                       # <- load delay slot, nothing to fill it with
addu    $2, $1, $5
...
jr      $ra               # <- jump to $ra: the return
addiu   $sp, $sp, 8       # <- branch delay slot, filled with real work
```

Both hazards were handled in a four-line function. There was nothing useful to put after the load, so the compiler inserted a `nop`. For the branch delay slot, it *did* have something available (the stack pointer adjustment), so the return costs nothing extra.

If we give the compiler more to work with, it does even better:

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

The second load slots neatly into the first load's shadow, because it doesn't depend on it. The scheduler is doing exactly what a careful assembly programmer would do by hand.

The compiler also wraps every function body between these directives:

```
.set noreorder
...
.set reorder
```

[`.set noreorder`][gas-mips] tells the assembler: *don't touch my instruction order, I've handled the delay slots myself*. This directive exists because the assembler can do this job too, dropping in `nop`s to keep hand-written assembly correct.

So the abstraction never really disappeared, it just moved. The hardware declined to hide the pipeline, and the toolchain hides it instead. And you can switch that off when you're writing a boot ROM and want to deal with the raw machine.

### Show me the code

So, what does all of this mean for an emulator?

The good news, and the thing that took me the longest to believe, is that **you don't have to simulate the five pipeline stages**. Only the two places where the overlap is *observable*. Everything else is invisible, so you get to keep the same one-instruction-at-a-time interpreter loop you'd write for a 65816, with about ten lines of extra state.

#### Two program counters

Because of the branch delay slot, we can't have a single `pc` anymore. We need to keep track of both what's executing now and what's queued behind it:

```cpp
u32 pc = 0;          // instruction about to execute
u32 next_pc = 0;     // the one after it; a branch rewrites this
u32 current_pc = 0;  // the one executing now, kept for exceptions
```

The whole trick is the ordering inside the `step()` function. Both counters are advanced *before* executing the instruction:

```cpp
pc = next_pc;
next_pc += 4;

execute(instr);
```

Now a branch writes to `next_pc`, and `pc`, which already points at the delay slot instruction, is left alone. The delay slot runs next, and then the branch target. The behavior falls out of the data structure instead of requiring a special case, and branching becomes just:

```cpp
void Cpu::branch(u32 offset)
{
    next_pc = pc + (offset << 2);
    branching = true;
}
```

#### Two register files

Because of the load delay slot, a write can't be visible to the instruction immediately after the one that issued it. To achieve this, instructions read from one array and write to another:

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

If you read this in order, it's exactly the rule we described: the previous instruction's load lands before this one runs, and this one's own writes only become visible after it's over. With two arrays and a copy, every load is correct, including the ones you haven't written yet. The alternative would be handling the delay in each load opcode individually, which works fine right up until you add the twentieth one late at night.

### Wrapping-up

That was the big surprise for me in this project. I didn't expect a CPU to make this kind of trade-off, handing a hardware problem over to whoever writes the instructions. It's one of the most interesting things I've found while writing this emulator so far.

The emulator is available [here][repository], and the whole CPU is a single file. [psx-spx][psx-spx] is the hardware reference I kept open the whole time, and the [ps1-tests][ps1-tests] test suite caught most of my mistakes.

[repository]: https://github.com/eduardovra/wobble-psx
[r3000a]: https://en.wikipedia.org/wiki/R3000
[65816]: https://en.wikipedia.org/wiki/WDC_65C816
[psx-spx]: https://psx-spx.consoledev.net/cpuspecifications/
[delay-slot]: https://en.wikipedia.org/wiki/Delay_slot
[gas-mips]: https://sourceware.org/binutils/docs/as/MIPS_002dDependent.html
[ps1-tests]: https://github.com/JaCzekanski/ps1-tests
