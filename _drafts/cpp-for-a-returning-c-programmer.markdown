---
layout: post
title: "What C++ costs a C programmer" # working title, not final
description: What I learned about C++ features by asking, for each one, what the equivalent C code would be and what using it costs.
tags: [cpp, c, emulator, playstation]
---

## Draft notes — remove before publishing

**My angle.** I wrote C ten years ago, came back to programming with
emulators, and picked C++ for the PlayStation emulator. I don't know C++
well. So for every feature I run into, I want two answers: *what would I
have written in C?* and *what does this cost me?* That's the whole post.
Not a language comparison, not "which should you learn" — a returning C
programmer working out what he's paying for.

**Why an emulator is a good place to ask.** It hits exactly the cases
where the cost question is real rather than academic:

- **Instruction dispatch** — `switch` on opcode vs virtual dispatch vs a
  table of function pointers, in a loop running millions of times a
  second. The honest answer here is often "the C thing is better," which
  is more interesting than "C++ has classes."
- **The bus / memory map** — devices behind one interface. The *open set*
  case, where `virtual` actually earns its keep, unlike the dispatch loop.
- **Value semantics on hot structs** — a `Registers` copy that looks free
  in the source and isn't.
- **RAII** — BIOS files, savestates, SDL handles: the `goto cleanup` I no
  longer write.
- **The subset question** — do I use exceptions in an emulator at all?
  This is where Orthodox C++ stops being an argument I'm reading about and
  becomes a decision I have to make.

**TODO before writing.** Go through the emulator and inventory which of
these features I actually leaned on and where. The examples should come
from my code, not from a list of language features.

**This is probably more than one post.** Candidates that stand alone:
`How C++ exceptions actually work, in C` (section 6 — clearest payoff),
`Casts and object layout` (section 9), `Modern C, C89 to C23` (section
11). Decide later.

**Accuracy TODO.** The ABI-level claims below need checking against real
output before publishing — `objdump -s -j .gcc_except_table`,
`readelf --debug-dump=frames`, and `sizeof` on the multiple-inheritance
example. The numbers (5–15% unwind tables) are secondhand.

---

## 1. Templates

Compile-time code generation. The closest C analogy is a `#define` macro
the compiler expands, except it knows about types.

The C way:

```c
#define MAX(T) T max_##T(T a, T b) { return a > b ? a : b; }
MAX(int)    // generates max_int
MAX(double) // generates max_double
```

The C++ way:

```cpp
template <typename T>
T max(T a, T b) { return a > b ? a : b; }

max(3, 4);      // compiler emits an int version
max(3.0, 4.0);  // and a double version
```

Same idea, one source and N generated functions. Differences that matter:

- **Type deduction.** You don't write `max_int` — the compiler picks `T`
  from the arguments.
- **Real parsing.** The body is parsed and checked, not blind token
  pasting. No `((a)>(b)?(a):(b))` paren paranoia, no double-evaluation
  bugs.
- **Instantiation is lazy.** No machine code exists until you use a given
  `T`. Unused templates cost nothing.

Class templates work the same way — `struct vector<T>` generates a
distinct struct per `T`, which is how you get a growable array of `int`
and of `char*` without `void*` and casts.

Two things that trip up C people:

1. **Templates live in headers.** The compiler needs the full definition
   to generate code at the call site, so the body can't hide in a
   `.c`-style translation unit. That's why C++ libraries are header-heavy.
2. **Errors are enormous.** Failures happen *during* instantiation, so you
   get a stack of "while instantiating..." noise instead of one clean
   line. Read them bottom-up; the root cause is usually last.

Mental model: templates replace both `void*` generics and macro generics,
paid for at compile time instead of runtime.

## 2. The other differences, quickly

**RAII — the big one.** Destructors run automatically at scope exit,
including on early return and exception paths. This replaces
`goto cleanup:`.

```cpp
{
    std::FILE* raw = fopen(...);   // C: must remember fclose on every path
    std::ifstream f("x.txt");      // C++: closed automatically, always
}                                  // destructor fires here
```

Nearly all C++ resource management is a struct whose destructor frees
something. `unique_ptr` is `malloc`/`free` welded together at compile time.

**References.** `int&` is a pointer that can't be null, can't be reseated,
and needs no `*`/`&` at the call site. Used for output params and to avoid
copying large structs (`const Foo&` ≈ `const Foo*` but guaranteed valid).

**Overloading and name mangling.** Functions may share a name if their
parameter types differ, so the linker symbol encodes the types —
`_Z3fooi`, not `foo`. Hence `extern "C" { ... }` around C headers.

**Classes and virtual dispatch.** A `virtual` function adds a hidden
vtable pointer to the object; calls go indirect. It's exactly the "struct
of function pointers" pattern C programmers hand-roll, with the plumbing
generated. Non-virtual methods cost nothing — plain functions with an
implicit `this`.

