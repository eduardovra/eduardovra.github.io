---
layout: post
title: "C++ features and their C99 equivalents" # working title, not final
description: A feature-by-feature look at what C++ does for you, what the equivalent C99 code looks like, and what each one costs.
tags: [cpp, c, emulator, playstation]
---

## Draft notes — remove before publishing

This is the reference companion to the other draft,
`cpp-for-a-returning-c-programmer` — that one is the essay-shaped
material, this one is the table. Same question applied 36 times: what does
the feature do, what would I have written in C99, and what does it cost.
(Link them with `{% raw %}{% post_url %}{% endraw %}` once whichever one
goes first is actually published; the tag breaks the build while both are
still drafts.)

**C99 is the baseline on purpose.** It's the C I actually know, and it's
what makes the comparison honest — several of the tidy answers people give
("just use `_Generic`", "just use `static_assert`") are C11 or C23, not
something I had. Where that happens it's marked.

**Where modern C changes the answer there's a third block.** Seven
features get a `**C23**` snippet: function templates (`_Generic` +
`typeof`), `constexpr` variables, `static_assert`, the `dynamic_cast` tag
(`enum : uint8_t`, `unreachable()`), overloading (`_Generic`),
`optional`/`expected` (`[[nodiscard]]`, `nullptr`), and `auto`
(`auto`/`typeof`). The rest don't have one, and that's the finding rather
than an omission — three say so explicitly with the reason:

- **Lookup tables:** C23's `constexpr` is objects-only, so it lands in the
  same `.rodata` as a C99 `static const`, and you can't even
  `static_assert` on an element. Compile-time *execution* is still absent.
- **RAII:** no scope-exit mechanism in any C standard. `defer` is a C2y
  discussion; `__attribute__((cleanup))` works but is a GNU extension.
- **`new`/`delete`:** `free_sized` exists on paper and glibc 2.39 doesn't
  declare it.

Verified on gcc 13.3, which accepts most of C23 — `constexpr`, `auto`,
`typeof`, `nullptr`, `unreachable()`, `enum : type`, `[[nodiscard]]`,
`static_assert`. Two things I wanted and couldn't verify: `#embed` (needs
gcc 15 / clang 19; would let a BIOS be baked into the binary) and
`_BitInt` (gcc 14).

**Everything here was compiled and measured**, on gcc/g++ 13.3.0 on
x86_64, not recalled. Every snippet builds under `gcc -std=c99 -Wall
-Wextra` or `g++` at the standard the feature needs. Every claim about
generated code comes from `objdump -d`, `readelf`, `-fdump-lang-class`, or
a benchmark that's described where it's used. Where a measurement came out
too noisy to mean anything, it says so instead of quoting a number.

**Some results went against what I expected**, which is the interesting
part and probably where the writing should go:

- The hand-rolled C vtable and C++ `virtual` produce *identical*
  disassembly — but only the C++ one can be devirtualized.
- `static_cast` emits *more* instructions than `container_of`, because it
  has to preserve null.
- `std::sort` beat `qsort` by 1.87x, and most of the gap is comparator
  inlining.
- `-fno-exceptions` does not remove `.eh_frame`, and the size saving is
  mostly landing-pad *code*, not tables.
- The two "the compiler won't warn you" claims I believed both turned out
  false on GCC 13.

**TODO.** Cut this down. 36 features is a reference, not a post — pick the
ones where the measurement surprised me and let the rest go.


---

## Compile-time and generics

### Function templates

**What it does.** You write one function with the type left as a
parameter, and the compiler stamps out a separate real function for
every type you actually use it with. Where the type appears in an
argument, the compiler works it out from the call and you don't name it
at all.

**C++**

```cpp
#include <cstdint>
#include <cstring>

// Read a little-endian value of any width out of a byte array.
template <typename T>
T bus_read(const uint8_t* mem, uint32_t addr) {
    T v;
    std::memcpy(&v, mem + addr, sizeof(T));
    return v;
}

// Here T is deduced from the argument, so no <> at the call site.
template <typename T>
T sign_extend16(T v) { return T(int16_t(v)); }

void demo(const uint8_t* ram) {
    uint8_t  op   = bus_read<uint8_t>(ram, 0x100);   // one instantiation
    uint32_t word = bus_read<uint32_t>(ram, 0x104);  // another
    uint32_t imm  = sign_extend16(word);             // T deduced: uint32_t
    (void)op; (void)imm;
}
```

**C99**

```c
#include <stdint.h>
#include <string.h>

#define DEFINE_BUS_READ(T)                                    \
    static T bus_read_##T(const uint8_t *mem, uint32_t addr)  \
    {                                                         \
        T v;                                                  \
        memcpy(&v, mem + addr, sizeof v);                     \
        return v;                                             \
    }

DEFINE_BUS_READ(uint8_t)
DEFINE_BUS_READ(uint16_t)
DEFINE_BUS_READ(uint32_t)

void demo(const uint8_t *ram)
{
    uint8_t  op   = bus_read_uint8_t(ram, 0x100);
    uint16_t half = bus_read_uint16_t(ram, 0x102);
    uint32_t word = bus_read_uint32_t(ram, 0x104);
    uint32_t imm  = (uint32_t)(int16_t)half;   /* no generic version */
    (void)op; (void)word; (void)imm;
}
```

C11's `_Generic` can pick a function based on the *type of an
expression*, which would cover `sign_extend16`, but it cannot dispatch on
a return type, so it does not help `bus_read` at all. In C99 there is no
`_Generic` either way, and the macro above is the whole toolkit.

**C23**

```c
#include <stdint.h>
#include <string.h>

static uint16_t sx16_u16(uint16_t v) { return (uint16_t)(int16_t)v; }
static uint32_t sx16_u32(uint32_t v) { return (uint32_t)(int16_t)v; }

/* C11 _Generic: one name, the compiler picks by the argument's type. */
#define sign_extend16(v) _Generic((v),  \
        uint16_t: sx16_u16,             \
        uint32_t: sx16_u32)(v)

/* C23 typeof: a generic macro no longer needs the type passed in. */
#define SWAP(a, b) do { typeof(a) t_ = (a); (a) = (b); (b) = t_; } while (0)

void demo(const uint8_t *ram)
{
    uint32_t word = 0, other = 0;
    memcpy(&word, ram + 0x104, sizeof word);
    uint32_t imm = sign_extend16(word);
    SWAP(word, other);
    (void)imm; (void)word; (void)other;
}
```

That closes the deduction gap for arguments, and `typeof` removes the
type parameter from macros that need a temporary. It does not close the
gap for `bus_read`: dispatch is still on the *arguments*, never on the
return type, so `DEFINE_BUS_READ` survives into C23 unchanged.

**What the compiler does for you.** It parses the body once, type-checks
it, then emits one machine-code copy per type actually used, deducing the
type from the arguments where it can. The macro version does the same
code duplication by pasting tokens, without checking anything until each
expansion.

**What it costs.** Nothing at runtime — the emitted functions are what
you would have written. Binary size grows with the number of
instantiations, exactly as it does with the macro. The definition has to
live in a header so every including translation unit re-parses and
re-instantiates it, which is where the compile-time cost comes from, and
mistakes are reported from inside the instantiation rather than at the
call. Against that, the macro version breaks on any type whose name is
more than one token — `DEFINE_BUS_READ(unsigned char)` pastes to
`bus_read_unsigned char` and fails to parse.

### Class templates

**What it does.** The same substitution applied to a struct: the type
(and any integer constants) become parameters, and each combination you
use produces a distinct type with its own functions. This is how you get
a typed container without `void*` and element-size arithmetic.

**C++**

```cpp
#include <cstddef>
#include <cstdint>

template <typename T, size_t N>
class Fifo {
public:
    bool push(T v) {
        if (count_ == N) return false;
        data_[(head_ + count_) % N] = v;
        ++count_;
        return true;
    }
    bool pop(T* out) {
        if (count_ == 0) return false;
        *out = data_[head_];
        head_ = (head_ + 1) % N;
        --count_;
        return true;
    }
private:
    T      data_[N];
    size_t head_  = 0;
    size_t count_ = 0;
};

Fifo<uint32_t, 16> gp0_commands;   // GPU command words
Fifo<uint8_t, 8>   cdrom_response; // CD-ROM response bytes
```

**C99**

```c
#include <stddef.h>
#include <stdint.h>

#define DEFINE_FIFO(name, T, N)                              \
    typedef struct {                                         \
        T      data[N];                                      \
        size_t head, count;                                  \
    } name;                                                  \
                                                             \
    static int name##_push(name *f, T v)                     \
    {                                                        \
        if (f->count == (N)) return 0;                       \
        f->data[(f->head + f->count) % (N)] = v;             \
        f->count++;                                          \
        return 1;                                            \
    }                                                        \
                                                             \
    static int name##_pop(name *f, T *out)                   \
    {                                                        \
        if (f->count == 0) return 0;                         \
        *out = f->data[f->head];                             \
        f->head = (f->head + 1) % (N);                       \
        f->count--;                                          \
        return 1;                                            \
    }

DEFINE_FIFO(Gp0Fifo, uint32_t, 16)
DEFINE_FIFO(CdromFifo, uint8_t, 8)

static Gp0Fifo   gp0_commands;
static CdromFifo cdrom_response;

void demo(void)
{
    uint32_t w;
    uint8_t  b;
    Gp0Fifo_push(&gp0_commands, 0xe1000000);
    Gp0Fifo_pop(&gp0_commands, &w);
    CdromFifo_push(&cdrom_response, 0x02);
    CdromFifo_pop(&cdrom_response, &b);
}
```

The other C99 option is one `void*`-based FIFO that takes an element size
at runtime. That gives you a single copy of the code, but the type
checking goes away and every access becomes pointer arithmetic on
`char*`.

**What the compiler does for you.** It generates a separate struct and a
separate set of functions per `<T, N>` pair, so `N` is a literal inside
`push` and `pop` and the `%` can be strength-reduced. The C macro
produces byte-for-byte the same thing; the difference is that the C++
version is parsed as code, so errors point at the template body rather
than at an expansion.

**What it costs.** Nothing at runtime. Code size scales with the number
of distinct instantiations, and it is easy to forget that
`Fifo<uint32_t, 16>` and `Fifo<uint32_t, 32>` are two full copies of
`push` and `pop`. The definition lives in a header, so compile times
grow. Readability cost is real but small here; it gets much worse once
templates take templates as parameters.

### `constexpr` variables (vs C99 `#define`, `enum`, `const`)

**What it does.** `constexpr` on a variable means two things at once:
it is `const`, and its value is known to the compiler, so it can be used
where the language demands a genuine compile-time constant — array
sizes, `case` labels, template arguments, `static_assert`. If the
initializer turns out not to be constant, you get an error on the
declaration rather than at some distant use.

**C++**

```cpp
#include <array>
#include <cstddef>
#include <cstdint>

constexpr uint32_t kCpuClockHz = 33868800;
constexpr size_t   kRamSize    = 2 * 1024 * 1024;
constexpr size_t   kVramWords  = 1024 * 512;

static uint8_t ram[kRamSize];                  // array size: fine
static std::array<uint16_t, kVramWords> vram;  // template argument: fine

static_assert(kRamSize % 4096 == 0, "RAM must be a whole number of pages");

// constexpr uint32_t k = rand();  // error at the definition, not at a use
```

**C99**

```c
#include <stddef.h>
#include <stdint.h>

#define RAM_SIZE (2 * 1024 * 1024)  /* no type, no scope, no debug symbol */
enum { CYCLES_PER_SCANLINE = 2172 };      /* typed int, real constant */
static const size_t ram_size = RAM_SIZE;  /* typed, but see below */

static uint8_t ram[RAM_SIZE];             /* fine */
/* static uint8_t ram2[ram_size]; */      /* error: in C, a const object is
                                             not a constant expression */
```

C99 gives you three tools and none of them does the whole job. `#define`
works everywhere but has no type and no scope. `enum` is a real constant
expression with a type, but only `int` — no `size_t`, no `uint32_t`, no
non-integers. `const` gets you a typed, scoped, debuggable symbol that is
*not* a constant expression: the commented line above fails with
`variably modified 'ram2' at file scope`. Inside a function the same
declaration compiles, but as a C99 VLA, which is a different thing.
**C23**

```c
#include <stddef.h>
#include <stdint.h>

constexpr uint32_t cpu_clock_hz = 33868800;
constexpr size_t   ram_size     = 2 * 1024 * 1024;

static uint8_t ram[ram_size];   /* now legal: a real constant expression */
static_assert(ram_size % 4096 == 0, "RAM must be a whole number of pages");

uint32_t hz(void) { return cpu_clock_hz + ram[0]; }
```

This is the one place in the whole list where C caught up completely. A
`constexpr` object is typed, scoped, visible to the debugger, and a
constant expression — all four at once, which none of the three C99
tools manages. Objects only, though: see the next section for what it
still cannot do.

**What the compiler does for you.** It checks at the point of
declaration that the value really is computable at compile time, and then
lets you use that one typed, scoped name in every context that needs a
constant.

**What it costs.** Nothing at runtime and nothing in binary size; the
value is folded into the instructions that use it, the same as a macro.
No measurable compile-time cost. It is strictly less error-prone than the
C99 choices, which is not something you can say about most of this list.

### `constexpr` functions and compile-time lookup tables

**What it does.** A `constexpr` function can be run by the compiler
during compilation, with real loops and local variables, and its result
used as a compile-time constant. The practical use in an emulator is
building a lookup table in source code instead of at startup.

**C++**

```cpp
#include <array>
#include <cstdint>

// PlayStation framebuffer is BGR555; expand a 5-bit channel to 8 bits.
constexpr uint8_t expand5(int c) { return uint8_t(c * 255 / 31); }

constexpr std::array<uint8_t, 32> make_expand5_table() {
    std::array<uint8_t, 32> t{};
    for (int i = 0; i < 32; ++i)
        t[i] = expand5(i);
    return t;
}

constexpr auto kExpand5 = make_expand5_table();  // 32 bytes in .rodata

static_assert(kExpand5[0]  == 0,   "black stays black");
static_assert(kExpand5[31] == 255, "white saturates");

uint32_t to_rgb888(uint16_t bgr555) {
    uint8_t r = kExpand5[bgr555 & 0x1f];
    uint8_t g = kExpand5[(bgr555 >> 5) & 0x1f];
    uint8_t b = kExpand5[(bgr555 >> 10) & 0x1f];
    return uint32_t(r) << 16 | uint32_t(g) << 8 | b;
}
```

**C99**

```c
#include <stdint.h>

static uint8_t expand5[32];   /* .bss: zero until someone fills it */

static void init_expand5(void)
{
    for (int i = 0; i < 32; i++)
        expand5[i] = (uint8_t)(i * 255 / 31);
}

uint32_t to_rgb888(uint16_t bgr555)
{
    uint8_t r = expand5[bgr555 & 0x1f];
    uint8_t g = expand5[(bgr555 >> 5) & 0x1f];
    uint8_t b = expand5[(bgr555 >> 10) & 0x1f];
    return (uint32_t)r << 16 | (uint32_t)g << 8 | b;
}

void emulator_init(void) { init_expand5(); }   /* forget this: all black */
```

C99 cannot express this. There is no mechanism for running your code at
compile time, and C23's `constexpr` does not add one — it applies to
objects, not functions. The three real options are: fill the table at
startup as above; write the 32 literal bytes out by hand; or generate the
table with a separate program and commit the generated file. Nested
macros can compute small fixed-size tables, but only for expressions a
macro can express, and the result is unreadable.

Checking the compiler output confirms where the table lands: at `-O2` the
C++ `kExpand5` is 32 bytes in `.rodata`, and the C `expand5` is 32 bytes
in `.bss`.