**Exceptions.** A second return path that unwinds the stack, running
destructors as it goes. Constructors have no return value, so this is how
they report failure. Many codebases ban them (`-fno-exceptions`).

**Value semantics.** Assignment and passing can invoke user code — copy
constructors, copy assignment, move constructors. `a = b` on a
`std::string` is a heap allocation, not a word copy. The biggest source of
hidden cost when reading C++ as if it were C.

**Stricter typing.** `void*` no longer converts implicitly to `T*` (so
`malloc` needs a cast). Enums don't decay to `int` freely. `const` is
enforced harder, and `const` globals have internal linkage.

**Standard library.** `std::vector`, `map`, `string`, `sort`,
`unordered_map` — templates instantiated at compile time, so generally no
slower than the C equivalent you'd write, minus the bugs.

**Gotchas at the C boundary.** `class`, `new`, `template`, `this` are
keywords; struct tags live in the ordinary namespace (no `typedef struct`
dance); designated initializers and VLAs are C-only or restricted;
character literals are `char`, not `int`.

## 3. Virtual dispatch

The hand-rolled C version:

```c
struct Shape;
struct ShapeVTable {
    double (*area)(const struct Shape*);
    void   (*destroy)(struct Shape*);
};

struct Shape {
    const struct ShapeVTable* vt;   /* set by every ctor */
};

struct Circle { struct Shape base; double r; };

static double circle_area(const struct Shape* s) {
    const struct Circle* c = (const struct Circle*)s;   /* downcast by hand */
    return 3.14159 * c->r * c->r;
}
static void circle_destroy(struct Shape* s) { free(s); }

static const struct ShapeVTable circle_vt = { circle_area, circle_destroy };

struct Shape* circle_new(double r) {
    struct Circle* c = malloc(sizeof *c);
    c->base.vt = &circle_vt;    /* forget this line and you crash */
    c->r = r;
    return &c->base;
}

/* call site */
double total = 0;
for (int i = 0; i < n; i++)
    total += shapes[i]->vt->area(shapes[i]);
```

The C++ version — same machine code, plumbing generated:

```cpp
struct Shape {
    virtual double area() const = 0;   // = 0 means no default impl
    virtual ~Shape() = default;        // needed to delete via Shape*
};

struct Circle : Shape {
    double r;
    Circle(double r) : r(r) {}
    double area() const override { return 3.14159 * r * r; }
};

struct Square : Shape {
    double s;
    Square(double s) : s(s) {}
    double area() const override { return s * s; }
};

// call site
std::vector<std::unique_ptr<Shape>> shapes;
shapes.push_back(std::make_unique<Circle>(1.0));
shapes.push_back(std::make_unique<Square>(2.0));

double total = 0;
for (const auto& s : shapes)
    total += s->area();        // compiles to s->vptr->slot0(s)
```

What the compiler did:

- Emitted one static vtable per concrete type, and wrote the vptr into
  every object during construction.
- Passed the object as the implicit `this` — no manual downcast, no cast
  bug.