No C23 snippet here, because I tried it and C23 does not help. You can
write `constexpr uint8_t expand5[32] = { 0, 8, 16, ... }` with the 32
bytes spelled out, but that is the "write it by hand" option with a new
keyword on it — and measured, it lands in exactly the same place a plain
C99 `static const` array does (`.rodata`, 32 bytes, identical object
file). Worse, indexing a `constexpr` array is *not* a constant
expression in C23: `static_assert(expand5[0] == 0)` fails with
`error: expression in static assertion is not constant` on gcc 13.3, so
you cannot even check the table you just wrote. The gap is compile-time
*execution*, and C still has none.

**What the compiler does for you.** It runs `make_expand5_table` at
compile time and emits the finished 32 bytes as read-only data, then
checks two entries with `static_assert` before your program exists. The
C99 version has to be initialized at runtime, so it lives in writable
memory, cannot be verified at compile time, and breaks silently if you
forget to call the init function.

**What it costs.** Nothing at runtime — less than nothing, since you drop
the startup loop and the table can sit in ROM. Binary size is the same
bytes you would have written by hand. The cost is compile time: the
compiler is interpreting your code, which is orders of magnitude slower
than running it, and there are hard limits on how many steps it will take
(GCC's `-fconstexpr-ops-limit`, Clang's `-fconstexpr-steps`) that a large
generated table can hit. Readability suffers too, since `constexpr`
functions are written under restrictions and often look contorted for
that reason.

### `static_assert` (and the C99 negative-array-size trick)

**What it does.** Checks a compile-time condition and stops the build
with your message if it is false. Typical use is guarding assumptions
about layout: that a register struct is the size you think it is, that a
pointer is 64 bits, that a table has the number of entries the opcode
decoder assumes.

**C++**

```cpp
#include <cstdint>

struct Registers {
    uint32_t gpr[32];
    uint32_t pc, hi, lo;
};

static_assert(sizeof(Registers) == 140, "Registers layout changed");
static_assert(alignof(Registers) == 4, "Registers must stay 4-byte aligned");
static_assert(sizeof(void*) == 8);   // C++17: message optional
```

**C99**

```c
#include <stdint.h>

struct Registers {
    uint32_t gpr[32];
    uint32_t pc, hi, lo;
};

/* A zero-or-negative size is a compile error; the name carries the
   message, because there is nowhere else to put it. */
#define STATIC_ASSERT(cond, name) \
    typedef char static_assert_##name[(cond) ? 1 : -1]

STATIC_ASSERT(sizeof(struct Registers) == 140, registers_size);
STATIC_ASSERT(sizeof(void *) == 8, pointers_are_64_bit);
```

C11 has `_Static_assert` (and `static_assert` via `<assert.h>`), which is
the same feature with a real message. In C99 the negative-array-size
typedef above is the standard workaround and it does work; the failure
reads `error: size of array 'static_assert_int_is_64_bit' is negative`,
so the diagnostic is the identifier you chose. Two constraints: the
condition must be an integer constant expression, and each `name` must be
unique within its scope.

**C23**

```c
#include <stdint.h>

struct Registers {
    uint32_t gpr[32];
    uint32_t pc, hi, lo;
};

static_assert(sizeof(struct Registers) == 140, "Registers layout changed");
static_assert(alignof(struct Registers) == 4, "must stay 4-byte aligned");
static_assert(sizeof(void *) == 8);   /* message optional, as in C++17 */
```

Identical to the C++ version, down to the optional message — C23 makes
`static_assert` and `alignof` plain keywords, so `<assert.h>` and
`_Alignof` are no longer needed. This feature is simply finished in
modern C.

**What the compiler does for you.** Not much beyond the C99 trick — it
prints the message you wrote instead of making you decode a name in an
error about array sizes, and it is an ordinary declaration rather than a
typedef, so it can appear anywhere a declaration can, including inside a
class body.

**What it costs.** Nothing at runtime, nothing in the binary,
nothing measurable at compile time. This one is free in both languages;
the difference is only in the quality of the error message.

### `inline`

**What it does.** In both languages `inline` is mostly not about
inlining — the optimizer decides that regardless. It is about being
allowed to put a function *definition* in a header without the linker
complaining that several object files define the same symbol. C++ and C99
solve that problem in different ways, and the C99 rule is the one that
surprises people.

**C++**

```cpp
// bus.hpp
#include <cstdint>

// One definition per translation unit; the linker keeps one and
// discards the rest. Works the same at -O0 and -O2.
inline uint32_t mask_region(uint32_t addr) { return addr & 0x1fffffff; }

inline constexpr uint32_t kRamMask = 0x1fffff;   // C++17: inline variable
```

**C99**

```c
/* bus.h */
#include <stdint.h>

/* C99: this is an *inline definition*. It is NOT an external
   definition, so it cannot satisfy the linker on its own. */
inline uint32_t mask_region(uint32_t addr) { return addr & 0x1fffffff; }
```

```c
/* bus.c */
#include "bus.h"

/* Exactly one TU must add this line, which turns the header's inline
   definition into the one external definition of the function. */
extern uint32_t mask_region(uint32_t addr);
```

Three differences worth knowing. First, C++'s `inline` says "this
definition may be repeated in every translation unit, they must be
identical, and the linker picks one"; C99's says "this translation unit
has a definition the compiler may inline, but somebody still has to
provide the external definition." Omit `bus.c` and the program links
fine at `-O2`, because every call got inlined and nothing referenced the
symbol, then fails at `-O0` with `undefined reference to 'mask_region'`.
That is an unpleasant way to learn the rule. Second, GNU89's
`extern inline` meant close to the opposite of C99's, which is why old
code compiled with `-std=gnu89` breaks when moved to `-std=c99`. Third,
most C code sidesteps all of this by writing `static inline` in the
header: one private copy per translation unit, no linker involvement, no
warning when a translation unit doesn't use it. C++17's `inline`
variables extend the same "one shared definition" rule to data, which C
has no equivalent for at all.

**What the compiler does for you.** In C++ it emits the function into
every object file that needs it, marks the copies as mergeable, and the
linker keeps one. In C99 it emits nothing unless you ask, and bookkeeping
which translation unit provides the real definition is your job.

**What it costs.** Nothing at runtime. `static inline` in C can enlarge
the binary, since each translation unit gets its own copy of anything the
optimizer chose not to inline; C++'s merging avoids that. Compile time
grows with the amount of code in headers, in both languages. The
readability cost is the rule itself: `inline` means three different
things depending on the language and the standard, and none of them is
"please inline this".

---

## Types, casts, and object layout

### `static_cast`

**What it does.** Converts between related types when the compiler can
check the relationship: pointer to base and back, `void*` to `T*`,
integer widths, enum to integer. For pointers inside a class hierarchy
it does arithmetic — it looks up the offset of the base subobject and
adds or subtracts it, which is exactly the `&d->member` and
`container_of` pair a C programmer writes by hand.

**C++**

```cpp
#include <cstdint>
#include <cstdio>

struct BusDevice {
    virtual uint32_t read32(uint32_t addr) = 0;
    virtual ~BusDevice() = default;
};
struct Debuggable {
    virtual void dump(std::FILE* f) const = 0;
    virtual ~Debuggable() = default;
};
struct Spu : BusDevice, Debuggable {
    uint16_t voice[24 * 8];
    uint32_t read32(uint32_t) override { return 0; }
    void dump(std::FILE*) const override {}
};

void bind(Spu& spu)
{
    Debuggable* dbg  = &spu;                   // upcast: + 8
    Spu*        back = static_cast<Spu*>(dbg);  // downcast: - 8

    void* raw = &spu;
    Spu*  p   = static_cast<Spu*>(raw);         // void* -> T*
    auto  lo  = static_cast<uint8_t>(0xdeadbeefu);
    (void)back; (void)p; (void)lo;
}
```

**C99**

```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

struct BusDeviceOps { uint32_t (*read32)(void* self, uint32_t addr); };
struct DebugOps     { void (*dump)(const void* self, FILE* f); };
struct BusDevice  { const struct BusDeviceOps* ops; };
struct Debuggable { const struct DebugOps* ops; };

struct Spu {
    struct BusDevice  bus;    /* offset 0 */
    struct Debuggable dbg;    /* offset 8 */
    uint16_t voice[24 * 8];
};

#define container_of(ptr, type, member) \
    ((type*)((char*)(ptr) - offsetof(type, member)))

void bind(struct Spu* spu)
{
    struct Debuggable* dbg  = &spu->dbg;                  /* + 8 */
    struct Spu*        back = container_of(dbg, struct Spu, dbg);

    void* raw = spu;
    struct Spu* p = raw;                 /* implicit in C */
    uint8_t lo = (uint8_t)0xdeadbeefu;
    (void)back; (void)p; (void)lo;
}
```

**What the compiler does for you.** It knows the byte offset of every
base subobject and writes the add or subtract for you, so the number
never appears in your source and cannot go stale when a field moves.
It also refuses the conversion outright if the two types are not
actually related, which is the check a C cast never performs.

**What it costs.** Measured on GCC 13.3.0, x86_64-linux-gnu: both
versions of `Spu` are 400 bytes with the second interface at offset 8 —
the C++ multiple-inheritance layout and the hand-nested C struct agree
exactly. At `-O2` the C `container_of` compiles to one instruction,
`lea -0x8(%rdi),%rax`. The C++ `static_cast` compiles to four:
`xor`, `lea -0x8`, `test %rdi,%rdi`, `cmove`. The extra three are a
null check, because the standard requires a null pointer to survive the
cast unchanged and `container_of` on `NULL` happily returns `-8`. So
`static_cast` is very slightly *more* code than the C idiom, and it is
correct in a case the C idiom is not. With single inheritance and no
virtual functions the base sits at offset 0 and `static_cast` emits
nothing at all. Nothing at compile time worth measuring, nothing in
binary size.

### `reinterpret_cast`

**What it does.** Relabels the bits at an address as a different type
without changing the address or emitting any conversion. It is the
direct equivalent of a C pointer cast, including the part where the
compiler stops helping you.

**C++**

```cpp
#include <cstdint>

// the GPU's 1MB VRAM, owned as bytes, viewed as 16-bit pixels
struct Vram { alignas(2) uint8_t bytes[1024 * 512 * 2]; };

uint16_t* as_pixels(Vram& v)
{
    return reinterpret_cast<uint16_t*>(v.bytes);
}

// a memory-mapped register block at a fixed offset
struct DmaChannel {
    uint32_t madr;
    uint32_t bcr;
    uint32_t chcr;
};

DmaChannel* channel(uint8_t* io, uint32_t offset)
{
    return reinterpret_cast<DmaChannel*>(io + offset);
}
```

**C99**

```c
#include <stdint.h>

struct Vram { uint8_t bytes[1024 * 512 * 2]; };

uint16_t* as_pixels(struct Vram* v)
{
    return (uint16_t*)v->bytes;      /* same relabel, same risk */
}

struct DmaChannel {
    uint32_t madr;
    uint32_t bcr;
    uint32_t chcr;
};

struct DmaChannel* channel(uint8_t* io, uint32_t offset)
{
    return (struct DmaChannel*)(io + offset);
}
```

Note the `alignas(2)` in the C++ version. C99 has no alignment
specifier — `_Alignas` is C11 — so the C99 way to guarantee the buffer
is aligned for the type you intend to view it as is to declare the
storage as that type, or as a union, and take a `uint8_t*` from it:
`static uint32_t io_storage[16];` then `(uint8_t*)io_storage`. A bare
`uint8_t io[64]` gives you no alignment promise beyond 1.

**What the compiler does for you.** Almost nothing, deliberately. It
checks that both sides are pointer-ish and stops there. The one real
service is that the keyword is greppable: every place you overrode the
type system is a token you can search for, which `(T*)` is not.

**What it costs.** Nothing at runtime. At `-O2` on GCC 13.3.0,
x86_64-linux-gnu, `as_pixels` is `mov %rdi,%rax; ret` and `channel` is
`lea (%rdi,%rsi,1),%rax; ret` — the cast itself contributes no
instruction in either. The cost is entirely in what it does not check:
alignment, object lifetime, and aliasing are all still yours to get
right, and a `reinterpret_cast` between a base and a derived class
silently produces the wrong address where `static_cast` would have
produced the right one.

### `const_cast`

**What it does.** Adds or removes `const` (or `volatile`) from a
pointer or reference type and nothing else. It exists so that the one
legitimate need — calling an older API whose signature is not
`const`-correct — does not require a cast that could also change the
pointed-to type by accident.

**C++**

```cpp
#include <cstdint>
#include <cstdio>
#include <vector>

// a C library that takes a non-const pointer but only reads
extern "C" void legacy_crc(void* data, std::size_t n);

uint32_t checksum(const std::vector<uint8_t>& bios)
{
    // the API is wrong, not us: strip const to satisfy the signature
    legacy_crc(const_cast<uint8_t*>(bios.data()), bios.size());
    return 0;
}
```

**C99**

```c
#include <stddef.h>
#include <stdint.h>

void legacy_crc(void* data, size_t n);

uint32_t checksum(const uint8_t* bios, size_t n)
{
    legacy_crc((uint8_t*)bios, n);   /* the cast that drops const */
    return 0;
}
```

**What the compiler does for you.** It guarantees the cast changes
*only* qualification. `(uint8_t*)bios` in C would compile just as
happily if `bios` were a `const uint32_t*` and quietly reinterpret the
bytes; `const_cast<uint8_t*>` on a `const uint32_t*` is a compile
error.

**What it costs.** Nothing at runtime — it is a type-system operation
with no instructions on either side. The cost is the same in both
languages and it is not the cast: actually *writing* through a pointer
to an object that was originally defined `const` is undefined behaviour
in C99 (6.7.3p5) and in C++, regardless of how you obtained the
pointer. `const_cast` is safe only when the underlying object was not
const to begin with. In C the equivalent mistake is invisible; in C++
the keyword at least marks the line. GCC's `-Wcast-qual` flags the C
form.

### `dynamic_cast`

**What it does.** Asks at runtime whether a pointer to a base class
actually points at a particular derived class, and returns the
correctly adjusted pointer if so or `nullptr` if not. It replaces the
kind tag a C programmer puts in the base struct, using the type
information the compiler already emitted for virtual dispatch.

**C++**

```cpp
#include <cstdint>

struct BusDevice {
    virtual uint32_t read32(uint32_t addr) = 0;
    virtual ~BusDevice() = default;
};
struct Dma : BusDevice {
    uint32_t channel[7];
    uint32_t read32(uint32_t) override { return 0; }
    void run_channel(int ch) { channel[ch]++; }
};
struct Gpu : BusDevice {
    uint32_t read32(uint32_t) override { return 0; }
};

// the bus holds BusDevice*; only the DMA has run_channel
void tick(BusDevice* dev)
{
    if (Dma* dma = dynamic_cast<Dma*>(dev))   // nullptr if not a Dma
        dma->run_channel(0);
}
```

**C99**

```c
#include <stddef.h>
#include <stdint.h>

enum DevKind { DEV_DMA, DEV_GPU };
struct BusDevice { enum DevKind kind; };
struct Dma { struct BusDevice base; uint32_t channel[7]; };
struct Gpu { struct BusDevice base; };

#define container_of(ptr, type, member) \
    ((type*)((char*)(ptr) - offsetof(type, member)))

static void run_channel(struct Dma* dma, int ch) { dma->channel[ch]++; }

void tick(struct BusDevice* dev)
{
    if (dev->kind == DEV_DMA)                 /* one integer compare */
        run_channel(container_of(dev, struct Dma, base), 0);
}
```

**C23**

```c
#include <stddef.h>
#include <stdint.h>

enum DevKind : uint8_t { DEV_DMA, DEV_GPU };   /* 1 byte, not 4 */

struct BusDevice { enum DevKind kind; };
struct Dma { struct BusDevice base; uint32_t channel[7]; };
struct Gpu { struct BusDevice base; };

#define container_of(ptr, type, member) \
    ((type*)((char*)(ptr) - offsetof(type, member)))

static void run_channel(struct Dma *dma, int ch) { dma->channel[ch]++; }

void tick(struct BusDevice *dev)
{
    switch (dev->kind) {
    case DEV_DMA: run_channel(container_of(dev, struct Dma, base), 0); break;
    case DEV_GPU: break;
    default:      unreachable();    /* C23: promise there is no other kind */
    }
}
```

Two small C23 wins on the tag itself, both aimed at the thing the C
version actually gets wrong. `enum DevKind : uint8_t` gives the tag a
fixed underlying type — measured, `sizeof` goes from 4 to 1, which
matters when the tag sits in the base of every device struct. And
`unreachable()` states that the tag has no other value, so a corrupt tag
is undefined behaviour the optimizer may assume away rather than a
silently ignored case. Neither addresses the real gap: you still
initialise the tag by hand, and nothing checks that you did.
itself, so there is no tag field to initialise and no way to set it
wrong, and it handles the cases a hand-rolled tag does not: casting to
an intermediate base, sideways casts across multiple inheritance, and
matching a derived type through a hierarchy the calling code was
compiled without knowing.

**What it costs.** This is the one with a real runtime price. On GCC
13.3.0, x86_64-linux-gnu at `-O2`, the C `tick` is five instructions
inline — `mov (%rdi),%eax; test; jne; addl; ret` — and the C++ `tick`
sets up four argument registers with the two `typeinfo` addresses and
makes an out-of-line `call __dynamic_cast`. Timed over 12.8M checks on
a 64-device vector, half of them hits, `dynamic_cast` cost 6.9–7.2 ns
per check against 0.51–0.56 ns for the tag compare plus `static_cast`
— about 13x, and the gap is a non-inlinable library call, so it does
not improve with context.

RTTI also costs binary size whether you call `dynamic_cast` or not. A
program with 21 polymorphic classes, compiled with and without
`-fno-rtti`: `.text` was 1822 bytes in both — RTTI generates no
instructions — but `.rodata` went 84 to 229 bytes (the mangled type
name strings), `.data.rel.ro` 800 to 1296 (the `typeinfo` objects and
the vtable slot pointing at them), and `.rela.dyn` 1632 to 3600
(dynamic relocations for those pointers, in a PIE build). Section
total 7841 to 10608 bytes, roughly 130 bytes per polymorphic class.

### Type punning: `std::bit_cast`, `memcpy`, and unions

**What it does.** Reads the bytes of one type as another — the
"reinterpret these 32 bits as a float" operation. `std::bit_cast<To>(from)`
(C++20) copies the object representation into a new object of the
target type. `memcpy` does the same thing spelled out. Both are
defined behaviour; `*(uint32_t*)p` is not, in either language.

**C++**

```cpp
#include <bit>
#include <cstdint>
#include <cstring>

// GTE-style: the same 32 bits used as fixed point and as a float
float bits_to_float_bitcast(uint32_t bits)
{
    return std::bit_cast<float>(bits);       // C++20
}

float bits_to_float_memcpy(uint32_t bits)
{
    float f;
    std::memcpy(&f, &bits, sizeof f);        // works in every standard
    return f;
}

// reading a little-endian 32-bit word out of the RAM byte array
uint32_t read32(const uint8_t* ram, uint32_t addr)
{
    uint32_t w;
    std::memcpy(&w, ram + addr, sizeof w);
    return w;
}
```

`std::bit_cast` needs `-std=c++20`; under `-std=c++17` GCC 13 reports
`'bit_cast' is not a member of 'std'`. It also requires both types to
be the same size and trivially copyable, checked at compile time, and
it works inside a constant expression, which `memcpy` does not.

**C99**

```c
#include <stdint.h>
#include <string.h>

float bits_to_float_memcpy(uint32_t bits)
{
    float f;
    memcpy(&f, &bits, sizeof f);
    return f;
}

/* union punning: blessed in C99 (as amended), not in C++ */
float bits_to_float_union(uint32_t bits)
{
    union { uint32_t i; float f; } u;
    u.i = bits;
    return u.f;
}

uint32_t read32(const uint8_t* ram, uint32_t addr)
{
    uint32_t w;
    memcpy(&w, ram + addr, sizeof w);
    return w;
}
```

This is the one place the two languages genuinely disagree rather than
differ in spelling. Reading a union member other than the one last
written is defined in C — C99 as amended by TC3 added the footnote to
6.5.2.3 saying the object representation is reinterpreted, and C11
states it in the text. In C++ only one member of a union is *active* at
a time and reading an inactive one is undefined; GCC supports it as an
extension anyway. So the C99 union idiom is not portable C++ even
though it compiles and works on GCC. `memcpy` is the answer that is
correct in both, and `bit_cast` is the same thing with the size and
triviality checks moved to compile time.

**What the compiler does for you.** It recognises the small fixed-size
`memcpy` and folds it into a load or a register move. There is no call
to the library function and no temporary in the final code — the
"copy" is a fiction that exists only to make the aliasing rules
satisfiable.

**What it costs.** Nothing at runtime. At `-O2` on GCC 13.3.0,
x86_64-linux-gnu, `bits_to_float_bitcast`, `bits_to_float_memcpy`
(C++20) and `bits_to_float_union` (C99) each compile to exactly
`movd %edi,%xmm0; ret` — byte-identical, one instruction. `read32`
compiles to `mov (%rdi,%rsi,1),%eax`, a single load; the `memcpy` call
is gone.

The cost of getting it wrong is real and I could observe it. A
function that writes through a `uint32_t*` and then through a `float*`
aliasing the same storage returns the stale value at `-O2` and `-O3`
and the fresh value at `-O0` or under `-fno-strict-aliasing`, in both
`gcc -std=c99` and `g++ -std=c++17`. That is the aliasing rule
deleting a store, not a theoretical concern. Notably, the emulator
pattern I expected to break — a byte store into a `uint8_t` RAM array
followed by `*(uint32_t*)(ram + off)` — was *not* miscompiled at `-O3`
by GCC 13.3.0; the results matched the `memcpy` version. It is still
undefined, just not currently exploited, which is the worst kind of
working code.

### `struct` vs `class`, and standard layout

**What it does.** In C++ `struct` and `class` are one feature with two
default access levels: members of a `struct` are public by default,
members of a `class` private. Either can have constructors,
destructors, member functions, base classes, and a vtable. Whether the
resulting object still has the layout a C compiler would give it is a
separate question, answered by the term *standard-layout*.

**C++**

```cpp
#include <cstdint>
#include <type_traits>

// shared with C: same size, same offsets
struct GpuRegs {
    uint32_t gp0, gp1, stat;
    uint16_t hres;
    uint8_t  vres;
};

// still standard-layout: functions and a constructor cost no bytes
struct GpuRegs2 : GpuRegs {
    GpuRegs2() { gp0 = gp1 = stat = 0; hres = 0; vres = 0; }
    uint32_t status() const { return stat; }
};

// one virtual function and the layout is gone
struct GpuRegs3 { uint32_t gp0, gp1, stat; uint16_t hres; uint8_t vres;
                  virtual ~GpuRegs3() = default; };

static_assert(std::is_standard_layout<GpuRegs>::value,  "ok");
static_assert(std::is_standard_layout<GpuRegs2>::value, "ok");
static_assert(!std::is_standard_layout<GpuRegs3>::value, "broken");
```

**C99**

```c
#include <stddef.h>
#include <stdint.h>

struct GpuRegs {
    uint32_t gp0, gp1, stat;
    uint16_t hres;
    uint8_t  vres;
};

/* the C99 way to assert layout, since there is no static_assert
   until C11: a negative array size fails at compile time */
typedef char assert_gpuregs_size[sizeof(struct GpuRegs) == 16 ? 1 : -1];
typedef char assert_gpuregs_stat[offsetof(struct GpuRegs, stat) == 8
                                 ? 1 : -1];

/* the C equivalent of inheriting: nest it */
struct GpuRegs2 { struct GpuRegs regs; };
```

**What the compiler does for you.** It tracks standard-layout as a
property you can query and assert on, so "does this still match the C
header" becomes a `static_assert` rather than a comment. It also warns
when you ask a layout question about a type where the answer is not
portable: `offsetof` on a non-standard-layout type produces
`-Winvalid-offsetof`, "conditionally-supported", under `-Wall
-Wextra`.

**What it costs.** Measured on GCC 13.3.0 / g++ 13.3.0,
x86_64-linux-gnu:

- `GpuRegs` is 16 bytes with `gp1` at 4, `stat` at 8, `hres` at 12,
  `vres` at 14 — identical from `gcc -std=c99` and `g++ -std=c++17`.
  `GpuRegs2`, which adds a base class, a constructor and a `const`
  member function on top of those same fields, is also 16 bytes with
  the same four offsets, and still standard-layout. Inheritance by
  itself does not break the C layout; inheritance that puts data
  members on both sides does.
- One `virtual ~GpuRegs3()` took it to 24 bytes and shifted every
  field by 8. `-fdump-lang-class` shows `size=24 align=8`, `base
  size=23`, `vptr` at offset 0. `is_standard_layout` is false.
- Mixed access levels (`public` / `private` / `public` over the same
  five fields) left the size at 16 and every offset unchanged on GCC,
  but `is_standard_layout` is false, so that agreement is this
  compiler's choice and not something the ABI owes you.
- Tail padding is the trap I did not expect. `struct PodBase {
  uint32_t a; uint8_t b; }` is 8 bytes with 3 bytes of tail padding.
  Deriving `struct PodDer : PodBase { uint8_t c; }` gives 12 bytes with
  `c` at offset 8, matching the nested C struct exactly. But give the
  base a user-declared constructor and destructor and `PodDer` becomes
  **8 bytes with `c` at offset 5** — the derived member is placed
  inside the base's padding. Nesting in C cannot do that, so the same
  fields laid out the "same" way differ by 4 bytes and one offset
  purely because the base stopped being a POD.