- Sized `Circle` as vptr + `double`, exactly like the hand-rolled struct.
- Ran `~Circle` via the vtable when `unique_ptr` destroyed it. (Omit
  `virtual ~Shape` and you'd call the wrong destructor — the real footgun.)

`override` is worth using always: it's a compile error if you misspell the
signature and silently create a new function instead of overriding.

**Cost model:** a virtual call is a load of the vptr, a load of the slot,
then an indirect call — unpredictable and not inlinable, same as a
function pointer. Non-virtual methods are direct calls.

### When is that C pattern realistic?

The vtable-struct example above is built backwards from the C++ answer.
Real C code for shapes would be a tag and a switch:

```c
enum Kind { CIRCLE, SQUARE };
struct Shape { enum Kind kind; union { double r; double s; }; };

double area(const struct Shape* sh) {
    switch (sh->kind) {
    case CIRCLE: return 3.14159 * sh->r * sh->r;
    case SQUARE: return sh->s * sh->s;
    }
}
```

Shorter, faster, and the compiler warns if you add a kind and forget a
case. For a **closed set** of types it's the better design in either
language.

The function-pointer pattern shows up in real C when the set of
implementations is **open**:

- `struct file_operations` in the Linux kernel — a driver fills in
  `.read`, `.write`, `.open`, and the VFS calls through it. The kernel was
  compiled before the driver existed.
- `qsort`'s comparator, `atexit` handlers, libcurl's
  `CURLOPT_WRITEFUNCTION`.
- Any plugin / `dlopen` boundary.

The honest use case for `virtual`: **you're writing code that calls into
implementations that don't exist yet.**

> Emulator note: this is the dispatch-loop-vs-bus split. Opcodes are a
> closed set decided at compile time — switch. Bus devices are closer to
> open, and the interface is crossed once per access, not once per
> instruction. TODO: check what I actually did in both places.

## 4. The "C with classes" subset

Two different things get lumped under this label.

**Literal 1980s style** — classes as namespaces, manual `new`/`delete`, no
destructors doing work, deep inheritance, `char*` everywhere. Mostly
legacy, and a bad target: you pay C++'s complexity for none of the safety.

**A deliberately chosen subset** — the defensible position. Google banned
exceptions for over a decade. LLVM disables exceptions and RTTI entirely.
Game engines and embedded shops ban both plus `iostream` and heap-happy
containers.

| Usually kept | Usually dropped |
|---|---|
| RAII / destructors | Exceptions |
| References | RTTI, `dynamic_cast` |
| `std::vector`, `unique_ptr` | Deep inheritance |
| Basic templates | `iostream` |
| `constexpr`, `override` | Heavy metaprogramming, operator overloading |

Almost nobody drops RAII or containers — pure wins over C with no runtime
cost. What gets cut is the stuff with hidden cost, hidden control flow, or
brutal error messages.

**For restricting:** exceptions add invisible control flow and complicate
binary size and real-time behavior; templates explode compile times and
error messages; a codebase where any line might allocate is hard to reason
about; a smaller subset is easier for a team to master.

**Against:** banning exceptions means status codes everywhere — and
constructors can't return one, forcing two-phase init, which defeats RAII.
Refusing templates means `void*` again. Some restrictions are cargo-culted
from 2005 toolchains. Hand-rolled substitutes for banned features are
usually worse than the feature.

**Pragmatic path from C:** take RAII, `unique_ptr`, references,
`vector`/`string`, `override`, `constexpr`, and basic function templates
immediately. Defer template metaprogramming, operator overloading, and
inheritance. Treat exceptions as a codebase-level decision.

## 5. Are exceptions harmful?

Mostly not — "harmful" overstates it. Separating the critiques:

Complaints that hold up:

- **Binary size and toolchain.** Unwind tables are real bytes — commonly
  5–15% of a binary. On a 64KB-flash microcontroller that decides it.
- **Unbounded worst-case latency.** Throwing walks frames and decodes
  tables; the cost isn't easily bounded. Hard real-time and audio
  callbacks can't accept it.
- **Invisible control flow.** Any call can exit early, so every function
  must be correct at every intermediate point. (RAII is the direct answer.)
- **Interop.** Exceptions can't cross a C ABI boundary. A library called
  from C, Python, or a plugin host must catch everything at the edge.

Complaints that don't hold up as well:

- **"They're slow."** Zero-cost implementations mean the non-throwing path
  costs nothing. Status-code returns cost a branch per call, everywhere.
  Exceptions lose only when "failure" is routine — which is why `stoi`
  throwing on bad input is a genuine design mistake and `find` returning
  `end()` is not.
- **"You lose control over errors."** You lose it *differently*. Ignoring
  an error requires effort with exceptions and requires nothing with
  return codes — most real-world C security bugs are unchecked returns.
  `[[nodiscard]]` closes some of the gap.

The structural problem: banning exceptions doesn't give you C's model
back, it gives you a C++ with a hole in it. Constructors have no return
channel, so fallible construction forces two-phase init, and now objects
have an invalid state — precisely what RAII exists to eliminate. You end
up with factory functions returning `optional`/`expected`.

Where the fault line actually is: embedded, real-time, or C-facing ABI →
the case against is strong and largely settled. Application code and
internal services → the mainstream position (Stroustrup's, the
committee's) is that exceptions plus RAII produce fewer error-handling
bugs than status codes. `std::expected` (C++23) is increasingly the middle
path.

## 6. How exceptions are implemented

> Strongest standalone-post candidate.

### What the compiler emits

Two artifacts, in **separate sections, not in your code path**:

1. **Instructions** — unchanged on the non-throwing path. No branch, no
   flag check, no register reserved for "am I in a try block."
2. **Tables** — `.eh_frame` (how to restore registers/SP per frame) and
   `.gcc_except_table` (which type filters this frame catches, where its
   cleanup code lives). Read-only data, touched only when something throws.

Normal execution pays nothing; throwing pays a lot.

### The throw path

```cpp
throw MyError{42};
```

becomes roughly:

```
p = __cxa_allocate_exception(sizeof(MyError));  // has an emergency reserve
MyError::MyError(p, 42);                        // construct in place
__cxa_throw(p, &typeinfo_for_MyError, &MyError::~MyError);  // never returns
```

`__cxa_throw` calls `_Unwind_RaiseException`, which walks the stack
**twice**:

- **Phase 1 — search.** For each frame, call its personality routine with
  `_UA_SEARCH_PHASE`. It reads that frame's `.gcc_except_table`, compares
  the thrown type against catch filters, answers "mine" or "keep going."
  **Nothing is unwound yet.**
- **Phase 2 — cleanup.** Walk again. In each frame with destructors,
  restore registers per the tables and jump to a **landing pad** —
  compiler-generated code that runs destructors for live locals, then
  calls `_Unwind_Resume`. In the handling frame the landing pad runs
  `__cxa_begin_catch`, the `catch` body, then `__cxa_end_catch`.

Two passes so that if no handler exists, phase 1 fails and you get
`std::terminate` with the stack **intact** — the core dump shows the throw
site.

### The C equivalent — this is real history, "SjLj" unwinding

```c
#include <setjmp.h>
#include <stdlib.h>

typedef struct Frame {
    jmp_buf       jb;
    struct Frame* prev;
} Frame;

static _Thread_local Frame* g_handlers;   /* stack of active "try" blocks */

static _Thread_local void* g_exc;
static _Thread_local int   g_exc_type;

#define TRY(f)   do { (f).prev = g_handlers; g_handlers = &(f); } while (0)
#define UNTRY(f) do { g_handlers = (f).prev; } while (0)

_Noreturn void throw_exc(int type, void* obj)
{
    g_exc_type = type;
    g_exc      = obj;

    if (!g_handlers) abort();          /* == std::terminate */

    Frame* f = g_handlers;
    g_handlers = f->prev;
    longjmp(f->jb, 1);                 /* == phase 2 jump to landing pad */
}
```

Usage — `setjmp` returning twice *is* the landing pad:

```c
void caller(void)
{
    Frame f;
    TRY(f);
    if (setjmp(f.jb) == 0) {
        risky();                       /* try block */
        UNTRY(f);
    } else {
        if (g_exc_type == TYPE_MYERROR) {   /* catch block */
            handle(g_exc);
            free(g_exc);
        } else {
            throw_exc(g_exc_type, g_exc);   /* rethrow */
        }
    }
}
```

### The hard part to replicate

The above jumps *straight* to the handler. Real C++ stops in every
intervening frame to run destructors. Emulating that needs a second linked
list:

```c
typedef struct Cleanup {
    void (*fn)(void*);
    void* arg;
    struct Cleanup* prev;
} Cleanup;

static _Thread_local Cleanup* g_cleanups;

#define DEFER(c, f, a) \
    do { (c).fn=(f); (c).arg=(a); (c).prev=g_cleanups; g_cleanups=&(c); } while (0)

static void unwind_to(Cleanup* target)
{
    while (g_cleanups != target) {
        Cleanup* c = g_cleanups;
        g_cleanups = c->prev;
        c->fn(c->arg);
    }
}
```

`throw_exc` must call `unwind_to()` before the `longjmp`, and every
`Frame` must record `g_cleanups` at entry.

| | C++ | C emulation |
|---|---|---|
| Cost at `try` entry | **zero** | `setjmp` — saves registers, writes a node |
| Cost per scope with cleanup | **zero** | one list push/pop per object |
| Type matching | typeinfo, handles inheritance and `catch(Base&)` | hand-rolled int tag |
| Destructor ordering | guaranteed, compiler-verified | you maintain it |
| Cost when throwing | table walk, two passes | one `longjmp` (faster!) |

### Takeaways

- **`try` is free; `throw` is not.** The happy path is identical to code
  with no error handling. That's the "zero-cost" claim, and it's accurate.
- **Throwing is slow in absolute terms** — microseconds. Hence "exceptions
  for exceptional cases" as an engineering rule, not style advice.
- **`-fno-exceptions` removes the tables** — that's the 5–15% size saving.
  It also makes `throw` a compile error and turns any escaping throw into
  `abort`.
- **`longjmp` is not a substitute in C++** — it skips destructors entirely
  and is UB if any frame it jumps over has non-trivial locals.

Inspect the real thing: `objdump -s -j .gcc_except_table`, or
`readelf --debug-dump=frames`. Format is in the Itanium C++ ABI.

## 7. `const` vs `constexpr`

**`const` is about permission, `constexpr` is about timing.**

```cpp
const int a = 5;            // compile-time constant (initializer is one)
const int b = rand();       // legal — runtime value, just immutable
constexpr int c = 5;        // compile-time constant, enforced
constexpr int d = rand();   // COMPILE ERROR
```

Some places require a genuine compile-time constant — array sizes,
template arguments, `case` labels, `static_assert`, bitfield widths:

```cpp
const int n = get_size();
int arr[n];              // error in C++ (this is a C99 VLA)

constexpr int m = 16;
int arr2[m];             // fine
std::array<int, m> a;    // fine — template argument
```

`const int n = 5;` also works there because the initializer happens to be
constant — but you find that out by trying. `constexpr` fails at the
definition instead of at a distant use site.

**`constexpr` on a variable implies `const`. The reverse isn't true.**

`constexpr` functions have no C analogue:

```cpp
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

constexpr int x = factorial(5);   // computed by the compiler; 120 in .rodata
int y = factorial(runtime_val);   // ordinary call at runtime
```

Compare to C's options: a `#define` macro (no type checking, no recursion,
hygiene problems) or an `enum` (integers only). Modern C++ allows loops,
local variables, even allocation — people compute lookup tables and parse
strings at compile time. `consteval` (C++20) *must* run at compile time.

> Emulator note: compile-time lookup tables are directly relevant —
> opcode tables, colour conversion, whatever else I built at startup.

`const`'s other job:

```cpp
struct Buf {
    size_t len() const { return n; }   // promises not to mutate *this
    size_t n;
};
```

That trailing `const` is part of the type — how the compiler knows you can
call `len()` on a `const Buf&`. No C equivalent, and used far more often
than the compile-time role.

Also: at file scope, `const` variables have internal linkage in C++
(unlike C). `inline constexpr` (C++17) gives one shared definition.

| | `const` | `constexpr` |
|---|---|---|
| Means | won't be modified | usable at compile time |
| Initializer | may be runtime | must be constant expression |
| As array size / template arg | only if initializer happens to be constant | always |
| On functions | "doesn't mutate `this`" | "may be evaluated at compile time" |
| Implies the other | no | yes, implies `const` |

## 8. Orthodox C++ and RTTI

> This is the section that got me interested in the first place, because
> it's about *choosing* a subset, which is the situation I'm actually in.

Orthodox C++ is **Branimir Karadžić's** (bgfx author), originally a gist,
still maintained. Acton and Muratori are adjacent in sentiment but not the
source.

### What RTTI actually is

Three things leaning on one runtime structure:

- `typeid(x)` → a `std::type_info` object
- `dynamic_cast<Derived*>(base_ptr)` → checked downcast, null on failure
- exception matching (`catch (Base&)` catching a `Derived`)

Mechanism: every class with virtual functions gets a static `type_info`
emitted, and the vtable holds a pointer to it (slot −1, just above the
function pointers). `dynamic_cast` follows that pointer and walks the
inheritance graph.

### The case against

- **You pay in size whether or not you use it.** Sharp difference from
  exceptions. `type_info` includes the mangled type name as a string, per
  polymorphic class. Deep template hierarchies produce enormous name
  strings. `-fno-rtti` deletes all of it. Part of why it's banned in LLVM.
- **`dynamic_cast` is genuinely slow and unbounded.** No O(1) guarantee.
  For multiple/virtual inheritance the implementation walks the hierarchy,
  and the Itanium ABI compares type *names by string* to stay correct
  across shared library boundaries. Hundreds of cycles. Unusable in a hot
  loop.
- **Usually a design smell.** `if (dynamic_cast<Circle*>(s))` means the
  virtual interface didn't capture what you needed. Branching on concrete
  type means you have a closed set — and a closed set wants a tag and a
  switch.

### What people use instead

LLVM's replacement, which is the C instinct formalized:

```cpp
class Shape {
public:
    enum Kind { SK_Circle, SK_Square };
    Kind getKind() const { return kind; }
private:
    Kind kind;
};

class Circle : public Shape {
public:
    static bool classof(const Shape* s) { return s->getKind() == SK_Circle; }
};

if (auto* c = dyn_cast<Circle>(shape)) { ... }
```

`dyn_cast` is a template that calls `classof` — one integer compare,
inlinable, no runtime tables. A tag switch with syntax.

The other modern answer is `std::variant` + `std::visit`: closed set,
compile-time exhaustiveness, no vtable. Closer to a C tagged union than to
inheritance.

### Where the argument is weaker

- Debuggers and profilers use RTTI; `-fno-rtti` costs introspection
  quality.
- Serialization, plugin registries, and reflection-ish code legitimately
  need runtime type identity, and hand-rolled tags don't compose across
  library boundaries the way `type_info` does.
- `-fno-rtti` with exceptions is awkward — exception matching needs type
  identity, so part of the machinery stays.
- `typeid` on a non-polymorphic type is free (compile-time). The blanket
  ban is coarser than the actual cost model.

### On Orthodox C++ generally

A useful provocation, not a spec. There's no precise definition, which is
the core criticism — viewpoints vary enough that discussion drifts from
facts to beliefs. HN's recurring jab is that nobody can identify the
"Orthodox C++ committee" besides the author. Parts have aged: the gist's
own changelog concedes `constexpr` needed several iterations to become
useful — an admission that "avoid the new thing" isn't durable advice.

Defensible core: don't add complexity a problem doesn't demand; prefer
code a C programmer can read. The overreach (some commenters argue there's
no real use for the STL) is where it stops being engineering.

Reading: the gist itself, LLVM's coding standards (RTTI section, `isa<>`
docs), bgfx source as reference implementation, a4z's skeptical post for
the other side.