- Empty types differ outright. `sizeof(Empty)` where `struct Empty {}`
  is 1 in C++, and `struct Der : Empty { uint32_t x; }` is 4 — the
  empty base takes no space. An empty struct is not valid C99 at all;
  GCC accepts it as an extension, warns under `-pedantic` ("struct has
  no members"), and gives it `sizeof` 0.

None of this costs runtime. It costs a class of bug that does not exist
in C: a struct definition that used to be ABI-compatible with a C
header and silently stopped being, because someone added a `virtual`,
changed an access level, or gave a base class a destructor.

### `new` / `delete` vs `malloc` / `free`

**What it does.** `new T(args)` allocates storage for one `T`, runs its
constructor, and returns a `T*`. `delete p` runs the destructor and
frees the storage. `new T[n]` and `delete[] p` do the same for arrays,
including running the constructor and destructor for each element.

**C++**

```cpp
#include <cstdint>
#include <memory>
#include <vector>

struct Ram {
    std::vector<uint8_t> bytes;
    uint32_t mask;

    explicit Ram(uint32_t size)
        : bytes(size, 0), mask(size - 1) {}   // allocates and zeroes

    uint8_t read8(uint32_t addr) const { return bytes[addr & mask]; }
};

void run()
{
    auto ram = std::make_unique<Ram>(2u * 1024 * 1024);
    // constructor ran; no free anywhere; released at scope exit
    (void)ram->read8(0x1000);
}
```

**C99**

```c
#include <stdint.h>
#include <stdlib.h>

struct Ram {
    uint8_t* bytes;
    uint32_t mask;
};

static int ram_init(struct Ram* r, uint32_t size)
{
    r->bytes = calloc(size, 1);       /* allocate and zero */
    if (!r->bytes) return -1;         /* every caller must check */
    r->mask = size - 1;
    return 0;
}
static void ram_free(struct Ram* r) { free(r->bytes); r->bytes = NULL; }

int run(void)
{
    struct Ram ram;
    if (ram_init(&ram, 2u * 1024 * 1024) != 0) return -1;
    ram_free(&ram);                   /* on every exit path */
    return 0;
}
```

No C23 snippet worth writing. C23 does add `free_sized` and
`free_aligned_sized`, the counterpart to C++'s sized `operator delete`,
which let the allocator skip looking the block size up again — but they
are a micro-optimisation, not an answer to any of the four problems
below, and I could not even compile a call: glibc 2.39 does not declare
them yet (`implicit declaration of function 'free_sized'`). Marking
`ram_init` `[[nodiscard]]` is the one change here that would actually
prevent a bug, and that is the same `[[nodiscard]]` covered under
`optional`/`expected`.

**What the compiler does for you.** Four things `malloc` does not.
It computes the size, so `sizeof` cannot drift out of sync with the
type. It calls the constructor, so there is no reachable state between
"allocated" and "initialised" and no two-phase `ram_init` for a caller
to forget. It reports failure by throwing `std::bad_alloc` rather than
returning a pointer that can be used unchecked. And it checks that the
element count times the element size has not overflowed: `new
uint32_t[n]` with `n = SIZE_MAX/4 + 1` threw `std::bad_array_new_length`,
where `malloc(n * sizeof *p)` wrapped to 0 and returned a non-NULL
pointer to a zero-byte block.

**What it costs.** `operator new` calls `malloc` underneath, so the
allocation itself costs the same. I replaced `operator new` and
`operator new[]` to print the requested size (GCC 13.3.0,
x86_64-linux-gnu): `new Trivial` on an 8-byte type requested exactly 8
bytes, and `new Trivial[10]` requested exactly 80. But for an 8-byte
type *with a destructor*, `new WithDtor[10]` requested **88** — an
extra 8 bytes of cookie holding the element count, so that `delete[]`
knows how many destructors to run. That overhead appears per array
allocation, only for element types with a non-trivial destructor, and
it has no `malloc` equivalent because C has nothing to run.

The other costs are structural. `new`/`delete` and `malloc`/`free`
cannot be mixed in either direction. `delete` where `delete[]` was
required is undefined behaviour with no diagnostic. Throwing on
failure means allocation is a control-flow edge, which is why
`-fno-exceptions` builds use `new (std::nothrow)`. And in practice you
should be writing almost none of this: `std::vector` and
`std::make_unique` in the snippet above call `new` for you and pair
every allocation with its release, which is the actual reason the C
version needs `ram_free` on every exit path and the C++ version needs
none.

---

## Objects and polymorphism

### Member functions and the implicit `this`

**What it does.** A member function is an ordinary function whose first
argument is hidden. You write `cpu.step()` instead of
`cpu_step(&cpu)`, and inside the body a bare `pc` means `this->pc`.
The `this` pointer is that hidden first argument.

**C++**

```cpp
#include <cstdint>

struct Cpu {
    uint32_t r[32];
    uint32_t pc;

    uint32_t reg(unsigned i) const { return i ? r[i] : 0; }
    void set_reg(unsigned i, uint32_t v) { if (i) r[i] = v; }
    void step();
};

void Cpu::step()
{
    pc += 4;              // 'pc' means 'this->pc'
}
```

**C99**

```c
#include <stdint.h>

struct Cpu {
    uint32_t r[32];
    uint32_t pc;
};

uint32_t cpu_reg(const struct Cpu *c, unsigned i)
{
    return i ? c->r[i] : 0;
}

void cpu_set_reg(struct Cpu *c, unsigned i, uint32_t v)
{
    if (i) c->r[i] = v;
}

void cpu_step(struct Cpu *c)
{
    c->pc += 4;
}
```

**What the compiler does for you.** It passes the object's address as
an invisible first parameter, resolves unqualified names against the
class scope before the enclosing scope, and puts the function's name
inside the class's scope so `reg` doesn't have to be spelled
`cpu_reg`. The trailing `const` on `reg` makes `this` a
`const Cpu*`, which is a promise the compiler checks.

**What it costs.** Nothing at runtime. G++ 13.3.0 on x86_64 at `-O2`
compiles `Cpu::step` to `addl $0x4,0x80(%rdi)` and GCC 13.3.0
compiles `cpu_step` to the same single instruction — `this` arrives
in `%rdi` exactly where the explicit pointer did. The readability
cost is that the receiver is no longer written down: in
`set_reg(8, 42)` you cannot see which object is being mutated without
looking up. The declaration also has to live in the header, so
touching the class body recompiles everything that includes it, where
in C a new `static` helper in the `.c` file recompiles one file.

### Constructors and destructors

**What it does.** A constructor is an `init` function the compiler
calls for you at the point the object comes into existence; a
destructor is a `destroy` function it calls for you when the object
goes out of scope. The point is not the call itself but that you
cannot forget it on some return path.

**C++**

```cpp
struct Bios {
    uint8_t *data;
    long     size;

    explicit Bios(const char *path) : data(nullptr), size(0) {
        std::FILE *f = std::fopen(path, "rb");
        if (!f) throw "no bios";
        std::fseek(f, 0, SEEK_END);
        size = std::ftell(f);
        std::rewind(f);
        data = static_cast<uint8_t *>(std::malloc(size));
        std::fread(data, 1, size, f);
        std::fclose(f);
    }
    ~Bios() { std::free(data); }

    Bios(const Bios &) = delete;              // copying double-frees
    Bios &operator=(const Bios &) = delete;
};

uint32_t boot(const char *path)
{
    Bios bios(path);              // constructor: acquire
    if (bios.size < 4) return 0;  // destructor runs here...
    return bios.data[0];          // ...and here
}
```

**C99**

```c
struct Bios {
    uint8_t *data;
    long     size;
};

int bios_init(struct Bios *b, const char *path)
{
    FILE *f = fopen(path, "rb");
    b->data = NULL;
    b->size = 0;
    if (!f) return -1;
    fseek(f, 0, SEEK_END);
    b->size = ftell(f);
    rewind(f);
    b->data = malloc(b->size);
    if (!b->data) { fclose(f); return -1; }
    fread(b->data, 1, b->size, f);
    fclose(f);
    return 0;
}

void bios_destroy(struct Bios *b) { free(b->data); b->data = NULL; }

uint32_t boot(const char *path)
{
    struct Bios bios;
    uint32_t first;

    if (bios_init(&bios, path) != 0) return 0;
    if (bios.size < 4) { bios_destroy(&bios); return 0; }  /* every path */

    first = bios.data[0];
    bios_destroy(&bios);
    return first;
}
```

**What the compiler does for you.** It inserts the constructor call at
the declaration and the destructor call at every exit from the scope —
`return`, `break`, falling off the end, and (unless you built with
`-fno-exceptions`) an exception passing through. It also destroys
members and bases in reverse declaration order, and refuses to compile
a copy once you `= delete` it, which is the part that actually
prevents the double-free.

**What it costs.** Nothing at runtime, and in this case slightly less
than the C version. Compiling a two-early-return RAII function against
the equivalent C `init`/`destroy` function with G++/GCC 13.3.0 at
`-O2`: `.text` was 67 bytes for C++ and 66 for C, neither emitted a
`.gcc_except_table`, and `-fno-exceptions` changed the C++ output not
at all. The C++ version emitted one `call free` that both return paths
jump to; the C version emitted two, one per `ram_destroy` call site.

The real costs are elsewhere. Constructors have no return value, so a
fallible constructor either throws or leaves the object in a
half-built state — the C version's `return -1` has no direct
equivalent, which is why `-fno-exceptions` codebases end up with
`init()` methods and two-phase construction anyway. And the calls are
invisible: `Bios bios(path);` opens a file, reads it, and allocates,
with nothing in the syntax saying so, where `bios_init(&bios, path)`
at least names the event.

### `virtual` functions and the vtable

**What it does.** Marking a member function `virtual` makes the call
go through a table of function pointers attached to the object, so
the version that runs depends on what the object actually is rather
than on what the pointer's type says. The compiler generates the
table, generates the code that installs it, and picks the slot.

**C++**

```cpp
struct Device {
    virtual uint32_t read32(uint32_t off) const = 0;
    virtual void write32(uint32_t off, uint32_t v) = 0;
    virtual ~Device() = default;
};

struct Ram : Device {
    uint8_t *bytes;
    uint32_t read32(uint32_t off) const override {
        uint32_t v;
        __builtin_memcpy(&v, bytes + off, 4);
        return v;
    }
    void write32(uint32_t off, uint32_t v) override {
        __builtin_memcpy(bytes + off, &v, 4);
    }
};

uint32_t bus_read(Device *d, uint32_t off)
{
    return d->read32(off);
}
```

**C99**

```c
struct Device;

struct DeviceOps {
    uint32_t (*read32)(const struct Device *, uint32_t off);
    void     (*write32)(struct Device *, uint32_t off, uint32_t v);
    void     (*destroy)(struct Device *);
};

struct Device {
    const struct DeviceOps *ops;   /* every constructor must set this */
};

struct Ram {
    struct Device base;            /* must be first */
    uint8_t *bytes;
};

static uint32_t ram_read32(const struct Device *d, uint32_t off)
{
    const struct Ram *r = (const struct Ram *)d;   /* downcast by hand */
    uint32_t v;
    memcpy(&v, r->bytes + off, 4);
    return v;
}

static const struct DeviceOps ram_ops = { ram_read32, ram_write32,
                                          ram_destroy };

void ram_init(struct Ram *r, uint8_t *bytes)
{
    r->base.ops = &ram_ops;    /* forget this line and you crash */
    r->bytes = bytes;
}

uint32_t bus_read(struct Device *d, uint32_t off)
{
    return d->ops->read32(d, off);
}
```

**What the compiler does for you.** It emits one static table per
concrete class, writes the table's address into the object during
construction, converts each call into a load-and-indirect-call at the
right slot index, and passes the object as `this` so the manual
downcast disappears. `override` makes a typo in the signature a
compile error instead of a silently-new function.

**What it costs.** Per object, one pointer. Measured with G++ 13.3.0:
`struct { uint8_t *bytes; }` is 8 bytes, the same struct with a
`virtual ~T() = default;` is 16 — and the hand-rolled C `struct Ram`
above is also 16, because its `ops` pointer is the same 8 bytes. The
vptr is not free, it is just not *extra* relative to the C pattern.

Per call, `-fdump-lang-class` gives the layout for `Ram`: six 8-byte
entries, with the vptr pointing 16 bytes into it.

```
offset  0   offset-to-top (0)
offset  8   &typeinfo for Ram          <- vptr points to offset 16
offset 16   Ram::read32                (slot 0)
offset 24   Ram::write32               (slot 1)
offset 32   Ram::~Ram   complete-object destructor
offset 40   Ram::~Ram   deleting destructor
```

Two destructor slots, not one. `objdump -d` at `-O2` on the call
sites:

```
bus_read:          mov (%rdi),%rax ; jmp *(%rax)        # slot 0, tail call
d->write32(...):   mov (%rdi),%rax ; jmp *0x8(%rax)     # slot 1
delete d:          test %rdi,%rdi ; je ... ;
                   mov (%rdi),%rax ; jmp *0x18(%rax)    # deleting dtor
```

Inside a loop, where it can't tail-call, the body was
`mov (%rbx),%rdi ; mov (%rdi),%rax ; call *(%rax)`. I compiled the
same loop in both languages and diffed the disassembly: the C
function-pointer version and the C++ virtual version are
**byte-for-byte identical**, prologue, loop, and epilogue. So one
extra dependent load per call, and the branch predictor has to guess
an indirect target — the same bill the C pattern hands you.

Devirtualization is where they stop being the same. Calling
`read32` through a `Ram*` rather than a `Device*`, GCC 13.3.0 does
*speculative* devirtualization: it loads the vptr, loads slot 0,
compares that function pointer against `&Ram::read32` (I confirmed the
`R_X86_64_PC32` relocation with `objdump -rd`), and inlines the body
on the match path, falling back to `jmp *%rax` if it misses. Give it
a local object it can see the type of —

```cpp
Spu s{};
Device *d = &s;
return d->read32(off);
```

— and it devirtualizes completely, then constant-folds the whole
function to `xor %eax,%eax ; ret`. The C version cannot be optimized
this way at all: with `struct Ram *` in hand and the type therefore
known, GCC still emitted `mov (%rdi),%rax ; jmp *(%rax)`, because
nothing tells it that `ops` still points at `ram_ops`.

Static size is where C++ costs more. For one abstract base and one
concrete class, the C++ object file contained the 48-byte vtable, a
24-byte `typeinfo` for `Ram`, a 16-byte `typeinfo` for `Device`, and
the mangled name strings `"3Ram"` and `"6Device"` — 101 bytes of
read-only data. `-fno-rtti` drops all of it except the 48-byte vtable,
whose typeinfo slot becomes zero. The hand-rolled C `ram_ops` was 24
bytes and no strings. Deep hierarchies and template-heavy class names
make the name strings the part that grows.

Compile time and readability: the class must be in a header, so the
vtable layout is part of your ABI and adding a virtual function in the
middle of a class renumbers slots and breaks anything not recompiled.
Against that, the C version has three lines that can silently be wrong
— `base` must be the first member, `ops` must be assigned in every
constructor, and the downcast in every handler is unchecked.

### Abstract interfaces / pure virtual functions

**What it does.** `= 0` on a virtual function means "no
implementation here; a derived class must supply one." A class made
entirely of those is an interface: a contract with no data and no
code, which the compiler enforces by refusing to let you instantiate
anything that hasn't filled it in.

**C++**

```cpp
struct Device {
    virtual const char *name() const = 0;
    virtual uint32_t read32(uint32_t off) = 0;
    virtual void write32(uint32_t off, uint32_t v) = 0;
    virtual ~Device() = default;
};

struct Bus {
    std::vector<std::unique_ptr<Device>> devices;
    void attach(std::unique_ptr<Device> d) {
        devices.push_back(std::move(d));
    }
};

/* written later, possibly in another library */
struct Timer : Device {
    uint32_t counter = 0;
    const char *name() const override { return "timer"; }
    uint32_t read32(uint32_t) override { return counter; }
    void write32(uint32_t, uint32_t v) override { counter = v; }
};
```

**C99**

```c
/* the interface: exactly Linux's struct file_operations shape */
struct DeviceOps {
    const char *name;
    uint32_t (*read32)(void *self, uint32_t off);
    void     (*write32)(void *self, uint32_t off, uint32_t v);
    void     (*destroy)(void *self);
};

struct Attachment {
    const struct DeviceOps *ops;
    void *self;                     /* like file->private_data */
};

/* written later, possibly in a loadable module */
struct Timer { uint32_t counter; };

static uint32_t timer_read32(void *self, uint32_t off)
{
    (void)off;
    return ((struct Timer *)self)->counter;
}
static void timer_write32(void *self, uint32_t off, uint32_t v)
{
    (void)off;
    ((struct Timer *)self)->counter = v;
}
static void timer_destroy(void *self) { free(self); }

const struct DeviceOps timer_ops = {
    "timer", timer_read32, timer_write32, timer_destroy
};

/* call site */
a->ops->write32(a->self, 0, 7);
```

**What the compiler does for you.** It checks completeness — a
`Timer` missing `write32` fails to compile, and a `Device` cannot be
instantiated at all. It fills unimplemented slots with
`__cxa_pure_virtual` so calling one aborts instead of jumping into
garbage. And it keeps the "which implementation" pointer inside the
object, so there is one pointer to pass around rather than two.

**What it costs.** Runtime, slightly less than the C99 version.
`ops` and `self` as separate fields is a fat pointer, and GCC 13.3.0
at `-O2` compiled `a->ops->read32(a->self, off)` to four loads plus a
register move before the indirect jump, against the C++ interface's
single `mov (%rdi),%rax`. Storing `struct Device base` as the first
member instead of a `void *self` closes that gap and gives the layout
the previous section measured, at the price of the manual downcast in
every handler.

What C99 genuinely can't do is check the contract. Leave a field out
of a `DeviceOps` initializer and you get a null pointer, called at
runtime, in a driver written months later. Designated initializers
(C99) at least let you name the fields, and a
`_Static_assert`-style check isn't available until C11.

This is the case where `virtual` earns its keep, and it is worth
being precise about why: not "polymorphism," but that the *set of
implementations is open*. `struct file_operations` exists because the
VFS was compiled before your driver was written. If the set is closed
— every opcode the CPU can execute, every MIPS instruction format —
neither pattern is right, and a tag plus a `switch` beats both: it
inlines, it constant-folds, and `-Wswitch` tells you when you add a
case and forget a handler. Reaching for an interface for a closed set
buys nothing and costs the indirect call.

### References (`T&`, `const T&`) vs pointers

**What it does.** A reference is another name for an existing object.
It compiles to a pointer, but it cannot be null, cannot be pointed
somewhere else after it's bound, and needs no `*` or `&` to use.
`const T&` is the standard way to pass a large struct without copying
it.

**C++**

```cpp
struct Registers { uint32_t r[32]; uint32_t hi, lo, pc; };

/* in-out parameter */
void advance(Registers &regs) { regs.pc += 4; }

/* read-only, no copy: 140 bytes stay where they are */
uint32_t sum(const Registers &regs)
{
    uint32_t t = 0;
    for (int i = 0; i < 32; i++) t += regs.r[i];
    return t;
}

/* the trap: drop the '&' and this copies 140 bytes per call */
uint32_t sum_by_value(Registers regs);

int main()
{
    Registers regs{};
    advance(regs);          // looks like a plain call; takes the address
    return static_cast<int>(sum(regs));
}
```

**C99**

```c
struct Registers { uint32_t r[32]; uint32_t hi, lo, pc; };

void advance(struct Registers *regs) { regs->pc += 4; }

uint32_t sum(const struct Registers *regs)
{
    uint32_t t = 0;
    for (int i = 0; i < 32; i++) t += regs->r[i];
    return t;
}

int main(void)
{
    struct Registers regs = { { 0 }, 0, 0, 0 };
    advance(&regs);      /* the '&' is visible, and NULL is possible */
    return (int)sum(&regs);
}
```

**What the compiler does for you.** It takes the address at the call
site, dereferences inside the callee, and drops the null check you
would otherwise have to consider — a reference parameter is a
guarantee of an object, not a promise to check for one. Binding is
also permanent, so a reference can't be accidentally reseated the way
a pointer parameter can.

**What it costs.** Nothing at runtime. With G++ 13.3.0 at `-O2`,
`advance(Registers&)`, `advance_p(Registers*)`, and GCC's C
`advance` all compile to the same one instruction,
`addl $0x4,0x88(%rdi)`. In the mangled name a reference is `R` where
a pointer is `P`, so they are distinct overloads at link time
(`_Z7advanceR9Registers` vs `_Z9advance_pP9Registers`).

The cost is at the call site, and it goes two ways. Reading
`advance(regs)` you cannot tell whether `regs` is being copied,
observed, or mutated — you have to go read the signature, where
`advance(&regs)` says it on the line. And getting it wrong is
expensive: `sizeof(Registers)` is 140, and dropping the `&` from
`const Registers&` made the *caller* do `sub $0x98,%rsp` and nine
`movdqu`/`movups` pairs to copy those 140 bytes, where the
by-reference call was a single `jmp`. That's the "value semantics on
hot structs" problem in one diff.

### Function overloading and name mangling

**What it does.** Two functions may share a name if their parameter
types differ; the compiler picks one from the argument types at the
call site. Because the linker still needs unique symbols, the
compiler encodes the parameter types into the symbol name — that's
mangling.

**C++**

```cpp
struct Bus { uint8_t *ram; };

void write(Bus &b, uint32_t addr, uint8_t v)  { b.ram[addr] = v; }
void write(Bus &b, uint32_t addr, uint16_t v) { memcpy(b.ram+addr, &v, 2); }
void write(Bus &b, uint32_t addr, uint32_t v) { memcpy(b.ram+addr, &v, 4); }

void store_word(Bus &b, uint32_t addr, uint32_t v)
{
    write(b, addr, v);                              // the uint32_t one
    write(b, addr, static_cast<uint8_t>(v));        // the uint8_t one
}
```

**C99**

```c
struct Bus { uint8_t *ram; };

void bus_write8(struct Bus *b, uint32_t addr, uint8_t v)
{
    b->ram[addr] = v;
}
void bus_write16(struct Bus *b, uint32_t addr, uint16_t v)
{
    memcpy(b->ram + addr, &v, 2);
}
void bus_write32(struct Bus *b, uint32_t addr, uint32_t v)
{
    memcpy(b->ram + addr, &v, 4);
}

void store_word(struct Bus *b, uint32_t addr, uint32_t v)
{
    bus_write32(b, addr, v);            /* the width is in the name */
    bus_write8(b, addr, (uint8_t)v);
}
```

C11's `_Generic` can dispatch on type behind one macro name, and
that's what `<tgmath.h>` uses. It is not available in C99 — under
`-std=c99` there is no type-directed dispatch at all, and distinct
names are the whole answer. (GCC's `__builtin_choose_expr` plus
`__builtin_types_compatible_p` gets close, but it's a GNU extension,
not C99.)

**C23**

```c
#include <stdint.h>

struct Bus { uint8_t *ram; };

void bus_write8(struct Bus *b, uint32_t addr, uint8_t v);
void bus_write16(struct Bus *b, uint32_t addr, uint16_t v);
void bus_write32(struct Bus *b, uint32_t addr, uint32_t v);

/* One call-site name; the explicit names still exist and still grep. */
#define bus_write(b, addr, v) _Generic((v), \
        uint8_t:  bus_write8,               \
        uint16_t: bus_write16,              \
        uint32_t: bus_write32)((b), (addr), (v))

void store_word(struct Bus *b, uint32_t addr, uint32_t v)
{
    bus_write(b, addr, v);
    bus_write(b, addr, (uint8_t)v);
}
```

`_Generic` is C11, so this is available to anything modern rather than
being new in C23. It buys the convenience of overloading and keeps what
overloading takes away: `bus_write32` still exists as a name you can
grep, jump to, and set a breakpoint on. What it does not do is *resolve*
— there is no ranking of candidates and no implicit conversions, so the
association list must match a type exactly, which is why the
`(uint8_t)v` cast is still written out. For a bus layer that is arguably
the better behaviour.

**What the compiler does for you.** It does overload resolution:
ranks the candidates by how well each converts the arguments, errors
if two tie, and then encodes the winner's parameter types into the
linker symbol so the three definitions coexist. `nm` on the C++
object gave `_Z5writeR3Busjh`, `_Z5writeR3Busjt`, and
`_Z5writeR3Busjj` — `R3Bus` is `Bus&`, then `j` for `unsigned int`
and `h`/`t`/`j` for the value's type.

**What it costs.** Nothing at runtime; resolution is entirely at
compile time and the three C++ functions and three C functions
produced the same code. What it costs is legibility at the call site
and at the tooling layer. `write(b, addr, v)` doesn't say how many
bytes it writes — you have to know the static type of `v`, and an
implicit conversion can quietly pick a different overload than you
meant, which is exactly the class of bug an emulator's bus layer can
least afford. `bus_write32` says 32 in the name and greps.

Mangling then leaks outward: symbols in a stack trace or a `nm`
listing need demangling, two compilers with different ABIs can't link
each other's objects, and anything a C caller (or a `dlsym`, or a
Python binding) has to find needs `extern "C"` — which turns
mangling off and therefore allows exactly one function of that name.

### `namespace` vs C's prefix convention

**What it does.** A namespace is a named scope for declarations, so
two subsystems can both have a `State` and a `reset` without
colliding. C has no such scope, so the convention is to put the
"namespace" in the identifier: `psx_cpu_reset`.

**C++**

```cpp
namespace psx {
namespace cpu {
    struct State { uint32_t pc; };
    void reset(State &s) { s.pc = 0xbfc00000; }
}
namespace gpu {
    struct State { uint32_t status; };
    void reset(State &s) { s.status = 0; }   // same name, no conflict
}
}

/* file-local, like C's 'static': no external symbol at all */
namespace {
    uint32_t helper(uint32_t x) { return x + 1; }
}

/* callable from C: mangling off, so only one such name may exist */
extern "C" void psx_reset_all(psx::cpu::State *c, psx::gpu::State *g)
{
    psx::cpu::reset(*c);
    psx::gpu::reset(*g);
}
```

**C99**

```c
struct psx_cpu_state { uint32_t pc; };
struct psx_gpu_state { uint32_t status; };

void psx_cpu_reset(struct psx_cpu_state *s) { s->pc = 0xbfc00000u; }
void psx_gpu_reset(struct psx_gpu_state *s) { s->status = 0; }

/* file-local: the prefix convention's one real enforcement mechanism */
static uint32_t helper(uint32_t x) { return x + 1; }

void psx_reset_all(struct psx_cpu_state *c, struct psx_gpu_state *g)
{
    psx_cpu_reset(c);
    psx_gpu_reset(g);
}
```

**What the compiler does for you.** It folds the enclosing namespaces
into the mangled symbol, so the linker sees the qualification whether
or not you wrote a prefix. `nm` on the C++ object above gave
`_ZN3psx3cpu5resetERNS0_5StateE` and `_ZN3psx3gpu5resetERNS0_5StateE`
— `3psx3cpu5reset` is the scope chain, spelled out. It also does
name lookup outward through enclosing namespaces, so inside
`namespace psx` you write `cpu::reset` and outside it you write
`psx::cpu::reset`.

The linkage interaction has three parts worth knowing. An unnamed
namespace gives everything inside it internal linkage — `helper`
came out as `_ZN12_GLOBAL__N_16helperEj` with a lowercase `t` in `nm`,
a local symbol, which is C's `static` with a scope attached. A
namespace is *not* a linkage boundary otherwise: `psx::cpu::reset` is
a global symbol, just a long-named one. And `extern "C"` cuts across
namespaces entirely — it turns mangling off, so the symbol came out
as plain `psx_reset_all` and the namespace it was declared in
contributes nothing. Two `extern "C"` functions with the same name in
different namespaces are a link error.

**What it costs.** Nothing at runtime, nothing measurable at compile
time. The costs are ergonomic: symbols get long and ugly in linker
errors, profilers, and `nm` output; `using namespace` at file scope
reintroduces exactly the collisions the namespace prevented; and
argument-dependent lookup means a function can be found in a
namespace you never named, which is genuinely surprising coming from
C. The C convention has the compensating virtue that
`psx_cpu_reset` is greppable as written and appears identically in
the source, the symbol table, and the backtrace.

### Operator overloading

**What it does.** Defining `operator+` or `operator==` for your type
lets `a + b` and `a == b` call your function. It is named-function
call syntax with the name removed.

**C++**

```cpp
/* a 32-bit MIPS address that must wrap, not widen */
struct Addr {
    uint32_t v;
    Addr operator+(uint32_t off) const { return Addr{v + off}; }
    bool operator==(const Addr &o) const { return v == o.v; }
};

uint32_t next(Addr pc) { return (pc + 4).v; }
bool same(Addr a, Addr b) { return a == b; }
```

**C99**

```c
struct Addr { uint32_t v; };

static struct Addr addr_add(struct Addr a, uint32_t off)
{
    struct Addr r = { a.v + off };
    return r;
}
static bool addr_eq(struct Addr a, struct Addr b) { return a.v == b.v; }

uint32_t next(struct Addr pc) { return addr_add(pc, 4).v; }
bool same(struct Addr a, struct Addr b) { return addr_eq(a, b); }
```

**What the compiler does for you.** Rewrites `pc + 4` into
`pc.operator+(4)`. That is the entire feature.

**What it costs.** Nothing at runtime — GCC and G++ 13.3.0 at `-O2`
both compiled `next` to `lea 0x4(%rdi),%eax ; ret` and `same` to
`cmp ; sete %al ; ret`. The cost is that a symbol like `+` no longer
tells you what runs, and for a wrapper type it can hide a copy or an
allocation that `addr_add(pc, 4)` would at least have named. Worth it
where the operation genuinely *is* arithmetic on a value type and the
notation matches what the hardware manual says; not worth it as a way
to make method calls shorter.

---

## Resources, copying, and errors

### RAII — destructors at scope exit

**What it does.** A destructor is a function the compiler calls
automatically when a variable goes out of scope, on every path out of that
scope: normal fall-through, `return`, `break`, or an exception passing
through. Put the release of a resource in a destructor and the release
becomes the compiler's job rather than yours, so there is no path you can
forget.

**C++**

```cpp
#include <cstdint>
#include <cstdio>
#include <vector>

class File {
public:
    File(const char* path, const char* mode)
        : fp(std::fopen(path, mode)) {}
    ~File() { if (fp) std::fclose(fp); }
    File(const File&) = delete;
    File& operator=(const File&) = delete;
    std::FILE* get() const { return fp; }
private:
    std::FILE* fp;
};

bool load_bios(const char* path, std::vector<std::uint8_t>& out) {
    File f(path, "rb");
    if (!f.get()) return false;                  // early return: still closed
    out.resize(512 * 1024);                      // may throw: still closed
    return std::fread(out.data(), 1, out.size(), f.get()) == out.size();
}
```

**C99**

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BIOS_SIZE (512 * 1024)

int load_bios(const char *path, uint8_t **out)
{
    FILE *fp = NULL;
    uint8_t *buf = NULL;
    int rc = -1;

    fp = fopen(path, "rb");
    if (!fp)
        goto cleanup;

    buf = malloc(BIOS_SIZE);
    if (!buf)
        goto cleanup;

    if (fread(buf, 1, BIOS_SIZE, fp) != BIOS_SIZE)
        goto cleanup;

    *out = buf;
    buf = NULL;                 /* ownership handed to the caller */
    rc = 0;

cleanup:
    free(buf);                  /* free(NULL) is a no-op */
    if (fp)
        fclose(fp);
    return rc;
}
```

No C23 snippet: this is the biggest gap in the list and C23 does not
narrow it. There is no scope-exit mechanism in standard C — GCC and Clang
both offer `__attribute__((cleanup(fn)))`, which really does work and is
what projects like systemd use, but it is not in any C standard. A
`defer` is under discussion for C2y and is not in a shipping compiler. So
`goto cleanup` remains the C answer, and it is the C99 code above
unchanged.

One C23 feature does sidestep this particular example rather than solve
it: `#embed` can paste a file's bytes into an initializer, so a BIOS or
test ROM baked into the binary needs no `fopen`, no `malloc`, and no
cleanup path at all. I could not verify it — neither gcc 13.3 nor clang
18 accepts `#embed` (`invalid preprocessing directive`); it needs gcc 15
or clang 19.

**What the compiler does for you.** It inserts the `fclose` call at every
exit from the scope, including exits you did not write, and it runs
destructors in reverse construction order so a half-built function cleans
up exactly the objects that were finished. The `goto cleanup` idiom is the
same mechanism written by hand, which is why it needs the
initialise-everything-to-NULL prologue and the `buf = NULL` line on the
success path.

**What it costs.** Nothing at runtime in the ordinary case — the
destructor call is the `fclose` you would have written, usually inlined,
and it is emitted once per exit path rather than once per object. What it
costs is a type per resource: the wrapper class, and remembering to delete
the copy operations, because a default-copied `File` would `fclose` the
same handle twice. Two readability costs: the release point is no longer
visible at the release site, and a destructor cannot report failure, so an
error from `fclose` is silently dropped unless you add an explicit
`close()` for the path where you care.

### `std::unique_ptr`

**What it does.** A struct holding one pointer, whose destructor calls
`delete` on it, and which cannot be copied — only moved. It encodes "this
pointer is the owner" in the type, so ownership becomes a compile-time
property instead of a comment in the header.

**C++**

```cpp
#include <cstdint>
#include <memory>

struct Savestate {
    std::uint8_t  ram[2 * 1024 * 1024];
    std::uint32_t pc;
};

std::unique_ptr<Savestate> capture(std::uint32_t pc) {
    auto s = std::make_unique<Savestate>();
    s->pc = pc;
    return s;                       // ownership moves out
}

void run() {
    std::unique_ptr<Savestate> s = capture(0xbfc00000);
    if (s->pc == 0) return;         // freed here
}                                   // and here
```

**C99**

```c
#include <stdint.h>
#include <stdlib.h>

struct Savestate {
    uint8_t  ram[2 * 1024 * 1024];
    uint32_t pc;
};

/* Caller owns the result and must free() it. Says so here; enforced
   by nothing. */
struct Savestate *capture(uint32_t pc)
{
    struct Savestate *s = calloc(1, sizeof *s);
    if (!s)
        return NULL;
    s->pc = pc;
    return s;
}

void run(void)
{
    struct Savestate *s = capture(0xbfc00000);
    if (!s)
        return;
    if (s->pc == 0) {
        free(s);                /* every early return needs this line */
        return;
    }
    free(s);
}
```

**What the compiler does for you.** It places the `free` on every exit
path, and it refuses to compile a second owner: passing a `unique_ptr` by
value requires `std::move` at the call site, so the transfer is visible in
the source and the old variable is left null. The ownership rule that lives
in a comment in the C version becomes a rule the type system checks.

**What it costs.** At `-O2` on this machine, measurably nothing on the
happy path. I compiled two versions of the same function — one with
`new`/`delete` by hand, one with `make_unique` — where the allocated struct
is 4100 bytes and an opaque `use()` is called in between:

- With `-fno-exceptions`: **byte-for-byte identical** disassembly.
- With exceptions on, but `use()` declared `noexcept`: **byte-for-byte
  identical**.
- With exceptions on and `use()` allowed to throw: the function body is the
  same 28 instructions in both (identical instruction multiset; two `mov`s
  are scheduled in a different order). The `unique_ptr` version then adds a
  3-instruction landing pad and a 5-instruction `.cold` block that frees
  the buffer and resumes unwinding.

In section sizes for that third case: manual is 104 bytes of `.text` plus
64 bytes of `.eh_frame`; `unique_ptr` is 116 bytes of `.text`, 21 bytes of
`.text.unlikely`, 20 bytes of `.gcc_except_table`, and 112 bytes of
`.eh_frame`. So the extra ~100 bytes buys the leak-freedom the manual
version does not have — the hand-written `delete` is simply skipped if
`use()` throws. `sizeof(unique_ptr<T>)` is 8, the same as `T*`. The real
cost is compile time: `#include <memory>` alone is 54,804 preprocessed
lines and 0.19 s here, against 810 lines and 0.01 s for
`stdio.h` + `stdlib.h` + `stdint.h` together.

### `std::shared_ptr`

**What it does.** A pointer plus a shared counter; the object is destroyed
when the last `shared_ptr` to it goes away. Use it only when ownership is
genuinely shared and you cannot say which owner outlives the others.

**C++**