## 9. Casts

> Second standalone-post candidate.

### The C intuition, and where it breaks

In C, a pointer cast emits no instructions — it only changes how the
compiler types the bits. In C++, **a pointer cast can change the numeric
address, and can run code.**

### The C baseline: embedding two structs

```c
#include <stddef.h>
#include <stdlib.h>

struct A { int a; };
struct B { int b; };

struct D {
    struct A a;    /* offset 0 */
    struct B b;    /* offset 4 */
    int d;         /* offset 8 */
};
```

```c
struct D* d = malloc(sizeof *d);

struct A* pa = &d->a;    /* d + 0 */
struct B* pb = &d->b;    /* d + 4  ← arithmetic is right there in the source */
```

Going back is `container_of`, straight out of the Linux kernel:

```c
#define container_of(ptr, type, member) \
    ((type*)((char*)(ptr) - offsetof(type, member)))

struct D* back = container_of(pb, struct D, b);   /* pb - 4 */
```

And the bug:

```c
struct B* wrong = (struct B*)d;   /* points at d->a, calls it a B */
wrong->b = 42;                    /* clobbers d->a */
```

The cast compiled fine. **The compiler had all the information needed to
catch this and said nothing** — in C, a pointer cast is an assertion, not
a question.

### The C++ version

```cpp
struct A { int a; };
struct B { int b; };
struct D : A, B { int d; };    // same layout as the C struct above
```

```cpp
D* d = new D;

A* pa = d;                       // implicit, d + 0
B* pb = d;                       // implicit, d + 4  ← compiler emits the add
D* back = static_cast<D*>(pb);   // subtracts 4 — container_of, generated
```

`static_cast` is `&d->b` and `container_of` in one operation, with offsets
looked up rather than typed by hand. **The compiler knows
`offsetof(D, b)` and you don't have to.**

The broken cast now separates from the correct one:

```cpp
B* good = static_cast<B*>(d);        // d + 4, correct
B* bad  = reinterpret_cast<B*>(d);   // d + 0, the C-style bug — spelled out
```

### Where it gets worse than C

Add virtual functions and each subobject needs its own vptr:

```cpp
struct A { int a; virtual ~A() = default; };   // 8 vptr + 4 int + 4 pad = 16
struct B { int b; virtual ~B() = default; };   // 16
struct D : A, B { int d; };                    // 40
```

```
offset  0  ┌────────────────┐
           │ vptr_A         │
           │ a              │
offset 16  ├────────────────┤
           │ vptr_B         │   ← a B* must point HERE
           │ b              │
offset 32  ├────────────────┤
           │ d              │
           └────────────────┘
```

`B* pb = d;` now adds 16 — a number you cannot compute from the source; it
depends on pointer size, alignment, and the ABI. Hand-rolled
`container_of` here means hardcoding an offset that changes when you add a
field to `A`.