```cpp
#include <memory>

struct Texture { unsigned gl_id; ~Texture(); };

std::shared_ptr<Texture> current;

void bind(std::shared_ptr<Texture> t) {
    current = t;        // refcount up here, down when t dies
}
```

**C99**

```c
#include <stdlib.h>

struct Texture {
    unsigned gl_id;
    int      refs;      /* you add this field, and remember to init it to 1 */
};

static struct Texture *current;

static struct Texture *tex_retain(struct Texture *t)
{
    t->refs++;
    return t;
}

static void tex_release(struct Texture *t)
{
    if (t && --t->refs == 0)
        free(t);
}

void bind(struct Texture *t)
{
    struct Texture *old = current;
    current = tex_retain(t);        /* retain before release: t may be old */
    tex_release(old);
}
```

**What the compiler does for you.** It pairs every retain with exactly one
release, including on exception paths, and it keeps the count in a separate
control block so the counted type needs no `refs` field — which is how
`shared_ptr<T>` works for a `T` you did not write. It also stores the
deleter, so freeing works through a base pointer without a virtual
destructor.

**What it costs.** Real and measurable. `sizeof(shared_ptr<T>)` is 16
against 8 for a raw pointer, because it carries both the object pointer and
the control-block pointer. The `bind` above compiles to 249 bytes of code;
the hand-rolled C version compiles to 48. On the count itself, libstdc++
here does not emit an unconditional atomic — it emits *both* paths and
branches on whether the process has threads: a plain
`addl $0x1,0x8(%rbx)` when single-threaded, and `lock addl $0x1,0x8(%rbx)`
once a thread exists, with `lock xadd` on release. So a single-threaded
emulator pays a well-predicted branch and a normal increment, and the
locked version (tens of cycles, and a cache-line bounce when two threads
touch the same count) only appears once you actually spawn one. There is
also a correctness cost with no C analogue: cycles never free, so a
back-pointer has to be a `weak_ptr`.

### Exceptions

**What it does.** A second return path. `throw` transfers control to the
nearest enclosing `catch` that matches the thrown type, running the
destructors of every local object in every frame it leaves on the way. It
exists mainly because constructors have no return value, so it is the only
way a constructor can report that it failed.

**C++**

```cpp
#include <cstdint>
#include <fstream>
#include <stdexcept>
#include <vector>

struct Bios {
    std::vector<std::uint8_t> rom;

    explicit Bios(const char* path) : rom(512 * 1024) {
        std::ifstream f(path, std::ios::binary);
        if (!f) throw std::runtime_error("BIOS not found");
        f.read(reinterpret_cast<char*>(rom.data()),
               static_cast<std::streamsize>(rom.size()));
        if (f.gcount() != static_cast<std::streamsize>(rom.size()))
            throw std::runtime_error("BIOS wrong size");
    }
};

int boot(const char* path) {
    try {
        Bios bios(path);        // either fully constructed, or never existed
        return bios.rom[0];
    } catch (const std::exception& e) {
        (void)e.what();
        return -1;
    }
}
```

**C99**

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BIOS_SIZE (512 * 1024)

enum bios_err { BIOS_OK, BIOS_NOT_FOUND, BIOS_WRONG_SIZE, BIOS_NO_MEM };

struct Bios { uint8_t *rom; };

/* Two-phase init: the struct exists in an invalid state until this
   returns BIOS_OK, and every caller has to know that. */
enum bios_err bios_init(struct Bios *b, const char *path)
{
    FILE *fp;

    b->rom = NULL;
    fp = fopen(path, "rb");
    if (!fp)
        return BIOS_NOT_FOUND;

    b->rom = malloc(BIOS_SIZE);
    if (!b->rom) {
        fclose(fp);
        return BIOS_NO_MEM;
    }

    if (fread(b->rom, 1, BIOS_SIZE, fp) != BIOS_SIZE) {
        free(b->rom);
        b->rom = NULL;
        fclose(fp);
        return BIOS_WRONG_SIZE;
    }

    fclose(fp);
    return BIOS_OK;
}

int boot(const char *path)
{
    struct Bios b;
    int first;

    if (bios_init(&b, path) != BIOS_OK)
        return -1;
    first = b.rom[0];
    free(b.rom);
    return first;
}
```

**C99, the `setjmp` variant.** The other C answer, and the one that looks
closest to exceptions. Note that the cleanup before each `throw_bios` is
hand-written — that is the part `longjmp` cannot do for you:

```c
#include <setjmp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static jmp_buf    g_bail;
static const char *g_reason;

static void throw_bios(const char *why)
{
    g_reason = why;
    longjmp(g_bail, 1);
}

static uint8_t *load_or_throw(const char *path)
{
    uint8_t *rom;
    FILE *fp = fopen(path, "rb");

    if (!fp)
        throw_bios("BIOS not found");

    rom = malloc(512 * 1024);
    if (!rom) {
        fclose(fp);
        throw_bios("out of memory");
    }
    if (fread(rom, 1, 512 * 1024, fp) != 512 * 1024) {
        fclose(fp);
        free(rom);              /* you unwind by hand before every throw */
        throw_bios("BIOS wrong size");
    }
    fclose(fp);
    return rom;
}

int boot(const char *path)
{
    uint8_t *rom;
    int first;

    if (setjmp(g_bail) != 0) {  /* the "catch" */
        (void)g_reason;
        return -1;
    }
    rom = load_or_throw(path);
    first = rom[0];
    free(rom);
    return first;
}
```

**Why `longjmp` cannot replace exceptions in C++.** Not a style
preference — it does not run destructors, and jumping over a frame that
owns anything is undefined behaviour. Demonstrated rather than asserted:

```cpp
struct Framebuffer {
    Framebuffer()  { std::puts("  framebuffer acquired"); }
    ~Framebuffer() { std::puts("  framebuffer RELEASED"); }
};
static void inner_longjmp() { Framebuffer fb; longjmp(bail, 1); }
static void inner_throw()   { Framebuffer fb; throw 1; }
```

Output, `g++ -O2`:

```
longjmp path:
  framebuffer acquired
  longjmp now
throw path:
  framebuffer acquired
  throw now
  framebuffer RELEASED
```

`framebuffer RELEASED` appears once. The `longjmp` path leaked, silently
and with no diagnostic. Three further gaps: there is no type matching, so
you hand-roll an integer tag and lose `catch (Base&)`; `jmp_buf` is one
global, so nesting and threading need a linked list in thread-local
storage; and the jump goes *straight* to the handler, whereas C++ stops in
each intervening frame. The draft's section 6 sketches the `Cleanup` list
that closes that last gap — the honest summary is that the sketch is a
reimplementation of the compiler's job, and the compiler's version is
checked.

**What the compiler does for you.** It emits, in sections outside your
code path, a description of every frame: which registers to restore
(`.eh_frame`) and which types each `catch` accepts plus where the cleanup
code lives (`.gcc_except_table`). The instructions on the non-throwing
path are unchanged, which is the "zero-cost" claim and is accurate. It also
guarantees the thing the C version cannot express: an object either
finished construction or never existed, so there is no `BIOS_OK`
convention for callers to get wrong.

**What it costs.** The draft's "5–15% of a binary, and `-fno-exceptions`
removes the tables" needs replacing on both halves. What I measured, on
`emu.cpp` — a 370-line PS1-shaped emulator core (unique_ptr-owned bus
devices behind a virtual interface, `vector`/`string`/`map` savestate
serialisation, an `ifstream` BIOS loader, a `switch` dispatch loop) whose
throw sites go through a `FAIL()` macro so the *same source* builds both
ways and both binaries produce identical output. Toolchain: g++ (Ubuntu
13.3.0-6ubuntu2~24.04.1) 13.3.0, target `x86_64-linux-gnu`, binutils 2.42,
dynamically linked against libstdc++.

`-O2`, `size(1)` and `readelf -S`:

| | exceptions | `-fno-exceptions` | delta |
|---|---|---|---|
| `size` text | 40162 | 35786 | −4376 (**−10.9%**) |
| `size` data | 1920 | 1776 | −144 |
| `.gcc_except_table` | 564 | absent | −564 |
| `.eh_frame` | 3508 | 3100 | −408 |
| `.eh_frame_hdr` | 572 | 500 | −72 |
| file bytes | 66792 | 55224 | −11568 |

Three things that changes. First, the total is about **11% at `-O2` and
15% at `-Os`** (28095 → 23922 text), so the 5–15% range is roughly right
at the top end — but only for a codebase this container-heavy, and it
grows as the code shrinks, because the tables stay about the same size
while the code around them gets smaller. That is the real reason the
embedded argument bites.

Second, the attribution in the draft is wrong. The **tables alone are
1044 bytes, 2.6%** of the text figure. The other ~3300 bytes are code:
landing pads, the `.cold` cleanup blocks (988 bytes of `.text.unlikely` in
the object file, which disappears entirely without exceptions), and the
throw sites themselves constructing `std::runtime_error`. Calling the cost
"unwind tables" understates where it actually comes from.

Third, and most concretely wrong: **`-fno-exceptions` does not remove
`.eh_frame`.** It only fell from 3508 to 3100 bytes, a 12% reduction,
because x86-64 defaults to `-fasynchronous-unwind-tables` — those tables
are also what backtraces and profilers walk, so they survive. Adding
`-fno-asynchronous-unwind-tables` is what actually removes them:
`.eh_frame` drops to 136 bytes and text to 32366, i.e. 19.4% below the
exceptions-on build. Two separate flags, and the second one costs you
usable stack traces.

Runtime cost on the happy path is nothing. Throwing costs microseconds and
is not easily bounded, since it walks frames twice and decodes tables.
Compile time barely moves: 0.79 s against 0.76 s for this file. The cost
that does not show up in any of these numbers is the one the draft already
names — banning them forces two-phase init, and the C99 column above is
what that looks like.

### Copy constructors and copy assignment

**What it does.** In C++, `b = a` and `Savestate b = a;` call a function
you can write. That lets a type that owns a heap buffer copy the buffer
too, so that two variables holding the same logical value do not share one
allocation.

**C++**

```cpp
#include <cstdint>
#include <cstring>

class Savestate {
public:
    explicit Savestate(std::size_t n)
        : n(n), ram(new std::uint8_t[n]()) {}
    ~Savestate() { delete[] ram; }

    Savestate(const Savestate& o)                   // copy constructor
        : n(o.n), ram(new std::uint8_t[o.n]) {
        std::memcpy(ram, o.ram, n);
    }

    Savestate& operator=(const Savestate& o) {      // copy assignment
        if (this != &o) {
            std::uint8_t* fresh = new std::uint8_t[o.n];
            std::memcpy(fresh, o.ram, o.n);
            delete[] ram;                            // only after new succeeded
            ram = fresh;
            n = o.n;
        }
        return *this;
    }
private:
    std::size_t n;
    std::uint8_t* ram;
};

void demo() {
    Savestate a(2 * 1024 * 1024);
    Savestate b = a;    // copy ctor: b gets its own 2 MiB
    Savestate c(16);
    c = a;              // copy assignment: c's old buffer freed first
    (void)b;
}
```

**C99**

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

struct Savestate {
    size_t   n;
    uint8_t *ram;
};

int savestate_init(struct Savestate *s, size_t n)
{
    s->ram = calloc(1, n);
    if (!s->ram)
        return -1;
    s->n = n;
    return 0;
}

void savestate_fini(struct Savestate *s)
{
    free(s->ram);
    s->ram = NULL;
    s->n = 0;
}

/* The deep copy has to be a named function, and callers have to
   remember to use it instead of `=`. */
int savestate_copy(struct Savestate *dst, const struct Savestate *src)
{
    dst->ram = malloc(src->n);
    if (!dst->ram)
        return -1;
    memcpy(dst->ram, src->ram, src->n);
    dst->n = src->n;
    return 0;
}

void demo(void)
{
    struct Savestate a, b, wrong;

    savestate_init(&a, 2 * 1024 * 1024);
    savestate_copy(&b, &a);     /* what you meant */

    wrong = a;                  /* 16-byte memcpy: two structs, one buffer */
    savestate_fini(&a);
    savestate_fini(&wrong);     /* double free; the compiler said nothing */

    savestate_fini(&b);
}
```

**What the compiler does for you.** It routes every copy — assignment,
passing by value, returning by value, growing a `vector` of these — through
your function, so there is no syntax that produces the `wrong = a` bug. In
C, struct assignment is a `memcpy` of the 16 bytes and always compiles;
there is no way to make `=` mean the deep copy, and no way to make the
shallow one an error.

**What it costs.** This is the direction that runs against C intuition, and
it is the one to be careful about. The C version's `wrong = a` is a
16-byte register copy; the C++ version's `c = a` is a 2 MiB allocation and
memcpy, and both are spelled `=`. Reading C++ as if assignment were cheap
is the single biggest source of accidental cost — a `Registers` struct
passed by value in a dispatch loop is the emulator-shaped version of this.
The defence is not to avoid value semantics but to pass `const T&` where
you meant a reference, and to write `= delete` on the copy operations of
anything that should never be copied, which turns the accident into a
compile error. Correctness cost: copy assignment has to handle
self-assignment and has to allocate before it frees, or a failed
allocation leaves the target destroyed.

### Move semantics and `std::move`

**What it does.** A move constructor and move assignment are overloads the
compiler picks when the source is about to die — a temporary, or something
you marked with `std::move`. They steal the pointer instead of copying the
buffer, then leave the source empty so its destructor does nothing.
`std::move` generates no code; it is a cast that says "treat this as
expendable."

**C++**

```cpp
#include <cstdint>
#include <utility>

class Savestate {
public:
    explicit Savestate(std::size_t n)
        : n(n), ram(new std::uint8_t[n]()) {}
    ~Savestate() { delete[] ram; }

    Savestate(Savestate&& o) noexcept               // move constructor
        : n(o.n), ram(o.ram) {
        o.ram = nullptr;                            // the null-out, generated
        o.n = 0;
    }

    Savestate& operator=(Savestate&& o) noexcept {  // move assignment
        if (this != &o) {
            delete[] ram;
            ram = o.ram; n = o.n;
            o.ram = nullptr; o.n = 0;
        }
        return *this;
    }

    Savestate(const Savestate&) = delete;
    Savestate& operator=(const Savestate&) = delete;
private:
    std::size_t n;
    std::uint8_t* ram;
};

void demo() {
    Savestate live(2 * 1024 * 1024);
    Savestate slot(16);
    slot = std::move(live);     // pointer steal, no 2 MiB copy
}                               // ~live sees ram == nullptr: harmless
```

**C99**

```c
#include <stdint.h>
#include <stdlib.h>

struct Savestate {
    size_t   n;
    uint8_t *ram;
};

static void savestate_fini(struct Savestate *s)
{
    free(s->ram);
    s->ram = NULL;
    s->n = 0;
}

/* C's move: shallow copy, then blank the source -- by hand, every time. */
static void savestate_move(struct Savestate *dst, struct Savestate *src)
{
    savestate_fini(dst);        /* forget this and you leak dst's buffer */
    dst->n   = src->n;
    dst->ram = src->ram;
    src->ram = NULL;            /* forget this and you double-free */
    src->n   = 0;
}

void demo(void)
{
    struct Savestate live = { 0, NULL };
    struct Savestate slot = { 0, NULL };

    live.ram = calloc(1, 2 * 1024 * 1024);
    live.n   = 2 * 1024 * 1024;

    savestate_move(&slot, &live);

    savestate_fini(&slot);
    savestate_fini(&live);      /* safe only because move blanked it */
}
```

**What the compiler does for you.** The C99 function is exactly what the
move constructor does — the point is that C++ calls it for you at every
site where the source is provably expendable: returning a local by value,
pushing a temporary into a `vector`, `vector` reallocating its storage. In
C that shallow-copy-and-blank is a function you must remember to call
instead of `=`, and the `src->ram = NULL` line is load-bearing with nothing
checking it.