### The four casts, in C terms

| C++ | C equivalent | Emits code? |
|---|---|---|
| `static_cast<B*>(d)` | `&d->b` / `container_of` | yes — add/sub offset |
| `reinterpret_cast<B*>(d)` | `(struct B*)d` | no — pure relabel |
| `const_cast<char*>(p)` | `(char*)p` on a `const char*` | no |
| `dynamic_cast<D*>(pa)` | `if (pa->kind == D) container_of(...)` | yes — RTTI lookup |

`reinterpret_cast` is the one that behaves like a C cast, and the one you
should almost never reach for in a class hierarchy. `static_cast` is the
default because it does the arithmetic.

Single inheritance with no virtuals has the base at offset 0, so
`static_cast` emits nothing and behaves exactly like a C cast. That's why
code gets away with C-style casts for years and then breaks the day
someone adds a second base class.

### Why the C-style cast is the real problem

`(T)x` in C++ isn't a fifth cast — it's a *lookup*. The compiler tries
`const_cast`, then `static_cast`, then `static_cast` + `const_cast`, then
`reinterpret_cast`, and takes the first that compiles.

```cpp
B* pb = (B*)d;   // resolves to static_cast — correct, adds 16
```

But if `B` were only forward-declared, the same syntax silently falls
through to `reinterpret_cast` and you get the broken pointer. **Identical
source, different operation, no warning.** That's the argument for the
verbose keywords — plus `grep reinterpret_cast` finds every place you lied
to the compiler.