**What it costs.** Nothing at runtime — it replaces a copy with a few
pointer stores, and returning a `unique_ptr` or a `vector` by value stops
being expensive. Three costs elsewhere. The type-system surface is large:
rvalue references, and the rule that once you declare a destructor or copy
operation you should think about all five special members. The moved-from
object still exists and must be left in a valid, destructible state, which
is a genuinely new concept coming from C — `live` above is still a live
variable holding `nullptr`, and using it after the move is a bug the
compiler does not catch. And `noexcept` on these is not decoration:
`std::vector` only uses the move path when the move constructor is
`noexcept`, and falls back to copying when it is not.

### `std::optional` and `std::expected`

**What it does.** `std::optional<T>` (C++17) is a `T` plus a bool saying
whether the `T` is there — "a value or nothing." `std::expected<T, E>`
(C++23) is a `T` or an error value of type `E` — "a value or a reason it is
missing." Both put the result in the return type instead of splitting it
across a status return and an out-parameter.

**C++**

```cpp
#include <cstdint>
#include <expected>     // C++23
#include <optional>     // C++17
#include <vector>

enum class LoadError { NotFound, WrongSize, ReadFailed };

std::expected<std::vector<std::uint8_t>, LoadError> load_bios(const char* path);
std::optional<std::uint32_t> peek_word(std::uint32_t addr);

int boot(const char* path) {
    auto bios = load_bios(path);
    if (!bios) return -static_cast<int>(bios.error());
    if (bios->empty()) return -1;

    if (auto w = peek_word(0xbfc00000))
        return static_cast<int>(*w);
    return -1;
}
```

**C99**

```c
#include <stddef.h>
#include <stdint.h>

enum load_error { LOAD_OK, LOAD_NOT_FOUND, LOAD_WRONG_SIZE, LOAD_READ_FAILED };

/* status in the return, payload through a pointer */
enum load_error load_bios(const char *path, uint8_t **out, size_t *out_len);

/* 0 = ok, -1 = unmapped. *out untouched on failure -- by convention. */
int peek_word(uint32_t addr, uint32_t *out);

int boot(const char *path)
{
    uint8_t *rom = NULL;
    size_t   len = 0;
    uint32_t word;
    enum load_error err;

    err = load_bios(path, &rom, &len);
    if (err != LOAD_OK)
        return -(int)err;       /* nothing stops you reading rom[0] here */
    if (len == 0)
        return -1;

    if (peek_word(0xbfc00000, &word) != 0)
        return -1;

    return (int)word;
}
```

**C23**

```c
#include <stddef.h>
#include <stdint.h>

enum load_error : uint8_t { LOAD_OK, LOAD_NOT_FOUND, LOAD_WRONG_SIZE };

[[nodiscard]] enum load_error load_bios(const char *path,
                                        uint8_t **out,
                                        size_t *out_len);

[[nodiscard]] int peek_word(uint32_t addr, uint32_t *out);

void sloppy(const char *path)
{
    uint8_t *rom = nullptr;
    size_t   len = 0;
    load_bios(path, &rom, &len);   /* warning: ignoring return value */
}
```

C23 cannot give you `optional` or `expected` — no templates, so no
value-or-error type — but `[[nodiscard]]` closes the single worst hole in
the C convention, and it is the hole that produces real bugs: silently
dropping the status. Verified, that emits
`warning: ignoring return value of 'load_bios', declared with attribute
'nodiscard' [-Wunused-result]` under plain `-Wall`. `nullptr` also makes
the out-parameter initialisation say what it means. What C23 still cannot
express is the coupling — `word` remains declared-but-unset in scope on
the failure path, and nothing stops you reading it.

**What the compiler does for you.** It couples the value to its validity,
so there is no declared-but-unset `word` sitting in scope waiting to be
read on the error path, and the value comes back *by return* — a
`vector` payload needs no `**` out-parameter and no ownership convention.
Mark the function `[[nodiscard]]` and ignoring the result becomes a
warning, which is the failure mode the C version cannot defend against at
all.

**What it costs.** Space: `optional<T>` is `T` plus a bool plus padding.
Measured here — `optional<uint32_t>` is 8 bytes against 4 for the bare
`uint32_t`, and there is no niche optimisation, so `optional<void*>` costs
16 bytes where a C API gets `NULL` as its sentinel for free.
`expected<vector<uint8_t>, LoadError>` is 32 bytes against 24 for the
`vector` alone; `expected<uint32_t, int>` is 8, the error sharing storage
with the value. Access is a branch you can skip: `*w` on
an empty `optional` is undefined behaviour, not a diagnostic, so it is
`if`-checked discipline just like C, only harder to forget. Nothing extra
at runtime beyond the flag — no allocation, no exception involved.
Portability is the real cost here: `<optional>` needs C++17, and
`<expected>` needs C++23 and a recent library — it compiled here on
libstdc++ 13, but it is the least portable thing in this whole group, and
MSVC and older Clang standard libraries are where it bites. `<expected>` is
cheap to include by C++ standards (8143 preprocessed lines, 0.02 s), well
under `<memory>`.

---

## The standard library and everyday idioms

### `std::vector`

**What it does.** A contiguous array that owns its memory and grows when
you push onto it. Elements live back-to-back like a C array, so indexing
is a load, not a chase; the difference from a C array is that the length
and the capacity travel with the pointer and the memory is freed when the
vector goes out of scope. C++98, though the braced `push_back` below is
C++11.

**C++**

```cpp
#include <cstdint>
#include <string>
#include <vector>

struct Rom {
    std::string path;
    uint32_t size;
};

void scan(std::vector<Rom>& roms)
{
    roms.push_back({"scph1001.bin", 524288});
    roms.push_back({"ridge-racer.cue", 681574400});
    roms.reserve(64);              // one allocation instead of six
    for (const Rom& r : roms)
        (void)r.size;
}
```

**C99**

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

struct Rom { char *path; uint32_t size; };

struct RomList {
    struct Rom *items;
    size_t len, cap;
};

/* returns 0 on success, -1 on allocation failure */
static int romlist_push(struct RomList *l, const char *path, uint32_t size)
{
    if (l->len == l->cap) {
        size_t cap = l->cap ? l->cap * 2 : 8;
        struct Rom *p = realloc(l->items, cap * sizeof *p);
        if (!p) return -1;                 /* old block still valid */
        l->items = p;
        l->cap = cap;
    }
    char *copy = malloc(strlen(path) + 1);
    if (!copy) return -1;
    strcpy(copy, path);
    l->items[l->len].path = copy;
    l->items[l->len].size = size;
    l->len++;
    return 0;
}

static void romlist_free(struct RomList *l)
{
    for (size_t i = 0; i < l->len; i++)
        free(l->items[i].path);
    free(l->items);
    l->items = NULL;
    l->len = l->cap = 0;
}
```

**What the compiler does for you.** It generates the doubling `realloc`,
the element-by-element destruction, and the `free` at scope exit, once per
element type, from one template. It also removes the class of bug where a
`realloc` succeeds and you forgot to write the new pointer back, or fails
and you overwrote the old one — the two lines the C version spends being
careful about `realloc`'s return value.

**What it costs.** Nothing at runtime for indexing or iteration — the
generated code is the same load off a pointer. `sizeof(std::vector<int>)`
is 24 bytes on x86-64 libstdc++ (three pointers), versus the 24 bytes the
hand-rolled struct uses for pointer + len + cap, so no difference there
either. The allocation behaviour is identical, and identically worth
controlling: 64 `push_back`s of `int` into an empty vector cost 7
allocations and 508 bytes of total churn, versus 1 allocation and 256
bytes after `reserve(64)`. The real costs are compile time and reading:
`#include <vector>` alone takes an empty translation unit from 11 ms to
85 ms with `g++ -O2 -c`, and `roms.push_back(r)` can allocate twice —
once for the vector's growth, once for the `std::string` inside `Rom` —
with nothing in the source saying so.

### `std::string`

**What it does.** A byte buffer that owns its memory, knows its length,
and grows on append. It removes the C question "who frees this, and is
there room" from every string operation. C++98; `std::to_string` is
C++11.

**C++**

```cpp
#include <string>

// build "saves/<title>-<slot>.state" from a fixed-width header field
std::string savestate_path(const char header[32], int slot)
{
    std::string title(header, 32);          // may contain no terminator
    title.resize(title.find_last_not_of(' ') + 1);   // trim padding
    return "saves/" + title + "-" + std::to_string(slot) + ".state";
}
```

**C99**

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* caller frees; returns NULL on failure */
static char *savestate_path(const char header[32], int slot)
{
    char title[33];
    memcpy(title, header, 32);          /* not strcpy: no terminator */
    title[32] = '\0';

    size_t n = strlen(title);
    while (n > 0 && title[n - 1] == ' ')
        title[--n] = '\0';

    int need = snprintf(NULL, 0, "saves/%s-%d.state", title, slot);
    if (need < 0) return NULL;

    char *out = malloc((size_t)need + 1);   /* +1 for the terminator */
    if (!out) return NULL;
    snprintf(out, (size_t)need + 1, "saves/%s-%d.state", title, slot);
    return out;
}
```

**What the compiler does for you.** The length is tracked rather than
recomputed, so the four bugs the C version is written to avoid — `strcpy`
off a field with no terminator, forgetting `+1` for the terminator,
believing `snprintf`'s return value is the number of bytes written rather
than the number needed, and leaking on the early-return path — are not
expressible. `std::string` also owns the free, so the "caller frees"
contract in the C comment does not need to exist.

**What it costs.** `sizeof(std::string)` is 32 bytes in libstdc++, of
which 15 characters' worth is an inline buffer — a string of 15 bytes or
fewer does not allocate at all, which covers most of what an emulator
does with paths and register names. Past that it heap-allocates: the
25-character path above is one allocation of 31 bytes. The costs that
matter are that `a = b` is an allocation and a copy where a C programmer
reads a pointer assignment, that `+` on strings builds temporaries, and
that `#include <string>` is the most expensive of the headers I measured
— 127 ms on an otherwise empty TU against 11 ms for nothing and 12 ms
for C99's `<stdio.h>`.

### `std::array` and `std::span`

**What it does.** `std::array<T, N>` is a fixed-size C array that knows
its own size and can be returned, copied, and passed by value like a
struct. `std::span<T>` is a pointer and a length in one object — the
`(ptr, len)` pair you would have passed as two arguments, bundled so
they cannot get out of step. `std::array` is C++11; `std::span` is
C++20.

**C++**

```cpp
#include <array>
#include <cstdint>
#include <span>
#include <vector>

// works for any contiguous run of pixels: an array, a vector, a sub-range
void dither(std::span<uint16_t> line)
{
    for (size_t x = 0; x < line.size(); x++)
        line[x] ^= static_cast<uint16_t>(x & 1);
}

struct Framebuffer {
    std::array<uint16_t, 320 * 240> vram{};

    std::span<uint16_t> scanline(int y)
    {
        return std::span<uint16_t>(vram).subspan(y * 320, 320);
    }
};

// call sites
Framebuffer fb;
dither(fb.scanline(120));
dither(fb.vram);                      // whole array, length deduced
std::vector<uint16_t> v(320);
dither(v);                            // and a vector, same function
```

**C99**

```c
#include <stdint.h>
#include <stddef.h>

/* the length travels separately, and nothing checks that it matches */
static void dither(uint16_t *line, size_t len)
{
    for (size_t x = 0; x < len; x++)
        line[x] ^= (uint16_t)(x & 1);
}

struct Framebuffer { uint16_t vram[320 * 240]; };

/* call sites */
struct Framebuffer fb = { { 0 } };
dither(&fb.vram[120 * 320], 320);
dither(fb.vram, sizeof fb.vram / sizeof fb.vram[0]);
```

**What the compiler does for you.** It carries the length for you and
derives it at the call site, so `sizeof arr / sizeof arr[0]` stops being
something you write — and stops silently becoming `sizeof(ptr)/sizeof(T)`
when the array decays to a parameter. One `dither` now accepts an array,
a vector, and a sub-range, where C99 would either take `(ptr, len)` and
trust you or need three overloads it cannot have.

**What it costs.** Nothing at runtime, and the sizes are what you would
guess: `std::array<uint16_t, 320>` is exactly 640 bytes with no header,
`std::span<uint16_t>` is 16 bytes (pointer + length), and a
statically-sized `std::span<uint16_t, 320>` is 8 bytes because the length
is in the type. Neither is bounds-checked by default — I indexed a
320-element span at 401 under `-O2` and it read out of bounds silently,
exactly like the C version. Compiling with `-D_GLIBCXX_ASSERTIONS` turns
that into `Assertion '__idx < size()' failed` and an abort, which is a
real safety option C99 has no equivalent of, at the price of a compare
and branch per access. Compile time: `<array>` is 42 ms and `<span>` 51
ms on an empty TU. The readability cost is that `std::span` is a
non-owning view, so it dangles exactly as a raw pointer would, and
nothing in the name says so.

### `std::sort`

**What it does.** Sorts a range in place. The comparator is passed as a
type, not as a pointer, so the compiler can see through it and inline it
into the sort. C++98; the lambda comparator is C++11.

**C++**

```cpp
#include <algorithm>
#include <cstdint>
#include <vector>

struct Breakpoint { uint32_t addr; int hits; };

void order(std::vector<Breakpoint>& bps)
{
    std::sort(bps.begin(), bps.end(),
              [](const Breakpoint& a, const Breakpoint& b) {
                  return a.addr < b.addr;     // "is a before b", a bool
              });
}
```

**C99**

```c
#include <stdint.h>
#include <stdlib.h>

struct Breakpoint { uint32_t addr; int hits; };

/* three-way, and the void* casts are unchecked */
static int cmp_bp(const void *pa, const void *pb)
{
    const struct Breakpoint *a = pa;
    const struct Breakpoint *b = pb;
    if (a->addr < b->addr) return -1;
    if (a->addr > b->addr) return 1;
    return 0;
    /* "return (int)(a->addr - b->addr);" is the classic bug:
       unsigned wraparound, and truncation to int */
}

/* call site */
qsort(bps, n, sizeof bps[0], cmp_bp);
```

**What the compiler does for you.** Three things. The comparator takes
typed references, so passing a comparator for the wrong struct is a
compile error rather than a `void*` cast that runs and reads garbage. The
predicate is a `bool` — "does `a` come first" — which cannot be got wrong
the way a three-way `int` can, and the subtraction bug in the comment
above has no equivalent form. And `std::sort` is instantiated with the
comparator's type, so the comparison becomes a `cmp` instruction inside
the sort loop instead of an indirect call, and the element swaps are
typed moves rather than `qsort`'s width-generic byte copying.

**What it costs.** Compile time and code size, in exchange for
measurable speed. The `std::sort` call site in the snippet above compiles
to 1679 bytes of `.text`; the `qsort` one is 239 bytes, because the sort
itself lives in libc rather than in your binary. That difference did not
show up in the whole stripped executable of the benchmark below (14,576
bytes for `std::sort`, 14,480 for `qsort`), but it scales with the number
of distinct element types you sort. `<algorithm>` costs 79 ms on an empty
TU.

**Measured.** 5,000,000 `int`s, the same xorshift64-seeded data in both
programs (verified by both printing the same min and max), timed with
`clock_gettime(CLOCK_MONOTONIC)` around the sort only, 7 runs each,
pinned with `taskset -c 2`:

```
gcc  -std=c99   -O2   qsort        503 ms median (499–516)
g++  -std=c++17 -O2   std::sort    269 ms median (259–275)
```