### Casts that run code

```cpp
std::string s = static_cast<std::string>("hi");  // allocates, copies
```

Nothing in the syntax hints at a heap allocation.

### Practical rules

- `static_cast` for anything the compiler can check — most casts.
- `reinterpret_cast` where you'd have written a C pointer cast for
  reinterpretation. Rare; each deserves a comment.
- `const_cast` almost only at C-API boundaries.
- `dynamic_cast` only when you truly need a runtime check, never in a hot
  loop.
- **For type punning, don't cast at all.** Strict aliasing makes
  `*(float*)&i` UB in both languages. Use `memcpy`, or
  `std::bit_cast<float>(i)` (C++20) — zero instructions, well-defined.

**One line:** in C a pointer cast is a claim about bits; in C++ it's a
request for a conversion, and the compiler needs to know which kind.

> Emulator note: type punning comes up constantly — reading a 32-bit word
> out of a byte array, float/int reinterpretation in the GTE. Check
> whether I wrote `*(uint32_t*)` anywhere, because that's UB, and
> `bit_cast`/`memcpy` is the fix.

## 10. `struct` in C++ vs C

**In C++, `struct` and `class` are the same feature.** The only difference
is the default access level — `struct` members are public, `class` members
are private.

```cpp
struct Foo {          // could say "class Foo" and add "public:"
    int x;
    Foo(int x);       // constructor
    ~Foo();           // destructor
    int get() const;  // member function
    virtual void f(); // virtual function
    static int count; // static member
};
```

So `struct` in C++ means "a type that may have data, functions,
constructors, destructors, base classes, and a vtable." In C it means "a
bag of fields, period."

Convention: `struct` when everything is public and there's no invariant to
protect, `class` when there's encapsulation. Purely stylistic.

Other C-struct habits that change:

```c
typedef struct Foo Foo;   /* C: needed, tags live in a separate namespace */
```

Unnecessary in C++ — `Foo` alone works after `struct Foo { ... };`.

```c
struct Point p = { .x = 1, .y = 2 };   /* C99 designated initializers */
```

Only arrived in C++20, with restrictions: declaration order required, no
nesting shortcuts, no skipping around. Older C++ rejects it outright.

**Portability trap:** `struct` layout in C++ is only guaranteed to match C
for *standard-layout* types — no virtual functions, no mixed access
levels, no base classes with data. Add a single `virtual` and you've added
a vptr, changed `sizeof`, and broken any C code sharing that struct across
the ABI.

## 11. Modern C: C89 → C23

> Third standalone-post candidate. Runs the opposite direction from the
> rest — what C gained while I was away, and how much of my reason to
> reach for C++ it removes.

### Status

C23 is default in GCC 15 (`-std=gnu23`); it's ISO 9899:2024 despite the
name. Clang has partial support via `-std=c23` in Clang 18+. MSVC lags
badly. The Linux kernel is still on `-std=gnu11` — "C23 is the default"
and "C23 is what codebases use" are very different claims. C2y/C29 drafts
are already landing in GCC 15 and Clang 19.

### C99 — changed daily coding most

```c
// comments
int i;                                  // declare anywhere, not just block top
for (int i = 0; i < n; i++) { }         // and in for-init
struct P p = { .x = 1, .y = 2 };        // designated initializers
f((struct P){ .x = 1 });                // compound literals
#include <stdint.h>                     // int32_t, uintptr_t — portable at last
#include <stdbool.h>                    // bool as a macro
inline, restrict, snprintf, long long
struct S { int n; char data[]; };       // flexible array member (no [1] hack)
```

### C11

```c
_Static_assert(sizeof(int) == 4, "nope");
struct S { union { int a; float b; }; };   // anonymous — access as s.a
#define abs(x) _Generic((x), int: absi, double: fabs)(x)   // type dispatch
_Thread_local, _Alignas, <stdatomic.h>
```

`_Generic` is C's answer to overloading, and how `tgmath.h` works.

### C17

Corrections only, nothing to learn.

### C23

```c
nullptr                    // real null pointer constant, not (void*)0
bool, true, false          // keywords now; <stdbool.h> unneeded
constexpr int N = 16;      // yes, really
typeof(x) y = x;           // standardized (was a GNU extension)
auto n = 42;               // type inference — NOT the C89 storage class
enum E : uint8_t { ... };  // fixed underlying type
[[nodiscard]] [[deprecated]] [[fallthrough]] [[maybe_unused]]
0b1010'1010                // binary literals + digit separators
#embed "logo.png"          // file contents as an initializer list
_BitInt(24)                // exact-width integers
unreachable()
```

Plus two cleanups: **K&R function definitions are gone**, and `f()` now
means `f(void)` rather than "unspecified args."

### Convergence — and its limits

C23 took `nullptr`, `constexpr`, `auto`, `[[attributes]]`, `enum : type`
from C++. C++ took C99's designated initializers in C++20. C++ got
`_Static_assert` as `static_assert`.

But the borrowings are shallower than they look:

- **C's `constexpr` applies only to objects, not functions.** No
  compile-time computation. Closer to "a `const` you can use as an array
  size."
- **C's `auto` is type inference for variables only** — no `auto` return
  types, no generic lambdas, because there are no templates to feed it.
- **`_Generic` is not overloading.** It's a compile-time switch on type,
  and it's verbose. Closes maybe 20% of the gap templates close.

The "should I move to C++" calculus genuinely shifted. Much of what C++
offered a C89 programmer — declare-anywhere, `bool`, `inline`, type-safe
null, attributes, static assertions — is now just C. What's left as
C++-only is the structural stuff: RAII, destructors, templates, and value
semantics.

> This is the one that speaks most directly to my own decision: I picked
> C++ for the emulator partly out of a ten-year-old picture of what C is.
> Worth being honest about how much of that picture still holds.

Reading: cppreference's C23 page, and Jens Gustedt's blog — he's on WG14
and wrote *Modern C*, which is free and aimed at exactly this background.

## 12. What's the point of `auto`?

### In C++: mostly not about saving keystrokes

**1. Some types cannot be written down.** Every lambda has a unique,
compiler-generated type with no name:

```cpp
auto cmp = [](int a, int b) { return a > b; };   // no way to spell this type
```

**2. Some types are absurd.**

```cpp
std::map<std::string, std::vector<int>>::const_iterator it = m.begin();
auto it = m.begin();
```

**3. It prevents real bugs — the strongest argument.**

```cpp
std::map<std::string, int> m;
for (const std::pair<std::string, int>& p : m) { ... }   // silently copies!
```

Map elements are `pair<const std::string, int>` — note the `const`. The
written type doesn't match, so a *conversion* happens: a temporary and a
string allocation per iteration, silently. `for (const auto& p : m)` binds
correctly and copies nothing.

Same class of bug with `int i = v.size()` (that's `size_t`, narrowing).
Writing the type explicitly means you can write the *wrong* type; `auto`
gets it right by construction.

**4. Refactoring.** Change a return type from `int` to `int64_t` and every
`auto` caller follows. Explicit ones either break or silently truncate.

**5. Generic code needs it.** In a template you often can't know the type.

### The costs

```cpp
auto x = foo();   // what is x? you must go read foo
```

A real readability loss. The "almost always auto" camp (Herb Sutter) and
the "types are documentation" camp have argued for a decade without
resolution. Google's style guide says use it when it aids readability, not
reflexively.

Two genuine traps:

```cpp
std::vector<bool> v;
auto b = v[0];         // NOT bool — a proxy reference object
auto s = v[0] ? 1 : 0; // works by accident; store it and it can dangle
```

Proxy types (`vector<bool>`, Eigen expression templates) return something
that isn't what it looks like, and `auto` faithfully deduces the proxy.
Also `auto` strips references and `const` — `auto x = obj.getRef();`
copies. Use `auto&` or `const auto&` deliberately.

Middle ground most teams land on: `auto` when the type is obvious from the
right-hand side (`auto p = std::make_unique<Foo>()`), when the type is
unspellable, and always in range-for. Write the type when it's the point
of the line.

### In C23: much weaker

No lambdas, no iterators, no templates — reasons 1, 2, and 5 evaporate.

```c
auto x = 42;   // it's int. you knew that.
```

The actual use is macro hygiene, avoiding double evaluation without
knowing the type:

```c
#define SWAP(a, b) do { auto tmp = (a); (a) = (b); (b) = tmp; } while (0)
```

But `typeof` — also standardized in C23, a GNU extension for decades —
already did that. C's `auto` is largely a consistency feature, and it cost
the C89 storage-class keyword to get. (Harmless: nobody ever wrote
`auto int i;`.)

Evaluating C23 features by payoff, `auto` is near the bottom.
`constexpr`, `nullptr`, `[[nodiscard]]`, and `#embed` earn their place
more clearly.

---

## Existing writing on this, for reference

The C-vs-C++ space is mostly aimed at people choosing a first language,
which isn't this. The narrower, useful work:

- Brush Blog's *C++ for C programmers* — a feature list, flat, from 2010.
- floooh's *Modern C for C++ peeps* — excellent, runs the opposite
  direction.
- The isocpp FAQ — authoritative and dry.

What none of them do is show the C code the compiler writes for you: the
vtable you'd hand-roll, the setjmp-based unwinder, the `container_of` that
`static_cast` generates. That's the part I wanted to understand, and it's
scarce because it needs both the C idiom and the ABI.