`std::sort` is 1.87x faster on this machine. Splitting the gap by
compiling `std::sort` twice in one program — once with the lambda, once
called through a `bool (*)(int, int)` chosen at runtime so it cannot be
devirtualized — separates the two causes:

```
g++  -std=c++17 -O2   std::sort + lambda    266 ms median (260–269)
g++  -std=c++17 -O2   std::sort + fn ptr    348 ms median (344–353)
```

So roughly 82 ms of the 235 ms gap is comparator inlining, and the rest
is `std::sort`'s algorithm and typed element moves against `qsort`'s
generic ones. Toolchain: gcc/g++ 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1),
target `x86_64-linux-gnu`, libstdc++ 13, glibc `qsort`, on an Intel Core
i5-12600K.

### `std::map` and `std::unordered_map`

**What it does.** Two associative containers with the same interface.
`std::map` is a balanced binary tree: ordered, O(log n), iterating it
gives you keys in sorted order. `std::unordered_map` is a hash table:
unordered, O(1) average. `std::map` is C++98, `std::unordered_map` is
C++11, and the structured binding below is C++17.

**C++**

```cpp
#include <cstdint>
#include <map>
#include <unordered_map>

struct Breakpoint { int hits; bool enabled; };

std::unordered_map<uint32_t, Breakpoint> bps;   // O(1) lookup, unordered
std::map<uint32_t, Breakpoint> ordered;         // sorted, O(log n)

bool should_break(uint32_t pc)
{
    auto it = bps.find(pc);
    if (it == bps.end())
        return false;
    it->second.hits++;
    return it->second.enabled;
}

// listing breakpoints in address order needs the sorted one
for (const auto& [addr, bp] : ordered)   // C++17 structured binding
    print(addr, bp.hits);
```

**C99**

```c
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

/* open addressing, power-of-two capacity, no deletion, no growth.
   0 is the "empty" key, so address 0 cannot be a breakpoint. */
#define BP_CAP 256

struct Breakpoint { uint32_t addr; int hits; bool enabled; };

static struct Breakpoint bps[BP_CAP];

static size_t bp_slot(uint32_t addr)
{
    uint32_t h = addr * 2654435761u;          /* Knuth multiplicative */
    size_t i = h & (BP_CAP - 1);
    while (bps[i].addr != 0 && bps[i].addr != addr)
        i = (i + 1) & (BP_CAP - 1);           /* linear probe */
    return i;
}

static void bp_insert(uint32_t addr, bool enabled)
{
    size_t i = bp_slot(addr);
    bps[i].addr = addr;
    bps[i].enabled = enabled;
    bps[i].hits = 0;
    /* no load-factor check: fill it past ~70% and probing degrades */
}

static bool should_break(uint32_t pc)
{
    size_t i = bp_slot(pc);
    if (bps[i].addr != pc)
        return false;
    bps[i].hits++;
    return bps[i].enabled;
}
```

**What the compiler does for you.** It supplies deletion, growth,
rehashing, a load-factor policy, and iteration — the four things the C99
version above deliberately does not have, and which are where a
hand-rolled table usually stops being 40 lines. It also removes the
sentinel problem: the C version cannot store address 0, and the day you
need to, the fix is a parallel occupancy array.

**What it costs.** Node allocation and pointer chasing, both of which are
real and both of which the hand-rolled version avoids by being a flat
static array. Counted with a replaced global `operator new`: 64 inserts
into `std::map<uint32_t,int>` are 64 allocations and 2560 bytes — 40
bytes of node for an 8-byte key/value pair, because a libstdc++ tree node
is a colour flag plus three pointers ahead of the payload. 64 inserts
into `unordered_map` are 68 allocations and 2848 bytes (one node each
plus the bucket array as it rehashes). Compile time: `<map>` is 77 ms and
`<unordered_map>` 92 ms on an empty TU, and the map snippet above takes
141 ms to compile against 18 ms for the C99 one.

**Measured.** 64 breakpoints, 100,000,000 lookups with a 1-in-64 hit
rate — the emulator shape, where the answer is almost always "no
breakpoint here." Same program, `g++ -std=c++17 -O2`, 3 runs each,
`taskset -c 2`:

```
std::unordered_map::find     318 ms  (317–325)   3.2  ns / lookup
std::map::find               322 ms  (321–329)   3.2  ns / lookup
hand-rolled open addressing  133 ms  (132–134)   1.33 ns / lookup
linear scan over 64 pairs    196 ms for 10M     19.6  ns / lookup
```

The hand-rolled table is 2.4x faster than `unordered_map` here, and that
is not a libstdc++ defect — it is the flat static array against node
allocation and a bucket indirection. `std::map` ties `unordered_map` at
this size because 64 nodes fit in cache and six comparisons are cheap. A
linear scan is 6x slower than either map and 15x slower than the
hand-rolled table, so it is the wrong thing to do per instruction, though
it is the right thing for a list you touch once per frame.

### Lambdas and `std::function`

**What it does.** A lambda is a function you can write in the middle of
an expression; if it captures variables, the compiler generates a struct
holding them, which is the `void* user_data` argument built for you. Each
lambda has its own unnamed type. `std::function` is a box that can hold
any callable with a given signature, so it is the thing you store in a
struct when the callable's type varies. Both C++11.

**C++**

```cpp
#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>

struct Spu { uint32_t regs[64]; };

struct Region {
    uint32_t base, size;
    std::function<void(uint32_t, uint32_t)> write;   // captures its own state
};

void install(std::vector<Region>& map, Spu& spu)
{
    map.push_back({0x1f801c00, 0x400,
                   [&spu](uint32_t off, uint32_t val) {
                       spu.regs[off / 4] = val;      // spu captured by ref
                   }});
}

// the zero-overhead form: the callable is a template parameter
template <typename Sink>
void replay(const uint32_t* log, std::size_t n, Sink sink)
{
    for (std::size_t i = 0; i < n; i++)
        sink(log[i]);                                // inlined away
}
```

**C99**

```c
#include <stdint.h>
#include <stddef.h>

struct Spu { uint32_t regs[64]; };

struct Region {
    uint32_t base, size;
    void (*write)(uint32_t off, uint32_t val, void *user);
    void *user;                       /* the capture, by hand */
};

static void spu_write(uint32_t off, uint32_t val, void *user)
{
    struct Spu *spu = user;           /* unchecked: any void* compiles */
    spu->regs[off / 4] = val;
}

static void replay(const uint32_t *log, size_t n,
                   void (*sink)(uint32_t, void *), void *user)
{
    for (size_t i = 0; i < n; i++)
        sink(log[i], user);           /* indirect call every iteration */
}
```

**What the compiler does for you.** It writes the context struct, keeps
the callback body next to the code that installs it instead of at file
scope, and types the context — `void *user` will accept any pointer at
all and the cast back inside the callback is unchecked, which is the one
real bug in the C pattern. When the callable is a template parameter
rather than a `std::function`, the call is a direct call to a known body
and gets inlined; nothing in C99 does that for an indirect call.

**What it costs.** `sizeof(std::function<void(uint32_t,uint32_t)>)` is 32
bytes against 16 for a function pointer plus a `void*`, and libstdc++
inline-stores small captures in that space and heap-allocates larger
ones. `<functional>` is 126 ms on an empty TU. The runtime cost of the
call itself I could not measure — see below — but the cost of *type
erasure* is large and measurable: erasing a callable through
`std::function` blocks the inlining that a template parameter allows.

**Measured, calling through it.** 200,000,000 calls of a two-argument
callback that accumulates into captured state, the callback chosen from
`argc` so it cannot be devirtualized, 5 runs, `-O2`, `taskset -c 2`:

```
gcc -std=c99   fn ptr + void* user_data   319 ms median (305–339)
g++ -std=c++17 std::function              313 ms median (310–316)
g++ -std=c++17 fn ptr + void* (in C++)    315 ms median (311–320)
```

All three are about 1.6 ns per call and the run-to-run spread within one
binary (up to 34 ms) is larger than the difference between binaries, so
this benchmark does not support a claim either way: at `-O2` on this
machine an unpredicted indirect call dominates, and `std::function`'s
extra hop through its stored pointer hides behind it.

**Measured, inlining instead.** The same body, called 200,000,000 times
through the `replay` template above — once with the lambda passed
directly, once with the identical lambda erased through a
`std::function`:

```
g++ -std=c++17 -O2  template + lambda         66 ms median (63–67)
g++ -std=c++17 -O2  template + std::function 271 ms median (265–276)
```

4.1x, from the same source-level body, with both loops producing the same
accumulator value. That is the number worth remembering: `std::function`
is not slow to call, it is slow because it prevents the call from
disappearing. The C99 program cannot get the 66 ms version at all without
abandoning the callback and writing the loop body by hand.

### Range-based `for`

**What it does.** `for (const auto& x : c)` walks a container from
beginning to end. There is no index, so there is no off-by-one and no
chance of iterating one container with another's length. C++11.

**C++**

```cpp
#include <cstdint>
#include <string>
#include <vector>

struct Rom { std::string path; uint32_t size; };

uint32_t total_bytes(const std::vector<Rom>& roms)
{
    uint32_t n = 0;
    for (const auto& r : roms)      // no copy: r is a const Rom&
        n += r.size;
    return n;
}

uint32_t total_bytes_slow(const std::vector<Rom>& roms)
{
    uint32_t n = 0;
    for (auto r : roms)             // copies every Rom, so every std::string
        n += r.size;
    return n;
}

void clamp(std::vector<uint16_t>& line)
{
    for (auto& px : line)           // auto& to write through
        px &= 0x7fff;
}
```

**C99**

```c
#include <stdint.h>
#include <stddef.h>

struct Rom { char *path; uint32_t size; };

static uint32_t total_bytes(const struct Rom *roms, size_t n)
{
    uint32_t total = 0;
    for (size_t i = 0; i < n; i++)          /* index, bound, and body */
        total += roms[i].size;
    return total;
}

static void clamp(uint16_t *line, size_t n)
{
    for (size_t i = 0; i < n; i++)
        line[i] &= 0x7fff;
}
```

**What the compiler does for you.** It writes `begin`, `end`, and the
increment, so the bound comes from the container being iterated rather
than from a variable you passed in. The generated code for a vector is
the same pointer walk `-O2` produces from the index loop.

**What it costs.** Nothing at runtime in the `const auto&` and `auto&`
forms. The `auto` form costs a copy of every element, and the copy is
invisible: `total_bytes_slow` above allocates 10 times and 330 bytes over
a 10-element `vector<Rom>`, because copying a `Rom` copies its
`std::string`, while `total_bytes` allocates zero. The nastier version of
the same trap is spelling the element type out for a map:

```cpp
std::map<std::string, int> m;
for (const std::pair<std::string, int>& p : m) { ... }
```

Map elements are `pair<const std::string, int>`, so the written type does
not match, a temporary `pair` is constructed per iteration, and the
reference binds to that. Over 10 elements: 10 allocations, 280 bytes.
Worth knowing that this one is no longer silent — GCC 13 reports it under
plain `-Wall` as `-Wrange-loop-construct` ("loop variable binds to a
temporary constructed from...", with the fix in the note). The `auto`
version has no diagnostic, because copying is what you asked for. The
habit that survives both: `const auto&` unless you are writing, `auto&`
if you are, and `auto` only when you mean to copy.

### `auto`

**What it does.** Tells the compiler to work out a variable's type from
its initializer. C++11 for variables; C++14 adds deduced function return
types; C++20 allows `auto` function parameters. C99 has no equivalent at
all — `typeof` is a GNU extension that WG14 only standardized in C23,
along with C23's own `auto`, and C99's `auto` is the storage-class
keyword nobody wrote.

**C++**

```cpp
std::map<std::string, uint32_t> syms{{"main", 0x80030000}};

auto it = syms.find("main");         // vs map<string,uint32_t>::iterator
if (it != syms.end())
    use(it->second);

auto emit = [](uint32_t w) { return w; };   // type has no name at all

std::vector<Symbol> table{{"main", 0x80030000}};
for (const auto& s : table)          // const Symbol&
    use(s.addr);

auto n = table.size();               // size_t, not int

const Symbol& first = table.front();
auto copy = first;                   // Symbol — auto drops the const&
const auto& ref = first;             // const Symbol&, no copy

std::vector<bool> flags(4);
auto b = flags[0];                   // NOT bool: a proxy reference
bool real = flags[0];                // this is a bool
```

**C99**

```c
#include <stdint.h>
#include <stddef.h>
#include <string.h>

struct Symbol { const char *name; uint32_t addr; };

/* C99 has no auto and no typeof: every type is spelled out */
static const struct Symbol *sym_find(const struct Symbol *table,
                                     size_t n,
                                     const char *name)
{
    for (size_t i = 0; i < n; i++)
        if (strcmp(table[i].name, name) == 0)
            return &table[i];
    return NULL;
}

/* the macro-hygiene case: the type must be a parameter */
#define SWAP(T, a, b) do { T tmp_ = (a); (a) = (b); (b) = tmp_; } while (0)
```

**C23**

```c
#include <stddef.h>
#include <stdint.h>
#include <string.h>

struct Symbol { const char *name; uint32_t addr; };

static const struct Symbol *sym_find(const struct Symbol *table,
                                     size_t n,
                                     const char *name)
{
    for (size_t i = 0; i < n; i++)
        if (strcmp(table[i].name, name) == 0)
            return &table[i];
    return nullptr;
}

/* typeof means the type is no longer a macro parameter */
#define SWAP(a, b) do { typeof(a) t_ = (a); (a) = (b); (b) = t_; } while (0)

uint32_t demo(const struct Symbol *table, size_t n)
{
    auto hit = sym_find(table, n, "main");   /* const struct Symbol * */
    if (!hit) return 0;
    auto addr = hit->addr;                   /* uint32_t */
    uint32_t zero = 0;
    SWAP(addr, zero);
    return zero;
}
```

C23's `auto` and `typeof` close the macro-hygiene gap exactly — `SWAP`
loses its type parameter and reads like the C++ version. What they do not
buy is the reason `auto` matters in C++: there are no unnameable lambda
types, no iterator types, and no `size_t`-vs-`int` deduction traps to
protect you from, because C's types are all short enough to write. So
`auto hit = ...` above is a convenience; `auto it = m.find(k)` in C++ is
load-bearing.

**What the compiler does for you.** It gets the type exactly right,
including the parts you would get wrong. Section 12 covers the headline
cases — unnameable lambda types, iterator types nobody wants to type,
`int i = v.size()` narrowing a `size_t`. Two things worth adding from
actually using it. First, `auto` deduces *by value*, stripping references
and top-level `const`, which is why `auto copy = first;` above is a copy
and why the range-for rule is `const auto&` rather than `auto`. Second,
`auto` is what makes the deduction *visible in one place*: the three
lines `auto copy`, `auto& ref`, `const auto& cref` say copy, mutate,
observe, and they are the whole vocabulary. Writing the type out gives
you the same three choices plus the option of writing a fourth type that
silently converts.

**What it costs.** Nothing at runtime — deduction finishes before any
code is generated, and `auto x = f()` and `T x = f()` for the correct `T`
produce identical output. The cost is that you cannot read the type off
the line, which for `auto it = m.find(k)` is a gain and for
`auto x = compute()` is a loss, and there is no rule that separates them
except judgement. The trap that bit me is the proxy: `auto b = flags[0]`
on a `std::vector<bool>` deduces `std::_Bit_reference`, not `bool`, and
it keeps a pointer into the vector — it works when used immediately and
dangles when stored. `auto` is faithful there; the container is the
problem. Against C99, the honest comparison is that C99's alternative is
not "write the type" but "make the type a macro parameter", as in `SWAP`
above, and C23's `auto` and `typeof` close that specific gap without
closing any of the others, because there are no iterators, lambdas, or
templates on the other side.
