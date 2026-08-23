---
layout: post
title: "Who says to write less C++, and what they actually argue" # working title
description: Reading the people who advocate restricted subsets of C and C++ — Orthodox C++, Dependable C, Casey Muratori — against the people who argue the other way, and checking the claims on both sides.
tags: [cpp, c, emulator, orthodox-cpp, dependable-c]
---

## Draft notes — remove before publishing

Third draft in the set, after `cpp-for-a-returning-c-programmer` (the
essay-shaped material) and `cpp-features-and-their-c99-equivalents` (the
feature reference). This one is the part I couldn't get from reading the
language: **who argues for using less of C++, what they actually say, and
whether the claims hold.**

**Why I went looking.** I picked C++ for the emulator without knowing it
well, and the first thing I hit was not a feature but a question — which
parts am I supposed to use? Orthodox C++ was the first answer I found.
That led to Eskil Steenberg's Dependable C, which does the same thing to C
itself and much harder, and to Casey Muratori, who argues the cost side
with numbers. Then I went looking for the other side, because a draft that
only reads the subsetters is not research, it's shopping.

**Everything here is checked against primary sources.** The gist and the
post, the Itanium ABI document, LLVM's and Google's style guides as they
read now, P0709, Stroustrup's own history papers, the Simula HOPL paper.
Where a claim came from a summary, a caption file, or a commenter, it says
so. Where a widely-repeated claim has no primary source, that is recorded
as a finding rather than quietly dropped.

**It corrected my own drafts in five places.** Worth keeping in mind while
reading — I had the RTTI string-comparison mechanism backwards, the
"unchecked returns are most C security bugs" claim is unsourced, the
`dynamic_cast` cost needed scoping to cross-library casts, my two
attributions to "commenters" were both wrong, and C23 `constexpr` is not
available on clang 18 at all, which undercuts the one place I said C had
caught up cleanly.

**The finding I did not expect.** Both sides of the OOP argument converge
on the expression problem — n types against m operations, and you choose
which direction is painful — and neither side names it. Uncle Bob concedes
the closed-set case in as many words; Muratori generalises it. That is
Wadler 1998, and it settles the question for an emulator on the merits
rather than on speed: a 1994 opcode set is the most closed set imaginable.
If there is one post in this pile, it might be that one.

**TODO.** This is four research reports concatenated, not a post. The
reading lists at the end of each part are the real deliverable for future
me. Decide whether the through-line is the expression problem, or "what I
got wrong and how I found out."


---

## Dependable C — Eskil Steenberg

# Dependable C — source notes

### What it actually is

### Scope, in its own words

The landing page's first sentence: "Dependable C, is an attempt to
document a subset of C for developers who want to write Dependable C."

The framing case is a utility library that a higher-level language will
link against: "What you want is a library written in C. Its fast,
simple, runs everywhere and in a pinch most people can read the code.
But what kind of C do you want it to be written in? You want it to be
written in the plainest possible C, that doesn't require any extensions,
compiler settings, build steps."

The stated priority order is explicit: "The most important feature of
any code is that you can make it compile and run as intended. That's
what Dependable C prioritizes. Not the ergonomics of the programmer, but
how much the user can depend on it working for their use."

It positions itself against dialects rather than as one: "Dependable C
is the opposite of a dialect. It is a C that is trying to be as middle
of the road as possible in order to be understood and implemented as
widely as possible. Think of it as Newscaster C, a neutral, universally
understood, language."

It disclaims being a style guide, and explicitly separates itself from
MISRA on the axis of what is being optimized: "Dependable C is not a
style guide, it does not prescribe formatting, indentation and style. It
simply tries to document what C functionality can be depended on and
how. ... The Misra standard prioritizes safety, where as Dependable C
prioritizes Compatibility. It is entirely possible to adhere both at the
same time."

The one-line summary of the whole project, from the same page: "Very few
people want to write Dependable C, but everyone wishes everyone else
wrote their code in Dependable C."

It also states, twice, that it is not a purity project — that it will
sanction technical UB where practice is uniform: "it therefore high
discourages writing standard compliant code without any UB code"
[sic — the sentence is garbled on the page; from context and from the
"Dependable UB" chapter the intent is that it *encourages* standard,
UB-free code] "However in some very rare occasions, this guide will
highlight where writing code that is technically UB is permitted,
because in practice it is dependable."

### Audience

Two audiences are named on the page. The "About this page" section: "This
page is maintained to chronicle my own understanding of the language, and
as a guide for my employees and anyone who wants to write dependable C."
The "Dependable UB" chapter names a second: "This list is especially
important for people who are implementing the C standard, because while
these things may be UB according to the standard, a lot of code depend on
them."

### Status

Living document, unversioned. The About section: "This website is
perpetually a work in progress and incomplete." There is no version
number, changelog, or date stamp anywhere on the page. Two chapter
headings — C17 and C23 — are present in the navigation and in the
document body with **no content at all** under them; the C23 slot is
followed straight by the VLA article. Several sections end mid-sentence
(the "Alignment" subsection under C11 stops at "In this case for two
integers to be able to be accessed" and then jumps to an unrelated
`quick_exit` macro).

Wayback Machine CDX for `dependablec.org` shows a 404 in May 2024, first
200 in November 2024, and content-digest changes in March 2025, July
2025, January 2026, February 2026, April 2026 and July 2026 — so it is
revised every few months, with no way to cite a specific revision.

The whole site is a single HTML document (~270 KB) with client-side
navigation; there are no separate URLs per chapter, which is why "read
the whole site" and "read the landing page" are the same fetch.

### Who Steenberg is (sourced)

- His own site, quelsolaar.com: "I work as an independent researcher and
  developer trying to be my very own little 'Xerox PARC', 'Lucasfilm
  R&D' or 'Skunk Works'." Projects listed there include the Verse
  network protocol, the game *Love*, *Loq Airou*, *EXO*, and *Unravel*;
  the page lists consulting for Pixar, ILM, Google, EA and Blizzard.
- Dependable C's About section: "I am a long time C developer, and
  represent Sweden in the C standard board. ... I consider myself as an
  expert in writing software in C, Undefined behaviour and I'm proficient
  in the memory model and concurrency model (I would probably rank as one
  of the worlds experts in these two areas, but I still do not want to
  claim to understand them fully...). I would consider myself less
  experienced in 'Modern' versions of the language."
- Independently confirmed: the official WG14 contacts page lists "Memory
  Object Model Study Group Chair : Eskil Steenberg Hald". The same page
  lists "Undefined Behavior Study Group Chair : David Svoboda" and
  "_Optional Study Group Chair : Chris Bazley" — i.e. two of the three
  people credited on the Dependable C UB chapter are WG14 study-group
  chairs.
- The WG14 document log lists papers authored by him: N2769 *Redefining
  Undefined Behavior* (2021), N2859 *break break* (2021), N3176 *A
  proposal for C2Y* (2023), N3243 *A Memory model with Synchronization
  based type aliasing* (2024), N3308 *Draft: Educational Undefined
  Behavior Technical Report* (2024), N3519 *Effective Type in C* (2025),
  N3778 (2026). N3308 and N3519 are the WG14 paper versions of two
  chapters that appear on the Dependable C site.
- His stated relationship to the standard, from the About section: "My
  participation in the wg14 C standard board is for my own education and
  participation in the Memory model and Undefined behaviour study groups.
  ... Because I will never use any of the newer versions of the language,
  and do not recommend their use, I abstain from voting in the languages
  development."
- Talks: "How I program C" (youtube.com/watch?v=443UNeGrFoM, title
  confirmed via the YouTube oEmbed API), "C is All You Need" on the
  Wookash Podcast (zqHdvT-vjA0), and "I've had it with the security
  orthodoxy." at Better Software Conference 2025 (SbeNRICgzTA). I
  confirmed the titles and authorship of all three but did **not** watch
  them, so nothing in this document is attributed to a talk.

### Attribution of the UB chapter

The UB chapter carries its own byline, and is a different genre from the
rest of the site — it reads as committee prose, not as advice. The site
labels it: "This document is an early draft of a technical report written
by the ISO wg14s Undefined behaviour study group." Its acknowledgements:
"This Document was written by Eskil Steenberg Hald. This document is the
result of many invaluable discussions in the Undefined Behavior Study
Group and ISO WG14, so many of its members deserves credit for its
creation. Specifically the author wants to thank David Svoboda, Chris
Bazley, and Martin Uecker for providing feedback, editing, and suggesting
improvements."

The aliasing chapter has a separate and more heavily hedged attribution:
"I owe huge gratitude for the time and efforts of my peers helping me
decipher this, especially Jens Gustedt and Martin Uecker. Still, this is
still only my interpretation, and it is not a document officially
endorsed by the wg14 or the memory model study group."

Worth keeping straight when quoting the site: the UB chapter's authority
is borrowed from a WG14 study group; the rules chapters are one
programmer's guide.

### The rule list

Grouped by theme. Quoted where the wording carries the argument;
paraphrases are marked "(paraphrase)".

### Standard version

- "Dependable C advocates for using a subset of all versions of C.
  Given that C89 is the smallest of the C standards, in practice this
  means a subset of C89."
- Reading C89 alone is not enough, because later standards fixed
  ambiguities and you get the fixed behaviour anyway: "If something is
  unclear in one standard but has been clarified in later standards,
  users tend to get the clarified behaviour even when they set their
  compiler to follow the earlier standard. Given that C89/ANSI C was the
  first version of the language, it is the version of the standard
  written with the least implementation experience, and therefore have
  lots of issues."
- The target is not a compiler flag: "Your code should not require a
  compiler that has a C89 mode, it should be universal. This is why
  Dependable C discourages the use of any deprecated functionality or any
  functionality that clashes with new C features (see 'auto')."
- Rule no. 1, stated as such: "As a general rule, it is good to always
  write standard compliant code unless you have good reason not to do
  it. If there are two ways of doing something, one which is correct,
  and one that isn't, but the results are identical, always do it the
  correct way." The worked example is `'\0'` versus `0` as a string
  terminator: "I always, terminate strings with '\0' instead of 0, not
  because I expect to have problems with using 0 as a null terminator,
  but because it's the correct way to do it and it doesn't cost
  anything to do it right."

### Platform assumptions

Two explicit tiers. "Basic assumptions about Common platforms that are
fair to make" — bytes/char are 8 bits; types are aligned to their size;
source code is ASCII; function pointers are the same size as data
pointers; `int` is at least 32 bits. Followed by: "None of these are
guaranteed by the standard."

"Optional platform assumptions" — pointers are 64 bits; platforms are
little endian; `int` is 32 bits and `short` is 16 bits. "For each
assumption we make, we reduce the dependability of our code."

Separately, on the exotic end: "There are for instance DSPs where bytes
are 32 bit sized. ... There is therefore worth considering these
platforms as platforms you can program for in C, rather then as platforms
that run portable C code. I choose to distinguish between 'exotic' and
'conventional'." Fully portable C across both is called impossible in
practice, for four listed reasons (binary number representation is
platform-defined; source and text I/O need not be ASCII; non-stdio I/O is
platform-specific; no minimum stack or resource guarantee).

### Undefined behaviour

The general rule: "As a rule all UB should be avoided. Thinking that you
know what UB does is a very dangerous thing to do. If there is a way to
avoid UB you should always do so."

The UB chapter's own closing advice (this is the WG14-study-group text):
"developers should interpret this to mean 'Trust the developer not to
initiate UB', rather than 'The developer can trust UB if they know the
underlying implementation and platform'. ... Testing to determine what
observable effect use of a nonportable or erroneous program construct has
on your platform is insufficient cause for assuming the UB will
consistently have the same behavior on all platforms."

Then the deliberate exception list — "Dependable UB", things that are UB
on paper and uniform in practice:

1. **Pointer to the first member of a struct** equals the pointer to the
   struct. "In practice, in all known implementation the pointer to the
   struct is equivalent to the pointer of the first member of the struct,
   and a lot of code depends on this to implement polymorphism." Note the
   asymmetry: "The same could apply for unions, but taking a pointer of a
   member of a union is not dependable."
2. **`[1]` as a flexible array member.** "While this is avoidable, this
   technically UB is dependable."
3. **Replacing standard library functions with macros.** "This practice
   is dependable and using this technique to create debug versions of
   standard library functions, is a good practice."
4. **A program with no `main`** (libraries). "Writing libraries without
   main in them, in C is dependable."
5. **Pointer arithmetic within an allocation.** Quotes 6.5.7.8 and
   concludes: "This is clearly a defect of the standard, and a pointer to
   allocated memory should be treated as if it was an array."
6. **Effective type is cleared at a function boundary.** "A way to
   express this is to say that all memory passing a function barrier has
   its effective type cleared. This is not standard, but is something I
   regard as dependable."
7. **Non-C11 threading.** "any program that uses pthreads (POSIX) are
   technicaly UB. Platform specific threading facilities such as posix
   threads are in practice far more dependable, supported and battle
   tested than C11 threads."

### Initialization

This is the longest opinionated chapter and the one that draws the most
fire. The stated general rule: "The general advice is to use '=' to
assign values directly."

- **Declare at the top of the function only.** "Being able to declare
  anywhere as you can in C99 makes the problem a lot worse. The simple
  solution to this is to always only declare variables at the beginning
  of a scope (C89 style), and only in the function scope. By not ever
  declaring variables in other scopes you also avoid a range of other
  bugs where variables in different scopes having the same name." The
  problem being made worse is that a declaration with an initializer is
  not executed if you `goto` or `switch` past it; two worked examples are
  given.
- **Prefer no braces on arrays.** "The safest way to initialize an array
  is therefore without braces if possible" — declare with a `#define`d
  length and fill with a loop. "Yes it's more verbose but it's fail
  safe." Also warns against `sizeof` on arrays: "In general I advice
  against using sizeof on any array, because they can decay to
  pointers".
- **`char string[1024] = {'\0'};` is not a one-byte operation.** "This
  code does not write a single byte to null terminate a string, it fills
  the entire string with null termination characters making it
  considerably slower than: `char string[1024]; string[0] = '\0';`"
- **NULL is not zero.** "You should not initialize NULL pointers with
  memset!" and, for structs: "`struct my_struct s; memset(&s, 0, sizeof
  s);` Is not a portable way to set pointer members of the struct to
  NULL!" Also: "you should always define NULL as (void *)0" and never use
  `NULL` as a string terminator.
- **No brace initialization of structs at all.** "In general I think that
  using braces to initialize structs are a bad practice, and should never
  be done." Positional initializers are called "incredibly fragile";
  C99 designated initializers are conceded to be "much better, but raises
  the language requirement and results in long lines of code"; the
  recommended form is a bare declaration followed by one assignment per
  member, with the workflow argument that you paste the struct definition
  and edit it.
- **C23 `= {}` is called a trap.** "This is a death-trap. If anyone
  compiles this with a compiler that does not support this feature you
  will get entirely uninitialized memory, without any warnings or error!
  Stay away from this feature, and if possible add tooling to detect
  accidental use of this."
- **Zero initialization is harmful — and the portability argument is
  explicitly the weaker of the two reasons given.** "it is not the main
  reason not to initialize memory with zeros. When you make a mistake you
  want that mistake to be as obvious as possible, and you want it to
  stick out like sore thumb. 0x0 is very common value both for pointers
  and other variables". The worked example is a link-array allocator
  where a missing `next = NULL` is caught by null checks on first use and
  only manifests on reuse: "This is a good example how by mitigating a
  simple bugs, you make more complex bugs significantly harder to find."
  Conclusion: "Essentially I strongly discourage the use of calloc or
  memseting memory to zero at allocation for this reason." The
  recommended alternative is a debug `malloc` wrapper that fills with
  `0xCD`.
- **One exception where `memset` is endorsed:** pre-priming a struct with
  `0xCD` so that the compiler may fold member stores plus padding into one
  wide store. (paraphrase of the worked example; the site's claim is
  three stores become "a single 64 bit write instruction".)
- **Reading uninitialized memory is worse than "garbage".** Trap
  representations, "wobbly values" (the same read twice giving different
  answers because of demand paging), and branch deletion. "Uninitialized
  memory is not a source of entropy."
- **A `memset` that erases a secret can be deleted.** C23's
  `memset_explicit` is mentioned as one fix; a hand-rolled `volatile`
  version is the recommended one.

### Allocation and the standard library

- Use the standard library for two reasons only: "either because of
  portability or intrinsics."
- The endorsed subset is listed verbatim: "malloc realloc free calloc
  (see 'Initialization in C', for more details on calloc); memset memcpy
  memmove; exit abort; assert; Math functions." `printf` is separately
  "dependable although not all features of these functions are".
- "In DEfence Of malloc": "There is a misconception the malloc is slow.
  Memory allocation is slow, because it's a hard problem, but malloc is
  almost always an extremely well-implemented solution to this problem."
  Custom pool allocators are criticized on two grounds — you must predict
  the ceiling, and you cannot give memory back — plus the MMU argument:
  "malloc implementations often have access to hardware facilities like
  the Memory Management Unit (MMU) ... that can solve a lot of memory
  fragmentation issues that can't be solved as well in a custom
  allocators".
- Annex K: "No implementations of Annex K exists. It doesn't get any less
  dependable than that."
- On why the standard library should stay small — the multiple-
  implementations argument again: "Consider a extremely reliable API like
  Curl, zlib, SQLite. If C standard adopted these interfaces ... we would
  invariably end up with far less reliable interfaces, because they would
  not be based on a single implementation."

### Types

- **Endianness:** "All modern architectures are converging on little
  endian. Little endian is simply objectively (yet unintuitively) better.
  We recommend that applications are written with a 'little endian first'
  design." The justification offered is a digit-reading analogy about the
  number 1337, not a hardware argument. (This is the specific passage a
  lobste.rs commenter singled out; see below.)
- **Floats:** `float` and `double` are "dependable". Two cautions: no FPU
  on some embedded targets, and rounding differences between IEEE 754
  implementations mean "floats are not reliable for lockstep
  synchronizations". Equality: "it is only safe == compare floating
  points values that are assigned, not values that have been computed, or
  to compare floating point values to themselves in order to detect a NaN
  state." `isnan` (C11) is "not dependable"; a two-line replacement is
  given.
- **Type sizes:** "I would caution against assuming pointers are and will
  always be 64 bits on modern platforms as there are new platforms that
  enable 128 bit pointers." (This is the *entire* type-size chapter.)
- **Booleans:** see the per-feature table below.
- **Comparison operators:** all dependable, with two caveats — NaN, and
  relational comparison of pointers into different objects: "it is
  undefined to compare less than or greater than comparisons of the two
  pointers do not have the same provenance."
- **Shifts:** "partially dependable". Right-shifting a negative signed
  value is implementation-defined and "therefore not dependable"; a list
  of architectures that do and don't have an arithmetic-shift instruction
  is credited to Aaron Peter Bachmann. Over-shifting: mask the count.
  (The masking example on the page, `x <<= y & (sizof(y) * BITS_IN_BYTE -
  1);`, contains a typo and uses `sizeof(y)` where `sizeof(x)` is
  presumably meant.)

### Naming and keywords

- "Any keyword starting with a _ (underscore) is reserved and should not
  be used."
- Avoid, because later C versions use them: `true`, `false`, `null`,
  `alignas`, `alignof`, `bool`, `constexpr`, `inline`, `nullptr`,
  `static_assert`, `thread_local`, `typeof`, `type_unequal`. (Verbatim
  list. Note `inline` is on it, and `null` lowercase.)
- Avoid because extensions reserve them: `asm`, `fortran`.
- A ~45-item list of C++ keywords which "can be used in Dependable C, if
  possible they are best avoided for clarity", plus C++ identifiers with
  special meaning (`final`, `override`, `import`, `module`, `pre`,
  `post`, …). `class` is absent from the list; a lobste.rs commenter
  noticed.

### C++ interop

The whole chapter, verbatim, is short enough to quote entire: "Dependable
C, encourages C++ compatibility in all interfaces, but does not guarantee
code to be compiled correctly in a C++ compiler. C++ is not a subset of
C, and the differences between the two languages are subtle and often
unintended. Being able to write code that is guaranteed to produce the
same results in both C and C++ requires deep knowledge of both languages
and is not something we recommend. We strongly encourage header files to
be C++ compatible and not contain any functions. We also discourage any
use of C++ keywords."

So: headers C++-compatible and function-free; no promise for
implementation files.

### Warnings

- "There is therefore no way to write C code that is free from warnings.
  An implementation is entirely free to warn the user that they are
  writing C in the first place. Warnings are thus meant to be ignorable."
- `-Werror` as a blanket policy is argued to be self-defeating: "as
  implementations advance and are able to detect more issues, new
  warnings causes builds to break. This in turn causes users to complain
  to the implementors, and implementors are disincentivized from
  providing additional diagnostics. Many or the major C implementations
  like gcc, llvm, and Msvc refrain from adding almost any new warnings
  for this reason."
- Recommendation: curate the list per project, and "We also do recommend
  turning relevant warnings in to errors, during development."

### Per-version verdicts

- **C99.** `inline`: "This keyword has no meaning due to 'AS-IF'."
  Mid-scope declarations: "This feature does not add any new capabilities
  to the language, it simply shifts where things are declared." VLAs:
  "very broken". Designated initializers: "only syntactic sugar that do
  not enable any new functionality." Compound literals: replaceable with
  a variable. `restrict`: "a very useful concept" — the only C99 feature
  given a positive verdict — and a portable `DC_RESTRICT` macro is
  supplied, with the reasoning that "removing the keyword wont alter the
  meaning of the code". Flexible array members: usable, but the
  all-versions form is to place the tail after the struct and cast
  `&t[1]`. Annex K and Annex L ("Analysability"): not dependable.
- **C11.** `threads.h`: "In practice C11 threads are far less dependable
  than POSIX Threads." Alignment: `_Alignof` is argued to be largely
  redundant with `sizeof`. Atomics: see the concurrency chapter — "In
  practice, C11 is not dependable, and only a few implementations
  exists"; mutexes are preferred to atomics as "inherently more portable
  and dependable"; the design critique is that "C11 opted to have the
  atomicity be part of the type. ... In reality Atomics are not types,
  they are operations."
- **C17.** Empty section.
- **C23.** Empty section. Everything the site says about C23 features is
  said elsewhere — in the keyword list, in the `auto` chapter, in the
  NULL chapter, and in the VLA chapter.
- **VLAs** get their own verdict: "It should never have been added to C.
  ... If you can't grantee what `int a[n];` does, then it is effectively
  UB. (VLAs should be added to to Annex J.) ... VLAs are not 'trust the
  compiler', or 'trust the programmer', it's trust no one." Two
  replacements are given: a pre-allocated manual stack, and a fixed
  buffer with a `malloc` fallback above a threshold.

### Aliasing / effective type

A long chapter that is explicitly descriptive, not prescriptive ("it is
not an endorsement of its design"), ending in a recommendation list. The
ones that read as rules:

- "Don't ever use variables as 'memory buffers' that can be written to,
  outside of memcpy and memmove. Don't ever access a declared variable
  with an other type then its declared type."
- "Don't use calloc or memset for struct or pointer initialization.
  (This is probably the most controversial advice on this list.)"
- "Don't ever take a pointer off a member of a union."
- "Any time you need to type prune [sic] ... use a union. (Do not access
  the same memory using a cast pointer.)" — note this is the *opposite*
  of the usual C++-compatible advice to use `memcpy`; the site's reason
  is that "Any reasonable compiler will optimize away the compiler"
  [sic].
- "Don't ever convert an integer in to a pointer."
- "Never use a pointer to a freed object for ANYTHING, including
  comparing it to other pointers."
- "Never use Variable length arrays. ... (so is recursion, unless you
  have set a hard limit on the number of recursions that have been
  thoroughly tested on the target platform)."
- "Do not EVER think you know when its ok to break the rules, because you
  know how your compiler/platform works."

It also concedes the practical position at length: "Many compilers (Like
visual studion) just flat out ignore these rulles ... Many projects (Most
notably the Linux kernel), and security guidelines mandate
no-strict-aliasing, in order to get around the issue entirely. If you are
unsure, or want to be safe, I recommend using these options."

### Non-rule chapters

Two chapters are argument rather than guidance and should be cited as
such if quoted: "Why is C the safest language?" (13 numbered hypotheses
for why security-critical software is disproportionately C, opening from
"In evolutionary terms, it is clear that security critical C projects
have a much higher survival rate than security critical projects written
in any other language"), and an unlabelled collection of aphorisms
("tweets" in the nav), which is where the site's only mention of
`_Generic` lives.

### The C89 argument

### Exact wording

The claim appears once, on the landing page, in this paragraph:

> "C23, and the upcoming C2Y are language versions that have become
> increasingly complex, include many new keywords, flow control, and a
> revised Charter that differs from 'Classic C'. Later versions of C are
> also only supported by two implementations out of the hundreds of C
> implementations available. The Delta between ANSI C and C2Y is arguably
> larger than the Delta between ANSI C and the first version of C++. This
> means that for developers who want to develop, widely portable, and
> compliant, software in Classic C, the latest ISO C standards are a poor
> guide."

Two further sentences in the same paragraph give the second half of the
motive, which is about the *standard as documentation* rather than about
compilers: "Reading earlier versions of standards is also not sufficient,
since they do not include lists of features that have since been
deprecated, or any guide as to what parts of the standard have had poor
implementation support. This is why Dependable C exists."

Note what the sentence does **not** say: it names no implementations,
gives no count for "hundreds", and does not define "supported" (fully?
partially? with which flag?). There is no footnote or citation anywhere
on the page.

### Is the claim about count, exotic targets, or certification?

About **count**, primarily — and the reasoning behind why count matters
is in a separate chapter, "Implementations", which never mentions C23:

> "Most other languages only have one or very few implementations. This
> means you can rely on the implementation's behaviour to not vary
> between platforms. C has numerous implementations and with a very wide
> range of complexity and feature support. Many C implementations have
> bugs, and they mostly manifest when you stretch the language to its
> limits. All basic functionality can be relied on because the most
> idiomatic code is also the most tested code. Compiler developers use
> publicly available code to test their implementations, and therefore a
> more common construct is much more likely to have been rigorously
> tested than an esoteric corner case. By writing code in a syntax that
> you can be sure all compilers have encountered in the past, you
> minimize the chance that you will trigger a bug."

So the mechanism claimed is not "your target lacks C23" but "rare
constructs are less tested, in every implementation, including the two
that do support them."

The same chapter adds a scope argument that is easy to miss and is
probably the strongest form of the position: the implementation set is
not just compilers. "The compiler is only one small part of the larger C
eco-system of implementations. There are Linters, sanitizers, formatters,
debuggers, syntax highlighting, documentation generation tools and many
other tools that implement the language to some degree, and they all
have their own limitations. Ideally you want your code to be able to take
advantage of all these tools, by staying within their limitations."

It is **not** about certification. The word appears exactly once on the
site, in an unrelated passage about re-certification cost discouraging
maintenance ("If every change results in onerous re-certification
processes ... software will not be maintained properly"). MISRA and CERT
are mentioned as guidelines that exist, not as a reason for C89.

Exotic targets are a *separate* axis, and the site is careful about it:
32-bit-byte DSPs are used to argue that fully portable C is not
achievable at all, and then explicitly set aside — "It is perfectly
reasonable to write software that follows the Dependable C guidelines,
but that isn't portable to hardware having smaller pointers than 64
bits." So Dependable C is not embedded-first; embedded is one input to
the "common vs exotic" line, which each project is told to draw for
itself.

### The same argument in his WG14 paper (primary, and sharper)

N3176, *A proposal for C2Y* (2023-11-07, "By: Eskil Steenberg Hald,
Representative of Sweden in the ISO JTC1/SC22/WG14"), makes the
implementation-count argument in normative form, and states the adoption
test he applies to new features. The paper opens with a red-text
disclaimer: "It has become clear to me that the wg14 as it currently
stands are interested in taking the language in a different direction
from what this paper proposes. I consider this proposal DOA, and only
submit it as a record of my work."

Relevant passages:

- "Therefore to use new features that are only implemented in the latest
  versions of some implementations defeats one of the biggest purposes of
  using C. It is not worth breaking compatibility for syntactic
  convenience. The value of being compatible with older implementations
  outweighs the value of the feature."
- The adoption test: "Someone who uses C in order to be portable, will
  only adopt features where it's worth writing two implementations: one
  with the feature and one without the feature for backwards
  compatibility, and then use the pre-processor to select the one
  supported by the C implementation. This places a high bar on new
  features but not an insurmountable one. Any feature that saves the
  developer typing, are obviously out, but features that lets the user
  access hardware features like, bit utilities and _BitInt(N) do make
  sense."
- The fork risk: "By making standard C harder to implement and with fewer
  implementations able to meet the requirements of the standard, while at
  the same time meeting the requirements of the vast majority of C code.
  The wg14 runs the risk of forking the language between ISO C and the
  classic C used by the community."
- On uptake as evidence: "Uptake of new features that have been added in
  the past like _Generic, VLAs, anonymous structs, bounds checking is
  limited too. Features that are added aren't being used, taught, or even
  known by the wider C community."
- Ease of implementation as a feature: "Ease of implementation is an
  under rated feature of C, and it deserves our attention. New platforms
  and hardware designs tend to chose C as the language of choice, because
  of its implementability."
- And the sentence that most directly targets my draft's premise: "For
  C2x several complicated features have been added like new uses of auto,
  nullptr and constexpr that the wg14 has had difficulty giving a
  rationale for the users adopting. They are borrowed from other
  languages where they have features C2x doesnt have and interact with
  systems that C does not have. 'It can have its uses' is not a good
  enough rationale for adding features to C, a language where the key
  feature is its simplicity."

The paper's actual proposal, for the record, is not "freeze C" — it is
"make C2Y a strict subset of C2X" plus a `#version` preprocessor
directive, with the goal that "98% of all existing Iso C compliant files
written in the last 20 years should also be C2Y compliant without any
change whatsoever."

### The direct conflict with my draft

One caution before the table. The site's own framing of the keyword list
is *avoid the identifier*, not *the feature is broken*: the heading is
"Reserved keywords" and the sentence is "The following keywords are used
by later C versions and should therefore be avoided." That is a
name-collision argument — if you use `bool` or `constexpr` as your own
identifier, or you want your C89 code to keep compiling under a C23
compiler, the name is spoken for. It is not, by itself, a critique of
what the C23 feature does. Where a real critique exists I've quoted it.

| Feature (my draft) | Dependable C position | Its stated reason |
|---|---|---|
| `constexpr` objects | **Rejected** — on the avoid-list of "keywords used by later C versions and should therefore be avoided". No dedicated section. | No reason given on the site beyond the list's blanket rationale. In N3176 he names `constexpr` twice: among features "the wg14 has had difficulty giving a rationale for the users adopting", and among "features that misleads the users into thinking that the language is a 'portable assembler' ... such as inline, constexpr, and register, and are in practice nullified by the as-if rule". |
| `static_assert` | **Rejected** — on the same avoid-list (both `static_assert` and `alignas`/`alignof`). No dedicated section, no discussion anywhere. | No reason given beyond the list. Note the site never proposes a replacement, and never mentions the C89 negative-array-size trick. |
| `auto` / `typeof` | **Rejected, with the site's harshest wording for any feature.** "Unfortunately auto has gone from pointless to dangerous in C23. ... Therefore any use of the keyword auto should be considered not dependable." `typeof` is on the avoid-list with no discussion. | Silent meaning change, not verbosity: "if you write the above in older versions of C, you don not need to specify a type at all, and will then be given a variable of type int per default. The above in C89 would make x an int. ... This means that very recent compilers will compile this and an int and even more recent compilers (supporting C23) will no longer warn against this." I.e. `auto x = 0.0;` is `int` in C89 and `double` in C23 — same text, different program. |
| `nullptr` | **Rejected explicitly, by name, outside the keyword list.** "C23 adds nullptr, a third way to define NULL, confusing the situation further. Don't use it, only use (void*)0." | Multiplication of spellings for NULL, on top of a chapter arguing that NULL is already a mess ("NULL has two definitions in C (three in c23)"). N3176 lists `nullptr` with `auto` and `constexpr` as features lacking a user-adoption rationale. |
| `enum : uint8_t` | **Says nothing.** No mention of fixed underlying enum types anywhere on the site; `enum` appears only inside the keyword list. | — (do not infer a position; the general C89-subset rule would exclude it, but the site never discusses it) |
| `unreachable()` | **Mixed, and the two voices differ.** The rules chapters say nothing — it is not in the keyword list, not in the C23 chapter (which is empty), not mentioned as non-dependable. The UB chapter *endorses it on purpose*: "The one exception to this is the `unreachable()` macro. The `unreachable()` macro is the only way for a user to express that a statement can be assumed to never be executed. ... The `unreachable()` macro can therefore not be implemented by the user by producing UB in some way other than the `unreachable()` macro." | The UB chapter's reason is that it is the only *legitimate* way to assert unreachability, and must be distinguished from erroneous UB: "Division by zero is UB, but unlike `unreachable()`, it is assumed to be a user error." Caveat when citing this: the UB chapter is the WG14 study-group draft, describing C as standardized, not the Dependable C subset. It is not an endorsement of using C23. |
| `[[nodiscard]]` | **Says nothing.** No mention of `[[nodiscard]]`, of `[[...]]` attribute syntax, or of unused-return-value diagnostics anywhere on the site. | — (do not infer a position) |
| `_Generic` | **No rule.** Not in the keyword list (it starts with `_`, so the "any keyword starting with a _ is reserved and should not be used" rule covers it by implication, but it is never named as a rule). The only mention on the site is in the aphorism collection: "I'm convinced that the keyword _Generic in C was not invented for programmers to use. It was invented to preoccupy the ISO C wg14, with an endless stream of proposals, arguments and corner cases." | The aphorism gives no technical reason. N3176 gives one, as evidence rather than critique: `_Generic` is cited first in the list of features whose "uptake ... is limited". |

Two more that touch my draft's material even though they weren't on my
list of eight:

- **`bool` / `_Bool`.** Rejected, with the site's most detailed
  reasoning. On the avoid-list, plus a dedicated section: "In fact there
  are good reasons not to use _Bool. First of all it is deprecated and
  replaced by 'bool', and then the keyword 'bool' is likely to clash with
  other definitions of bool. A header file that defines a function that
  returns bool, requires stdbool.h to be included and that means that any
  code that defines their own bool, will have trouble accessing the
  function. We strongly recommend considering the word 'bool' to be
  reserved as well as 'true' and 'false'." The functional argument
  against it is that `_Bool` solves only the `if (x == TRUE)` problem,
  which `if (x)`, `if (x != FALSE)` or `!!x` also solve, and that it is
  not a good *storage* type — the three endorsed storage choices are a
  bit in a larger integer, a byte, or an `int`, with a use-case rule for
  each.
- **`#embed` and `_BitInt`.** My draft flags both as unverifiable on gcc
  13.3. The site says nothing about either. N3176 puts `_BitInt(N)` in
  the *approved* category — one of the "features that lets the user
  access hardware features ... [that] do make sense" — which is the one
  place where his stated test and my draft's interest coincide.

Net for the draft: of the eight, three are rejected by name with a stated
reason (`auto`, `nullptr`, and — with the fullest argument — `bool`), two
are rejected only by inclusion in a keyword list with no argument
(`constexpr`, `static_assert`, plus `typeof`), two get nothing at all
(`enum : uint8_t`, `[[nodiscard]]`), and one is a joke in a sidebar
(`_Generic`). The one my draft treats as the clean win — `constexpr`
objects — is exactly the one where the site's stated objection is the
identifier rather than the semantics, and where the substantive objection
has to be pulled from N3176.

### Where it lands relative to Orthodox C++

Dependable C never mentions Orthodox C++, Branimir Karadžić, or C++
subsetting as a practice. It does discuss C++ twice: the C++
compatibility chapter (headers only, quoted above) and the observation
that C++ derivative languages are C89-shaped — "Many languages have
derived their syntax from C. C++, Java, C#, D, JavaScript, Objective-C to
name a few. Almost all of these languages are based on C89, and have not
incorporated C99 or later features. This means that programmers who
mainly use these languages have difficulty reading code written using the
later versions." That last clause is a *reader*-portability argument for
C89 that has no Orthodox C++ counterpart.

The comparison is other people's, not his. On HN, `aw1621107`: "This is
reminiscent of Orthodox C++ [0], though I think it's perhaps more similar
in goal than intent." And `pjmlp`: "It is kind of ironic, given the
existence of Orthodox C++, and kind of proves the point, that C isn't as
simple as people think, having only read the K&R C book and nothing
else."

Same instinct, different argument, and a different magnitude:

- Orthodox C++ (Karadžić, first published 2016-01-16, updated through
  2025) defines itself as "minimal subset of C++ that improves C, but
  avoids all unnecessary things from so called Modern C++", and gives two
  reasons: "Code base written with Orthodox C++ limitations will be easer
  to understand, simpler, and it will build with older compilers." Its
  avoid-list is *library and runtime* machinery — exceptions, RTTI,
  iostreams, allocating STL, excessive metaprogramming, modules — plus
  "premature adoption of new C++ standards", with a rule of thumb of
  waiting about five years after a standard ships.
- Dependable C's avoid-list is *language* machinery, and its waiting
  period is effectively 35 years. Its primary reason is not
  comprehensibility or build compatibility but implementation and tooling
  coverage plus test coverage of rare constructs — an argument Orthodox
  C++ does not make at all (C++ has few implementations, so it cannot).
- Orthodox C++ keeps a positive core it is trying to reach ("C-like
  C++"); Dependable C's core is a pre-existing standard, so it needs no
  invention, only a documented list of exclusions and of places where the
  standard and practice disagree.

The honest summary is that they share the "the language grew past what I
want to depend on" instinct, and share the older-compilers argument, but
Dependable C's central claim — that the count and diversity of
implementations is itself the reason to stay small — has no Orthodox C++
analogue, and Orthodox C++'s central complaints (exceptions, RTTI,
allocation you can't see) have no Dependable C analogue because C has
none of those features.

### The strongest counterarguments

Two public threads exist. HN item 46214091 (2025-12-10, 65 points, 65
comments) and lobste.rs `s/plztql` (2026-07-19, 17 points, ~39 comments).
Everything below is a commenter unless labelled otherwise; I found no
published rebuttal from a WG14 member. Martin Uecker (WG14, and credited
on the site's UB chapter) appears in the HN thread with a single
four-word comment, "Programming is unforgiving." — which is not a
position on the document.

### On the implementation-support claim (the strongest challenges)

`flohofwoe` on HN — the author of sokol, so a working C library author —
attacks the empirical core directly:

> "So basically back to C89... I'm not a fan since the changes in C99
> made the language significantly more convenient, more enjoyable and
> actually safer, and even the MSVC C frontend has a nearly complete C99
> implementation since around 2015 (the parts of C99 that matter
> anyway)."

and, when told C89 compiles anywhere:

> "It will be pretty hard to find a platform which doesn't have at least
> a C99 compiler. For instance even SDCC has uptodate C standard support
> (better than MSVC actually), and that covers most 8-bit CPUs all the
> way back to the 70's ... Also let's not forget that C99 is a quarter
> century old by now. That's about as old as K&R C was in 1999 ;)"

`david_chisnall` on lobste.rs (David Chisnall, ex-GCC contributor, CHERI)
gives the mechanism behind slow C99/C11 uptake, which reframes the
implementation-count claim as being about two specific optional
sub-features rather than about the standards as wholes:

> "Both C99 and C11 had big-ticket items that added a lot of
> implementation complexity. For C99, this was all of the Fortran-envy
> floating-point stuff. A lot of implementations didn't claim C99
> compliance for a long time because they didn't completely handle all of
> this ... Almost no C code outside of scientific computing uses it
> because it's horrible ... C11 added atomics. ... Most of the other bits
> of C11 are fairly simple."

`fuhsnn` on HN asks for the falsifiable version of the claim, which the
site does not supply:

> "Honestly as a hobbyist programmer I'm more interested in knowing which
> exact platforms/compilers that don't support the non-dependable
> patterns and why should I care about them. Even better if the author
> can host a list of 'supported platforms' that's guaranteed to work if
> people's projects invest in the style."

### For the implementation-support claim

`malxau` on lobste.rs gives the concrete Windows version of it:

> "I spent most of my time working on Windows, and C99 support was only
> added to Visual C++ ... very recently. While it's possible to depend on
> a newer compiler, doing so also implicitly means the compiled program
> will require a newer version of the operating system. ... as I'm
> writing this there's another story on lobste.rs about somebody getting
> an Itanium Windows VM to run, and I'm confident my C89 code will at
> least compile on that system."

`emk` on lobste.rs states the version of the claim that is hardest to
dispute, while rejecting the conclusion:

> "One of the great remaining advantages of C is that there really is a
> compiler for almost anything, including some of the most godforsaken
> and obscure processors out there. Granted, that compiler might cost
> $5,000 a seat and support most but not quite all of C89. ... (Not that
> any this, in my opinion, excuses using C for new software.)"

`derriz` on HN makes the all-or-nothing argument, which is the sharpest
statement of the position on the page:

> "The problem with post-C89 is that you lose the unique features of
> old-school C. For example, it can be compiled on basically any platform
> that contains a CPU. It has tool support everywhere. And it can be
> fairly easily adapted to run using older C compilers going back to the
> 1980s. ... So the problem with later versions of C is that you lose
> these unique features while you are now competing for mindshare with
> languages that were designed in the modern age."

### On the initialization rules

`flohofwoe` on HN puts the concrete bug against the no-braces rule, using
the site's own example code:

> "Case in point: the article has this somewhere in the example code:
> struct struct s; s.member = 42; s.other_member = 1138; (ignore the
> syntax errors and typos, the article is full of them) If new members
> are added to the struct, you end up with uninitialized memory. With C99
> designated init at least the new members are zero-initialized."

`hvea` supplies the author's rejoinder correctly ("as far as I know the
author takes a stance against zero initialization in general") and
`derriz` supplies the old-school one:

> "Your example of an uninitialized memory situation will not be so
> compelling for old-school C engineers because they've 'solved' the
> issue decades ago by integrating tools like valgrind into their
> work-flows."

`1718627440` on HN takes the site's side and generalizes it: "I honestly
prefer it more, if not explicitly initialized variables stay
uninitialized, since then the compiler/analyzer/fuzzer can find undesired
access instead of it just silently working."

On lobste.rs, `pervognsen` is the substantive voice on why designated
initializers are the feature people actually miss, and why the C++
compatibility argument doesn't hold: C++20 has designated initializers
with different ordering rules, "So it's possible (annoying but possible)
to write C with designated initializers that can be compiled as C++ code
while preserving the intended meaning. But another issue is that many of
the classic use cases for designated initializers also involve C99
compound literals. And when people say they want designated initializers
they usually mean the combination of those two features."

### On specific technical content

`xq` on lobste.rs lists four things as evidence the guide is not
trustworthy:

> "Types are aligned to their size. Which would imply struct{ int a, b,
> c; } is aligned to 3 * sizeof(int) instead of int, so an alignment of
> 12. *int is at least 32 bits. Which excludes all 16-bit embedded
> platforms, making the code unusable for them. ... Don't ever read
> memory with a type that is different then it was written. So never
> serialize/deserialize data, as i cannot read a float as 4 bytes?
> There's some good and some bad advice in there, but overall i would not
> recommend following this guide."

(The alignment objection is a fair reading of the sentence as written;
the site plainly means scalar types. The `int` ≥ 32 bits objection is
real and in tension with the site's own embedded framing. The
serialization objection is answered elsewhere on the site — the
aliasing chapter blesses `memcpy`/`memmove` and standard-library writes —
but not where the reader meets the rule.)

`spc476` on lobste.rs:

> "The more I read, the less I liked it. In the list of keywords to
> avoid, it missed the C++ class keyword---you know, the point of C++!
> The rational for assuming (or preferring) little endianess was silly;
> it didn't even have a technical computer reason behind it. The argument
> about type sizes only mentions 128-bit pointers? Nothing about sizes
> being implementation-dependent and that the minimum sizes relate back
> to the 70s. And the entire 'tweet' section just comes across as
> gatekeeping to me. Yuck."

Both of those check out against the document: `class` is absent from the
C++ keyword list, the endianness argument is a numeral-reading analogy,
and the type-size chapter is one paragraph about 128-bit pointers.

### On the "Why is C the safest language?" chapter

This is where the criticism is sharpest, and it is worth keeping separate
from the rule list — it is the chapter least connected to the subset.

`kornel` on lobste.rs:

> "And the Why is C the safest language? is so confused. It scolds
> security researches for not using the scientific method, but the whole
> section is based on treating correlation as causation. Many
> 'security-critical' projects use C despite its unsafety. For a long
> time, C was the only language that met performance and interop
> requirements such projects had, which forced them to accept the dangers
> of C and deal with consequences."

`madhadron` on lobste.rs gives the alternative causal story:

> "C became common because Unix became common. C stays common because
> there's a lot of C already out there, Unix provides calling conventions
> that break down for anything more complicated than C ... There are
> times when I would start a project in C, but they would be entirely
> because of toolchain and compatibility issues that forced that choice."

`chbarts` counters madhadron with the early-Macintosh case (C displaced
Pascal on a Pascal-designed API), which is a real argument on the site's
side; and separately supplies the best analogy against the
compatibility-forever premise:

> "One of the greatest strengths of C is its compatibility. ... Back not
> too long ago, but long enough to fall from memory, the language people
> were saying this about was FORTRAN. Not Fortran, but line-number
> column-formatted all-caps mainframe-DP EBCDIC character set FORTRAN.
> FORTRAN 66 was not going anywhere ... until it did, eh?"

`0x2ba22e11` on lobste.rs rejects the site's own thesis sentence: "Very
few people want to write Dependable C, but everyone wishes everyone else
wrote their code in Dependable C. — Absolutely not! I am indifferent to
whether a piece of software I might want to run is written in Go, Rust,
Swift, ... but it is an enormous negative for software to be written in a
C family language."

### On presentation

Multiple commenters on both sites raise the same thing, and it is
verifiable: `brooke2k` on HN, "the actual articles are riddled with
spelling errors, typos, missing words, sentences that cut off before And
so on. Is this a work-in-progress thing not meant for public
consumption yet?"; `keyle`, "Inconsistent titles, stuff labelled [TOC]."
The C17 and C23 sections being empty, and the truncated C11 alignment
section, are consistent with that.

### What's checkable vs what's a position

### Positions (taste, not testable)

- C89-subset as a target; "Newscaster C" as the goal.
- No brace initialization of structs, ever; declare-then-assign as the
  preferred form.
- The debuggability argument for `0xCD` over zero fill. (The *portability*
  half of the same argument is empirical — see below — but the site
  itself says portability "is not the main reason".)
- Declaring all variables at the top of the function.
- "Little endian is simply objectively (yet unintuitively) better."
- `malloc` over custom allocators as a default.
- Mutexes over atomics.
- The whole "Why is C the safest language?" chapter, which is explicitly
  labelled as hypotheses: "I want to be clear, I am not a researcher, nor
  am I claiming to present quantitative evidence for these theories."
- The keyword-avoidance list, insofar as its justification is
  "identifiers I want to keep for myself".

### Empirical claims, and what I measured

All tests on this machine: gcc (Ubuntu) 13.3.0 and clang 18.1.3,
x86_64-linux-gnu.

**1. "Later versions of C are also only supported by two implementations
out of the hundreds of C implementations available."** Not checkable as
stated — "supported", "later versions" and "hundreds" are all undefined,
and the site gives no list. What I *can* report is that the two
implementations usually meant are both partial at the versions shipping
in a current LTS distro:

- gcc 13.3 does not accept `-std=c23` at all ("unrecognized command-line
  option '-std=c23'; did you mean '-std=c2x'?"). The C23 spelling
  arrives in gcc 14.
- clang 18.1.3 accepts `-std=c23`, and **rejects `constexpr` in every C
  mode** (`error: unknown type name 'constexpr'`, identical under c17,
  c2x and c23). So of my draft's eight features, the one it calls "the
  one place in the whole list where C caught up completely" does not
  exist on one of the two implementations in question, at the version
  Ubuntu 24.04 ships.
- Feature-by-feature, on the two compilers I have:

  | Feature | gcc 13.3 `-std=c2x` | clang 18 `-std=c23` | gcc/clang pre-C23 |
  |---|---|---|---|
  | `constexpr` object | OK | **error** | error |
  | `static_assert` (keyword) | OK | OK | error (needs `<assert.h>`/`_Static_assert`) |
  | `auto x = 0.0;` | OK (double) | OK | gcc: warns, gives **int**; clang: **error** in c99 |
  | `typeof` | OK | OK | error in strict modes |
  | `nullptr` | OK | OK | error |
  | `enum E : uint8_t` | OK | OK | accepted as an extension by both (gcc `-Wpedantic`, clang `-Wfixed-enum-extension`) |
  | `unreachable()` (with `<stddef.h>`) | OK | OK | gcc: implicit-decl warning; clang: **error** |
  | `[[nodiscard]]` | OK | OK | accepted as an extension by both, and the diagnostic actually fires |
  | `_Generic` | OK | OK | accepted as an extension by both since C11 |
  | `struct S s = {};` | OK | OK | accepted as an extension by both, `-Wpedantic` warns |

  Read against the site's claim, this cuts both ways: the two big
  compilers do accept most of C23, several of these features work back to
  C89 mode as extensions, and yet the one feature my draft rates highest
  is missing from clang 18 and needs a compiler-version-specific `-std`
  spelling on gcc 13.

**2. "You should not initialize NULL pointers with memset!" /
`memset(&s, 0, sizeof s)` "Is not a portable way to set pointer members
of the struct to NULL".** The *portability* claim is not testable on one
platform; the *local* behaviour is, and it is what you'd expect:
`int *p; memset(&p, 0, sizeof p);` yields `p == NULL` and `p == (void*)0`
both true, gcc and clang, `-O2`. Whether a hosted platform exists today
where all-bits-zero is not a null pointer: **could not verify.** I did
not find a first-party citation, and the site gives none; the usual
secondhand references are historical (Prime 50, Honeywell, some CDC
machines) via the comp.lang.c FAQ, which I did not fetch. Treat "a
platform where this breaks" as unverified in both directions. Note also
that the site's *own* stated main reason for the rule is debuggability,
not portability, so the empirical question is not load-bearing for the
advice.

**3. "Being able to declare anywhere as you can in C99 makes the problem
a lot worse" / mid-scope declarations "simply shift where things are
declared".** Cost is testable. Same loop written C89-style (all
declarations at function top) and C99-style (`for (int i…)`, `int t`
inside the body), gcc 13.3:

- `-O2`: `.text` 55 bytes in both, and the multiset of emitted
  instructions is **identical** after normalizing the function name.
- `-O0`: `.text` 103 bytes in both, same instruction count; the only
  differences are which stack slot each variable got.

So the "costs nothing" half of the site's claim is confirmed, and its
argument is not a performance argument — it is entirely about the
`goto`/`switch`-past-an-initializer hazard and shadowing, which is a real
hazard and which the site demonstrates correctly with two compilable
examples.

**4. "`char string[1024] = {'\0'};` ... fills the entire string with null
termination characters."** Confirmed, and visible in the disassembly.
gcc 13.3 `-O2`: the braced version emits `mov $0x80,%ecx` + `rep stos
%rax,%es:(%rdi)` — 128 qwords, i.e. all 1024 bytes. The manual version
(`char s[1024]; s[0] = '\0';`) emits no fill at all. This one is simply
true.

**5. C23 `= {}` is a "death-trap ... you will get entirely uninitialized
memory, without any warnings or error".** Could not reproduce, and I
don't think it can be reproduced with mainstream compilers. Both gcc 13.3
and clang 18 accept `struct S s = {};` all the way back to `-std=c89` as
an extension, warn about it under `-Wpedantic` ("ISO C forbids empty
initializer braces before C2X" / "use of an empty initializer is a C23
extension"), and **do** zero it: a probe that first poisons the stack
with `0xCD` reports `zeroed=1` for gcc and clang, c99 and c17, `-O0` and
`-O2`. The claim is about a compiler that does *not* support the feature,
and to fail the way the site describes such a compiler would have to
accept the syntax and ignore it, which is a stranger failure than
rejecting it. **Untested for lack of such a compiler**; on the two I
have, the failure mode is a diagnostic, not silence.

**6. "auto ... in older versions of C ... will then be given a variable
of type int per default. ... almost all compilers support it with a
warning."** Half confirmed. gcc 13.3 `-std=c89` and `-std=c99` both
compile `auto x = 0.0;` with only a warning (`-Wimplicit-int`) and make
`x` an `int` — so the silent-meaning-change hazard is real on gcc, and
that is the strongest single technical point on the whole site. But
"almost all compilers support it with a warning" does not hold for clang
18: `-std=c99` gives `error: type specifier missing, defaults to 'int';
ISO C99 and later do not support implicit int`, i.e. it is an error by
default, not a warning. So the same code that silently changes meaning
across gcc versions is simply rejected by clang.

**7. "Annex K: No implementations of Annex K exists."** Not tested. Known
counterexample class: Microsoft's `_s` functions predate and differ from
Annex K, and there is a third-party Safe C Library; whether any of these
counts as an Annex K *implementation* is exactly the contested point.
Flag as **could not verify** rather than as either true or false.

**8. "`inline` ... has no meaning due to 'AS-IF'."** This is a position
dressed as a fact, and it is wrong about C99 as written: C99 `inline`
changes the *linkage* rules (an inline definition is not an external
definition), which is observable at link time, not an optimizer hint.
My draft already measures this — the `-O2`-links-but-`-O0`-doesn't case.
Worth noting because it is a place where the site's own C89-first
instinct led it to under-describe a C99 feature.

**9. "there are new platforms that enable 128 bit pointers".** Not
verified. Plausible referents exist (CHERI's 128-bit capabilities are the
obvious one, and the site's parenthetical about encoding a network
address plus a memory address in one pointer sounds like a NUMA/fabric
design), but the site names none, and I did not chase it.

### Things I could not verify at all

- The tweet quoted in search results ("What I want is a dependable C. I
  want the subset I can depend 100% on...", attributed to
  x.com/EskilSteenberg/status/1742400215615684869) came to me as a search
  snippet. I did not fetch x.com, so I have **not** verified that wording
  against the live post. Don't quote it as primary.
- His statement that he decided not to participate in future versions of
  C: the *site* says "I abstain from voting in the languages development"
  and N3176 says "Where this leaves IOS C and the extent of my further
  participation is yet to be determined." A stronger version of this
  appeared in a search summary; I could not find that stronger wording in
  any primary source and did not use it.
- The three talks: titles and speaker confirmed via the YouTube oEmbed
  API only. **Not watched.** Nothing in this document is sourced to them.
- Whether "hundreds of C implementations" is a real count. No source on
  the site, none found.
- Whether any WG14 member has published a rebuttal of Dependable C
  specifically. I found none; the only WG14 voice in either thread is
  Uecker's four-word HN comment.

### Reading list (URLs actually fetched)

- https://dependablec.org/ — the whole thing; single HTML page, ~270 KB,
  all chapters inline, client-side nav.
- https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3176.pdf — Steenberg,
  *A proposal for C2Y* (2023-11-07), 13 pp. The primary source for the
  implementation-count argument, the "two implementations" adoption test,
  and named objections to `auto`/`nullptr`/`constexpr`. Marked DOA by its
  own author on page 1.
- https://www.open-std.org/jtc1/sc22/wg14/www/wg14_document_log — WG14
  document log; used to enumerate his authored papers (N2769, N2859,
  N3176, N3243, N3308, N3519, N3778).
- https://www.open-std.org/jtc1/sc22/wg14/www/contacts — WG14 contacts;
  independent confirmation that Steenberg chairs the Memory Object Model
  Study Group, Svoboda the UB Study Group, Bazley the _Optional Study
  Group.
- https://hn.algolia.com/api/v1/items/46214091 — full comment tree of the
  HN thread "Dependable C" (2025-12-10, 65 points, 65 comments); the
  human-facing page is https://news.ycombinator.com/item?id=46214091.
- https://lobste.rs/s/plztql/dependable_c.json — full comment tree of the
  lobste.rs thread (2026-07-19, 17 points); human page at
  https://lobste.rs/s/plztql/dependable_c.
- https://bkaradzic.github.io/posts/orthodoxc++/ — Orthodox C++,
  Karadžić, 2016-01-16, updated through 2025-10-19. Primary source for
  the comparison.
- https://quelsolaar.com/ — Steenberg's own site; bio and project list.
- http://web.archive.org/cdx/search/cdx?url=dependablec.org — Wayback
  CDX index; used to date the site (404 May 2024, first 200 Nov 2024) and
  to show it is revised every few months.
- https://www.youtube.com/oembed?url=…&format=json for video ids
  `443UNeGrFoM`, `zqHdvT-vjA0`, `SbeNRICgzTA` — titles only: "How I
  program C", "C is All You Need | Eskil Steenberg | Wookash Podcast",
  "Eskil Steenberg – I've had it with the security orthodoxy. – BSC
  2025". Talks not watched.

---

## Orthodox C++ — claim by claim

### Claim 1 — provenance of Orthodox C++

**Claim.** "Orthodox C++ is Branimir Karadžić's (bgfx author), originally a
gist, still maintained."

**Verdict: confirmed**, with one correction — the gist is now a stub that
redirects to a blog post.

**Evidence.** GitHub's API for gist `2e39896bc7d8c34e042b` reports
`owner: bkaradzic`, `created_at: 2016-01-16T21:43:57Z`,
`updated_at: 2026-07-21T07:07:29Z`, 30 revisions, 188 comments. The raw
gist body is now four lines:

> Orthodox C++
> ============
>
> ## This article has been updated and is available [here](https://bkaradzic.github.io/posts/orthodoxc++/).

The canonical text now lives at
`https://bkaradzic.github.io/posts/orthodoxc++/`, dated "Jan 16, 2016",
which itself says:

> This article was originally published as a gist here.

Its Revision History section, verbatim:

> UPDATE As of January 14th 2025, Orthodox C++ committee approved
> selective use of C++20.
>
> Oct 19, 2025 - Added info on modules.
> Jan 16, 2019 - Added info on exception handling.
> Feb 1, 2018 - Added info how constexpr needed multiple iterations to be
> useful.
> Jan 16, 2016 - The original article.

So: first published 16 January 2016; last substantive edit 19 October
2025 (modules); still maintained. Karadžić is the author of bgfx, and the
post lists bgfx among its own "Code examples."

**What the draft should say instead.** Keep the sentence, but note the
move: it started as a gist in January 2016 and the gist now redirects to
`bkaradzic.github.io/posts/orthodoxc++/`, which is the version being
updated (most recently October 2025, to add a section against modules).
Linking the gist alone points readers at a stub.

### Claim 2 — Acton and Muratori "adjacent in sentiment but not the source"

**Claim.** "Acton and Muratori are adjacent in sentiment but not the
source."

**Verdict: confirmed**, and it is stronger than "not the source" — the
lists genuinely differ.

**Evidence, "not the source."** Neither name appears anywhere in the
Orthodox C++ post, including in its "Any other similar ideas?" section,
which does list its actual siblings: Embedded C++, Nominal C++, Sane
C++, "Why Your C++ Should Be Simple", "C++, it's not you. It's me.",
Alexander Radchenko's "Keep It C-mple", "A dialect of C++", the Defold
engine code style, and the Orthodoxy clang plugin. A grep of the rendered
page for `acton|muratori` returns zero hits. The influences it does cite
are Stroustrup ("Within C++, there is a much smaller and cleaner language
struggling to get out."), Andrei Alexandrescu's CppCon 2015 allocator
talk, and Jason Turner.

**Evidence, "adjacent in sentiment."** Acton's CppCon 2014 keynote
"Data-Oriented Design and C++" (slides in the CppCon2014 repo) builds a
list across slides 17–27 under the header "We don't make games for Mars
but…" / "How are games like the Mars rovers?", accumulating, verbatim:

> Exceptions / Templates / Iostream / Multiple inheritance / Operator
> overloading / RTTI

then:

> No STL / Custom allocators (lots) / Custom debugging tools

Note the framing: the list is what NASA/JPL flight-software standards
ban, and Acton's argument is that games share the constraint. Overlap
with Orthodox C++ is real (exceptions, iostream, RTTI, STL) but the
overlap is not total: Acton lists templates and operator overloading,
which Orthodox C++ does *not* ban — it says "Don't use metaprogramming
excessively for academic masturbation. Use it in moderation." Muratori's
Handmade Hero is the same shape from the other direction: he writes
C-style but keeps function overloading and operator overloading
precisely because he likes them (Handmade Network forum thread
"why use C++ instead of C", March 2015).

**What the draft should say instead.** Sharpen it: same milieu (game and
console development, ~2014–2016), independent statements, and the
prohibitions only partly overlap. Acton bans templates and operator
overloading; Orthodox C++ permits templates in moderation, and Muratori
keeps operator overloading on purpose. There is no shared document. The
gist's own "similar ideas" list names Embedded C++, Sane C++ and the
Defold style guide, not Acton or Muratori.

### Claim 3 — the changelog concedes `constexpr` needed iterations

**Claim.** "The gist's own changelog concedes `constexpr` needed several
iterations to become useful."

**Verdict: confirmed**, verbatim, and it is in the body as well as the
changelog.

**Evidence.** Changelog entry:

> Feb 1, 2018 - Added info how constexpr needed multiple iterations to be
> useful.

The body text that entry added, verbatim:

> Wary of any features introduced in current standard C++, ideally wait
> for improvements of those feature in next iteration of standard.
> Example constexpr from C++11 became usable in C++14 (per Jason Turner
> cppbestpractices.com curator).

**What the draft should say instead.** This is the one place where the
draft can quote rather than characterize, so quote it. But the draft's
gloss — "an admission that 'avoid the new thing' isn't durable advice" —
inverts the author's intent. He offers `constexpr` as *supporting
evidence* for the wait-five-years rule: the feature arrived unusable in
C++11 and became usable in C++14, therefore waiting was correct. The
honest framing is that the example cuts both ways: it vindicates the
delay rule for `constexpr` specifically, while conceding that the list of
things to avoid is not fixed — a feature can graduate off it. The
"committee approved selective use of C++20" note (Jan 2025) is the same
concession made structurally.

### Claim 4 — HN's "Orthodox C++ committee" jab

**Claim.** "HN's recurring jab is that nobody can identify the 'Orthodox
C++ committee' besides the author."

**Verdict: partly.** The comment exists and says almost exactly that, but
"recurring" on HN is wrong, and the joke's origin is the author himself.

**Evidence.** Across all five HN submissions of Orthodox C++ (413
comments total: 48517412 / 2026-06-13, 25554018 / 2020-12-27, 40445536 /
2024-05-22, 13751244 / 2017-02-28, 35688013 / 2023-04-24), the phrase
"Orthodox C++ committee" appears exactly **once**, in comment 25555603 by
`MauranKilom` on the 2020 thread:

> I would also like to know who or what the "Orthodox C++ committee" is.
> A search only gets you this exact gist. Is the author himself the
> committee? That really doesn't put this piece into a better light.

The joke is much more at home in the gist's own 188 comments, where it
recurs — and where the author plays along. `Jiwan`, 2019-05-05:

> I feel so relieved that the orthodox committee finally approved C++14
> this year. I have been living in fear for the past few years […]

`illnyang`, 2021-01-28:

> On a serious note, does Orthodox C++ committee plan on approving C++17?
> constexpr stuff is pretty neat

`bkaradzic`, same day, replying:

> C++17 will be approved on January 1st, 2022 (mark that date in your
> Julian calendar).

And the term is the author's own, still in the live post: "As of January
14th 2025, Orthodox C++ committee approved selective use of C++20."

**What the draft should say instead.** Attribute it correctly and drop
"recurring […] on HN." Something like: the "Orthodox C++ committee" is
Karadžić's own running joke — the post announces what the committee has
approved — and readers pick it up both straight and sarcastically. One HN
commenter took it at face value and asked who the committee is, noting a
search "only gets you this exact gist"; the author's answer, in the gist
comments, was that C++17 would be approved on 1 January 2022. Cite
`MauranKilom` (HN 25555603) if you quote it, and don't imply a chorus.

### Claim 5 — "some commenters argue there's no real use for the STL"

**Claim.** "The overreach (some commenters argue there's no real use for
the STL) is where it stops being engineering."

**Verdict: confirmed as to existence, wrong as to venue and as to
"commenters" plural.** It is one gist comment, not HN, and the HN threads
run the opposite way.

**Evidence.** Gist comment by `DrCroco`, 2016-10-07:

> I'd say that you're not orthodox enough. First of all, there's no real
> use for STL. Complicated data structures are never generic, they must
> be carefully designed for each particular task. From the other hand,
> primitive data structures, such as vector or list, give almost no
> profit, but are way harder to debug/maintain than hand-crafted linked
> lists and resizeable arrays. Furthermore, the very idea of a container
> _class_ is weird.

The same commenter continues:

> Next, there's no such thing as 'safe features from new standards'. All
> technical standards since around 1995 or so are simply terrorist acts,
> and these committees that prepare and create new standards are
> dangerous international terrorist organizations […]

which is the tell: this is a single self-consciously extreme comment, and
its author frames himself as *more* orthodox than the post. Meanwhile the
HN threads push the other way. Searching all 413 HN comments for any
claim that the STL is useless returns nothing; what it returns is
pushback on the STL restriction, e.g. on the 2024 thread:

> "don't use the STL if it allocates memory" is pretty aggressive change,
> especially compared to "some templates are okay" Gimme
> std::vector/map/unordered_map/list. The performance cost is pretty
> miniscule […]

and on the 2020 thread:

> So don't use std::vector? Or std::unordered_map? Or std::string? These
> are all perfectly fine classes, banning them makes no sense at all.

**What the draft should say instead.** Either quote `DrCroco` with the
attribution and the "terrorist acts" sentence attached — which shows the
reader exactly what kind of comment it is, and makes the "stops being
engineering" point without you having to assert it — or cut the claim.
"Some commenters" as written implies a faction; it is one person in the
gist thread, and the crowd reaction to Orthodox C++ is the reverse. Note
also that the post itself never says the STL is useless: it says "Don't
use anything from STL that allocates memory, unless you don't care about
memory management," which several commenters read as a conditional rather
than a ban.

### Claim 6 — LLVM disables exceptions and RTTI; Google banned exceptions
for over a decade

**Claim.** Both halves as stated in the draft ("Part of why it's banned
in LLVM").

**Verdict: confirmed**, with two nuances the draft is currently missing:
Google's RTTI position *softened*, and Google says explicitly that its
exception ban is not a technical judgement.

**Evidence, LLVM.** LLVM Coding Standards, section headed "Do not use
RTTI or Exceptions":

> In an effort to reduce code and executable size, LLVM does not use
> exceptions or RTTI (runtime type information, for example,
> `dynamic_cast<>`).
>
> That said, LLVM does make extensive use of a hand-rolled form of RTTI
> that use templates like isa<>, cast<>, and dyn_cast<>. This form of
> RTTI is opt-in and can be added to any class.

This is enforced at build level. LLVM's CMake documentation:

> **LLVM_ENABLE_EH**:BOOL — Build LLVM with exception-handling support.
> This is necessary if you wish to link against LLVM libraries and make
> use of C++ exceptions in your own code that need to propagate through
> LLVM code. Defaults to OFF.
>
> **LLVM_ENABLE_RTTI**:BOOL — Build LLVM with run-time type information.
> Defaults to OFF.

**Evidence, Google, exceptions.** Current guide: "We do not use C++
exceptions." The same sentence is in the earliest Wayback snapshot of the
guide I could retrieve, `cppguide.xml` as of 2008-07-01 — so the ban is
at least eighteen years old, not "over a decade." Also in both the 2008
and current text, verbatim:

> Our advice against using exceptions is not predicated on philosophical
> or moral grounds, but practical ones. Because we'd like to use our
> open-source projects at Google and it's difficult to do so if those
> projects use exceptions, we need to advise against exceptions in Google
> open-source projects as well. Things would probably be different if we
> had to do it all over again from scratch.

**Evidence, Google, RTTI — the position changed.** 2008 snapshot:

> We do not use Run Time Type Information (RTTI).

Current guide, heading and decision line:

> Run-Time Type Information (RTTI) — Avoid using run-time type
> information (RTTI).

and:

> RTTI has legitimate uses but is prone to abuse, so you must be careful
> when using it. You may use it freely in unit tests, but avoid it when
> possible in other code. In particular, think twice before using RTTI in
> new code.

The current guide also, notably for section 8's argument, forbids the
LLVM approach:

> Do not hand-implement an RTTI-like workaround. The arguments against
> RTTI apply just as much to workarounds like class hierarchies with type
> tags. Moreover, workarounds disguise your true intent.

and gives its own rationale in design rather than cost terms:

> Querying the type of an object at run-time frequently means a design
> problem. […] Decision trees based on type are a strong indication that
> your code is on the wrong track.

**What the draft should say instead.** Three corrections. (1) LLVM's is
not merely a coding-standard preference — `LLVM_ENABLE_EH` and
`LLVM_ENABLE_RTTI` both default to OFF, so the whole project builds
`-fno-rtti -fno-exceptions`, and the stated reason is code and executable
size, matching the measured "read-only data only, zero `.text`" result.
(2) Google's exception ban is eighteen-plus years old and Google itself
attributes it to legacy-code inertia, not to a cost model — "Things would
probably be different if we had to do it all over again from scratch."
Quoting that line is far more useful to a returning C programmer than the
bare fact of the ban, because it says the ban does not transfer to a new
codebase. (3) Google's RTTI rule went from "We do not use RTTI" (2008) to
"Avoid using RTTI" plus free use in unit tests (now) — a softening worth
one sentence, and a direct counterexample to the section's implicit
premise that the industry converged on banning it. Add that Google
explicitly rejects LLVM's replacement ("Do not hand-implement an
RTTI-like workaround"), because that means the two most-cited style
guides in this argument disagree with each other about the alternative,
not just about RTTI.

### Claim 7 — `isa<>`/`dyn_cast<>`/`classof` is "a tag switch with syntax"

**Claim.** "`dyn_cast` is a template that calls `classof` — one integer
compare, inlinable, no runtime tables. A tag switch with syntax."

**Verdict: partly confirmed.** The mechanism is right; "one integer
compare" is right only for leaf classes. Non-leaf classes are a range
check — two comparisons — and the mechanism depends on an ordering
invariant the draft doesn't mention.

**Evidence.** LLVM's "How to set up LLVM-style RTTI for your class
hierarchy" states the premise:

> LLVM avoids using C++'s built in RTTI. Instead, it pervasively uses its
> own hand-rolled form of RTTI which is much more efficient and flexible,
> although it requires a bit more work from you as a class author.

The dispatch, verbatim:

> The code of the `isa<>` test in this code will eventually boil
> down—after template instantiation and some other machinery—to a check
> roughly like `Circle::classof(S)`.

The part the draft omits:

> The reason that we need to test a range like this instead of just
> equality is that both `SpecialSquare` and `OtherSpecialSquare` "is-a"
> `Square`, and so `classof` needs to return true for them. This approach
> can be made to scale to arbitrarily deep hierarchies. The trick is that
> you arrange the enum values so that they correspond to a preorder
> traversal of the class hierarchy tree. With that arrangement, all
> subclass tests can be done with two comparisons as shown above.

And LLVM warns about the cost of that invariant, in a section titled "A
Bug to be Aware Of":

> The example just given opens the door to bugs where the `classof`s are
> not updated to match the `Kind` enum when adding (or removing) classes
> to (from) the hierarchy.

On `dyn_cast` itself, the Programmer's Manual:

> The `dyn_cast<>` operator is a "checking cast" operation. It checks to
> see if the operand is of the specified type, and if so, returns a
> pointer to it (this operator does not work with references). If the
> operand is not of the correct type, a null pointer is returned. Thus,
> this works very much like the `dynamic_cast<>` operator in C++, and
> should be used in the same circumstances.

> you should **not** use an `isa<>` test followed by a `cast<>`; for that
> use the `dyn_cast<>` operator.

**What the draft should say instead.** Keep the snippet but fix the cost
claim and add the invariant, because the invariant is the actual price of
the technique and it is the kind of detail a C programmer will recognise
immediately. Suggested substance: `dyn_cast<T>` instantiates down to
roughly `T::classof(p)`; for a leaf class that is one integer compare,
and for a class with subclasses it is a two-comparison range check —
which only works because the `Kind` enum values are laid out in preorder
traversal of the hierarchy. So it is not "a tag switch with syntax" so
much as *an ordered tag with a hand-maintained range invariant*, and LLVM
documents the corresponding failure mode: add a class, forget to update
`classof`, and the range silently stops covering it. Compare that against
`-fno-rtti` saving the measured ~130 bytes of read-only data per
polymorphic class and turning an out-of-line `call __dynamic_cast`
(6.9–7.2 ns) into an inlined compare (0.51–0.56 ns) — that's the actual
trade: a compiler-maintained table for a human-maintained enum ordering.

### Claim 8 — the RTTI mechanism, and the string-comparison claim

**Claim.** Four sub-claims: (a) `type_info` emitted per polymorphic
class; (b) vtable slot −1 points at it; (c) `dynamic_cast` walks the
hierarchy; (d) "the Itanium ABI compares type *names by string* to stay
correct across shared library boundaries."

**Verdict: (a) confirmed, (b) confirmed, (c) confirmed, (d) refuted as
stated** — the ABI says the opposite. String comparison is a libstdc++
implementation *default*, not an ABI requirement, and the reason is
`dlopen`/`RTLD_LOCAL`, not shared libraries in general.

**Evidence (a).** Itanium C++ ABI:

> […] should be emitted with the primary virtual table for that type. For
> other types, they must be emitted at the location where their use is
> implied: the object file containing the typeid, throw or catch.

and:

> We add one pointer to the `std::type_info` class in addition to the
> virtual table pointer implied by its virtual destructor: […]
> `__type_name` is a pointer to a NTBS representing the mangled name of
> the type.

**Evidence (b).** Verbatim, and more precise than the draft:

> Every virtual table shall contain one entry that is a pointer to an
> object derived from `std::type_info`. This entry is located at the word
> preceding the location pointed to by the virtual pointer (i.e., entry
> "-1"). The entry is allocated in all virtual tables; for classes having
> virtual bases but no virtual functions, the entry is zero.

Note "allocated in all virtual tables" — the slot exists regardless, which
is consistent with the measured result that `-fno-rtti` removes read-only
data and changes zero bytes of `.text`: it nulls a slot and drops the
pointed-to object, it does not resize the vtable or alter call sites.
Slot −2 is the offset-to-top used by `dynamic_cast<void*>`.

**Evidence (c).** The ABI specifies `abi::__dynamic_cast`:

> extern "C" void* __dynamic_cast (const void *sub,
>   const abi::__class_type_info *src,
>   const abi::__class_type_info *dst,
>   std::ptrdiff_t src2dst_offset);

with the rationale, verbatim:

> A simple dynamic_cast algorithm that is efficient in the common case of
> base-to-most-derived cast case is preferable to more sophisticated
> ideas that handle deep-base-to-in-between-derived casts more
> efficiently at a slight cost to the common case. Hence, an earlier
> scheme of providing a hash-table into the list of base classes (as is
> done e.g. in the HP aC++ compiler) was dropped. For similar reasons, we
> only keep direct base information about a class type. Indirect base
> information can be found by chasing type_info pointers (and care should
> be taken to determine ambiguous base class types).

"Chasing type_info pointers" for indirect bases is the hierarchy walk,
and "we only keep direct base information" is why there is no O(1)
guarantee — the ABI deliberately traded away the hash table. The
`src2dst_offset` hint exists to short-circuit the common case, and "An
implementation is free to always pass -1 (no hint), or to always ignore
the hint in __dynamic_cast." That an out-of-line `call __dynamic_cast` is
the observed code shape is exactly what the ABI prescribes.

**Evidence (d) — this is the one to fix.** The ABI mandates *address*
comparison:

> After linking and loading, only one `std::type_info` structure is
> accessible via the external name defined by this ABI for any particular
> complete type symbol (see Vague Linkage). Therefore, except for direct
> or indirect pointers to incomplete types, the equality and inequality
> operators can be written as address comparisons when operating on those
> type_info objects: two type_info structures describe the same type if
> and only if they are the same structure (at the same address).

The only string-flavoured line in the ABI is about the *name* pointer,
still an address comparison:

> In a flat address space (such as that of the Itanium architecture), the
> `operator==`, `operator!=`, and `before()` members are easily
> implemented in terms of an address comparison of the name NTBS.

The `strcmp` is libstdc++'s choice, and libstdc++ says why. From
`libstdc++-v3/libsupc++/typeinfo`:

> Determine whether typeinfo names for the same type are merged (in which
> case comparison can just compare pointers) or not (in which case
> strings must be compared) […] We used to do inline pointer comparison by
> default if weak symbols are available, but even with weak symbols
> sometimes names are not merged when objects are loaded with RTLD_LOCAL,
> so now we always use strcmp by default.

and:

> // By default, typeinfo names are not merged.
> #define __GXX_MERGED_TYPEINFO_NAMES 0

The actual `operator==` is a pointer compare with a guarded `strcmp`
fallback, keyed on a leading `'*'` that marks a name known to be unique:

> if (__name == __arg.__name)
>   return true;
> […]
> #elif !__GXX_MERGED_TYPEINFO_NAMES
>   // Need to do string comparison.
>   return __name[0] != '*' && __builtin_strcmp (__name, __arg.name()) == 0;

`name()` itself strips that marker: `return __name[0] == '*' ? __name + 1
: __name;`.

**What the draft should say instead.** Replace the sentence. Correct
version: the Itanium ABI requires that only one `type_info` be reachable
per complete type after linking and loading, and therefore says equality
"can be written as address comparisons." libstdc++ does not trust that in
practice — its own header explains that names are sometimes not merged
when objects are loaded with `RTLD_LOCAL`, so `__GXX_MERGED_TYPEINFO_NAMES`
defaults to 0 and `operator==` falls back to `strcmp` after the pointer
compare misses, unless the name is marked unique with a leading `'*'`. So
the string comparison is real, but it is a libstdc++ default hedging
against `dlopen`, not an ABI mandate, and not something that happens on
every cross-library cast. The genuine ABI-level reason `dynamic_cast` is
unbounded is separate and better: the ABI keeps only *direct* base
information per class and explicitly dropped an earlier hash-table scheme,
so indirect bases are found by "chasing type_info pointers."

### What Orthodox C++ actually says now

Straight from `bkaradzic.github.io/posts/orthodoxc++/`, in its own words.

**Framing.** "Orthodox C++ (sometimes referred as C+) is minimal subset
of C++ that improves C, but avoids all unnecessary things from so called
Modern C++. It's exactly opposite of what Modern C++ suppose to be." The
motivation given is experiential, not theoretical: "Back in late 1990 we
were also modern-at-the-time C++ hipsters, and we used latest features. We
told everyone also they should use those features too. Over time we
learned it's unnecesary to use some language features just because they
are there, or features we used proved to be bad (like RTTI, exceptions,
and streams), or it backfired by unnecessary code complexity."

**Claimed benefit.** "Code base written with Orthodox C++ limitations
will be easer to understand, simpler, and it will build with older
compilers. Projects written in Orthodox C++ subset will be more
acceptable by other C++ projects because subset used by Orthodox C++ is
unlikely to violate adopter's C++ subset preferences." That last clause is
the interesting one and rarely quoted: the argument is partly about
*interoperability of subsets*, not only about performance.

**Keep.** C-like C++ — "if code doesn't require more complexity don't add
unnecessary C++ complexities. In general case code should be readable to
anyone who is familiar with C language." Its "Hello World" is
`#include <stdio.h>` and `printf`. Templates and metaprogramming are
allowed "in moderation, only where necessary, and where it reduces code
complexity." `constexpr` is cited approvingly (as of C++14).

**Drop.** Exceptions (with a long quoted rationale about exception
handling being "the only C++ feature that has a runtime cost even if you
don't use it"); RTTI; the `<cxxx>` wrappers, in favour of `<stdio.h>`,
`<math.h>`; iostream and stringstream, in favour of printf-style;
"anything from STL that allocates memory, unless you don't care about
memory management"; excessive metaprogramming; and, since October 2025,
modules — for which the post lists disadvantages (rewrite, "Loss of
portability", non-portable module binaries, more complicated build setup,
only the newest toolchains work) and, under advantages: "Nothing."

**The dating rule.** "if current year is C++year+5 then it's safe to
start selectively using C++year's features." Hence the changelog
approving C++14 (2019), C++17 (announced for 1 January 2022), and
"selective use of C++20" (January 2025).

### The strongest published pushback

**Harald Achitz (a4z), "Orthodox C++, a Good or Bad Idea?", 14 January
2024.** The definitional argument, verbatim:

> There is no exact definition of Orthodox C++.

> This definition is very loose. It's unclear what is meant by
> "unnecessary things." Also, there is no exact definition of Modern C++,
> so what should be the opposite of it?

> The problem I see is finding and defining the smaller and clearer
> language that is Orthodox C++. Viewpoints may vary widely. Soon, a
> discussion about it might leave the realm of C++ and become one of
> those infamous programming-religious discussions where it's not about
> facts anymore, but beliefs and opinions. From this point of view, I find
> the name "Orthodox C++" pretty accurate. :-)

His real objection is sociological rather than technical:

> I once had to work with people who told me they rejected C++11 or
> anything newer since they did not want to have two programming
> languages in one project. To me, that was a very uneducated point of
> view. Unfortunately, while there is some merit in the idea of Orthodox
> C++, I see the concept too often misused to justify not learning new
> things or leaving an existing comfort zone.

And what he concedes:

> A bit of Orthodox C++ is not a bad idea, in some aspects. Until some of
> them - for me, problematic or unclear - new features are more mature,
> well-understood, and explored.

> But my approach is to look at features, decide if I fully understand
> them, and then decide if I want to use them or not.

That last line is the sharpest version of the critique, and it is worth
the draft's while: Achitz's alternative is per-feature judgement rather
than a list, which is the same move Karadžić makes when his committee
"approves" a standard — just without the pretence of a rule.

**Others, from HN 48517412 (13 June 2026, 228 comments).** `Panzerschrek`:

> "> Don't use RTTI." That's the core feature of the language. Not using
> it doesn't make any sense. […] Overall I find such "Orthodox" C++
> harmful. I call it "pure C heresy".

`ok123456`, which is the most useful hostile comment because it concedes
the domain and denies the generalisation:

> No exceptions or RTTI make sense in an embedded system that needs to
> ensure determinism, but are arbitrary and unnecessarily hobbling for
> high-level systems and application programming.

`PaulDavisThe1st`:

> Also, you can fight me if you want to take `dynamic_cast<Derived>
> (base_ptr)` and force me to implement my own typing system every time I
> need to upcast.

And the best defence, from `flohofwoe` (Andre Weissflog, author of the
"Sane C++" post the gist links, and of Oryol which it lists as an
example) — worth quoting because it corrects a misreading the draft is
close to making:

> Orthodox C++ isn't generally against new C++ features, it only advices
> to wait about 5 years (or at least one C++ version) for stabilization
> and to apply some common sense before adopting them. The notes about
> not using RTTI, exceptions and stdlib features that allocate under the
> hood are all justified by painful experience with those things in the
> context of game development.

He also notes, against the draft's own snippet choice, that
`dynamic_cast` "is also a typical code smell" while range-`for` with
`auto const&` "is allowed by Orthodox C++" — i.e. the subset is not
anti-C++11.

### Reading list — URLs actually fetched

- https://gist.github.com/bkaradzic/2e39896bc7d8c34e042b — now a 4-line stub redirecting to the blog post
- https://gist.githubusercontent.com/bkaradzic/2e39896bc7d8c34e042b/raw — raw stub text
- https://api.github.com/gists/2e39896bc7d8c34e042b — created_at 2016-01-16, 30 revisions, 188 comments
- https://api.github.com/gists/2e39896bc7d8c34e042b/comments — the 188 gist comments (DrCroco, Jiwan, illnyang, bkaradzic replies)
- https://bkaradzic.github.io/posts/orthodoxc++/ — canonical Orthodox C++ text and Revision History
- https://a4z.noexcept.dev/blog/2024/01/14/OrthodoxCpp.html — Achitz's skeptical post, full text
- https://a4z.noexcept.dev/about/ — confirms a4z is "Harald", Stockholm, SwedenCpp
- https://llvm.org/docs/CodingStandards.html — "Do not use RTTI or Exceptions"
- https://llvm.org/docs/ProgrammersManual.html — isa<>/cast<>/dyn_cast<> semantics
- https://llvm.org/docs/HowToSetUpLLVMStyleRTTI.html — Kind enum, classof, preorder range check
- https://llvm.org/docs/CMake.html — LLVM_ENABLE_EH / LLVM_ENABLE_RTTI both default OFF
- https://google.github.io/styleguide/cppguide.html — current Exceptions and RTTI sections
- http://web.archive.org/web/20080701113040/http://google-styleguide.googlecode.com:80/svn/trunk/cppguide.xml — 2008 guide, dating the bans
- https://itanium-cxx-abi.github.io/cxx-abi/abi.html — vtable entries −1/−2, type_info layout, __dynamic_cast, address-comparison rule
- https://raw.githubusercontent.com/gcc-mirror/gcc/master/libstdc%2B%2B-v3/libsupc%2B%2B/typeinfo — __GXX_MERGED_TYPEINFO_NAMES, strcmp fallback
- https://github.com/CppCon/CppCon2014/raw/master/Presentations/Data-Oriented%20Design%20and%20C%2B%2B/Data-Oriented%20Design%20and%20C%2B%2B%20-%20Mike%20Acton%20-%20CppCon%202014.pptx — slides 17–27, the Mars rovers list
- https://hn.algolia.com/api/v1/search — HN stories 48517412, 25554018, 40445536, 13751244, 35688013 and all 413 comments
- https://news.ycombinator.com/item?id=25554018 — MauranKilom's "Orthodox C++ committee" comment (id 25555603)
- https://news.ycombinator.com/item?id=48517412 — 2026 thread, Panzerschrek / ok123456 / PaulDavisThe1st / flohofwoe
- https://hero.handmade.network/forums/code-discussion/t/453-why_use_c%2B%2B_instead_of_c — Muratori on his C++ subset

### Notes on the established measurements

Nothing in the primary sources contradicts them; two corroborate.

- ~130 bytes of read-only data per polymorphic class, zero `.text`: matches
  the ABI, which allocates the slot-−1 entry "in all virtual tables"
  regardless (so `-fno-rtti` nulls a pointer and drops the pointed-to
  object rather than changing code layout), and matches LLVM's stated
  motive, "In an effort to reduce code and executable size."
- `dynamic_cast` at 6.9–7.2 ns as an out-of-line `call __dynamic_cast`:
  matches the ABI, which specifies `abi::__dynamic_cast` as an
  `extern "C"` runtime call and deliberately dropped the hash-table
  scheme, keeping "only direct base information about a class type."
- The tag compare at 0.51–0.56 ns is the leaf-class case; per LLVM's
  docs a non-leaf `classof` is two comparisons, so the ~13x figure is the
  best case for the tag side.

---

## Casey Muratori — the cost argument and the history

# Source notes: Casey Muratori on OOP, abstraction, and their costs

### Provenance and what is primary

Three notes on sourcing before anything else, because they change how much
weight each part of this carries.

**The Big OOPs talk.** There is no written transcript and no article
version. The computerenhance.com post that accompanies it is a short
pointer piece plus a reading list — it contains almost no argument. What I
worked from is the YouTube auto-generated caption track for
`wo84LFzx5nI`, downloaded with `yt-dlp` (~30,000 words). That is the
talk's own words, so the *substance* is primary, but the *text* is ASR
output: proper names are mangled throughout ("Bjnestrip", "Strus",
"Allen K", "Southerntherland", "fatty strruct"). Every quote below marked
`[caption]` is ASR text; I have kept the wording verbatim and only noted
in brackets where a garbled name is obviously a known person. On HN, a
commenter reports asking Muratori on Twitter for a text version and being
told "sorry, no" — I could not verify that exchange.

**The Frontend Masters writeup could not be fetched.** The URL 302s to
`blog.master.dev`, which returns 403 to WebFetch; direct fetches of the
frontendmasters.com URL returned 429 (rate-limited) on two attempts.
Nothing in these notes comes from it.

**The clean-code benchmark's compiler, flags and CPU are not stated
anywhere I could find.** See "What is *not* in the sources", below.

### 1. "The Big OOPs: Anatomy of a Thirty-Five-Year Mistake"

Better Software Conference (inaugural), Sweden; video posted 2025-07-17.
Runtime ~2h07 of talk plus ~35 min of on-stage interview with Ryan Fleury.

### The claim he is making, in his own framing

He spends about 90 seconds at the top narrowing the target, explicitly to
pre-empt the objection that he is attacking OOP in general.

> "when I say the big oops anatomy of a 35-y year mistake, I'm not
> talking about uh OOP as a whole. I'm talking about looking for very
> specific things in it." `[caption ≈00:10:04]`

> "And I'm not saying it *was* a mistake. I'm saying *this* was a
> mistake: the idea that you're going to draw encapsulation boundaries
> around these compile time hierarchies that are based off of whatever
> you're trying to write." `[caption ≈00:10:49]`

The unit of the argument is therefore not inheritance, not virtual
functions, and not OOP — it is *where the encapsulation boundary goes*:

> "Encapsulation boundaries are really what we care about when we're
> doing architecture. What we care about is where we make it difficult to
> access things and where we make it easy" `[caption ≈00:04:45]`

The contrast case is the opening example: Looking Glass's Thief: The Dark
Project (1998), which drew its encapsulation boundaries around *systems*
(physics, combat) rather than around entities, with entities reduced to
IDs used as lookup keys — what we now call an entity-component system. He
claims it as "the first instance of an actually commercially released
entity component system" `[caption ≈00:04:21]`. He is careful that this
is still OOP-compatible: "it's important to remember this is not like not
oop you could easily call this object-oriented programming"
`[caption ≈00:05:39]`.

The phrase he keeps returning to — "compile time hierarchies that match
the domain model" — he credits to a Looking Glass programmer whose name
the captions render as "Mark Blank" / "Mach" / "Mock", described as
having done "a lot of the implementation" of the Dark Object System and
having joined at Ultima Underworld 2. From the surrounding facts this is
Marc "Mahk" LeBlanc; the identification is mine, from caption text, not
from a written source.

**The "35 years", precisely.** Not 1990→2025. It is the gap between the
architecture being *available* and the architecture being *shipped*:

> "that's the 35-year mistake is the distance between those two years.
> The year in which we could have had the entity component system
> because the first person has sort of done something that was almost
> that and the year in which we actually got the entity component
> system, which I'm not even saying is a good design or not. I don't
> even have an opinion on something like that to be completely honest
> with you." `[caption ≈01:20:36]`

i.e. Sketchpad (1963) → Thief (1998). Note that he disclaims any verdict
on ECS itself in the same breath.

### The historical narrative

He states his method: "I went only through primary sources for this"
`[caption ≈00:17:31]`. The chain, running backwards the way he presents
it:

**C++ (Stroustrup).** 1978, Cambridge, PhD on distributed systems — not a
languages researcher. Wrote a simulator in Simula, having learned Simula
directly from Kristen Nygaard at his previous university. Liked it
because the "class concept ... was really good for direct mapping"
`[caption ≈00:20:09]` — the domain he was modelling was literally a set
of processes that cannot reach into each other, so "It's an exact fit for
what a class actually does" `[caption ≈00:20:09]`. Then the Simula
version collapsed: build times ("If you compiled 1/30th of the program
and tried to link it, it was slower than just recompiling the entire
thing" `[caption ≈00:22:55]`) and runtime (the garbage collector "was
taking any 80% of the runtime apparently even though there was no actual
garbage that needed to be collected" `[caption ≈00:23:35]`). He rewrote
it in BCPL, which has essentially no type checking. At Bell Labs he built
C with Classes to get Simula's typing without Simula's collapse.
Stroustrup also used inheritance for *code reuse* (deriving from a link
block so things could go in a list) — a use Stroustrup himself later
disowned in favour of parameterized types.

**Simula 67 (Dahl and Nygaard).** The classes came out of a code-reuse
problem, not an architecture theory: a toll bridge with trucks and buses
crossing it, "What could we do so that we could just write this once and
have it work for both the trucks and the buses" `[caption ≈00:36:10]`.
The 1963-era snippet he shows is `link class car`, then `car class truck`
and `car class bus` — both uses at once, inheritance-for-reuse (`link`)
and inheritance-as-domain-model (`car`/`truck`/`bus`). Virtual functions
came later and secondarily, to let subclasses vary the queueing
operations.

**Hoare (1966), "Record Handling".** Dahl and Nygaard credit subclassing
to Hoare, not to themselves. Muratori's find here is the one he seems
most pleased with: Hoare's paper *already contained discriminated unions*
and a switch-like construct to consume them type-safely, and Hoare
already understood the type-safety benefit. Simula kept it as `inspect`.
Then:

> "When Stroustrup went to do his classes, he took it out. He thought
> that discriminated unions were bad because they broke modularity,
> right? It's because now someone from the outside can tell what class
> you are. So we lost out on one of what I consider would be one of the
> most important features I would use in C++ every day because it got
> removed when Simula was playing telephone with C++."
> `[caption ≈00:47:32]`

**Ross's "plex" (1960, work from ~1956).** Hoare got the structured-data
idea from Douglas T. Ross via the ALGOL 68 committee. The plex is a
record with data members, linkage (pointer) members, flag fields, *and
embedded subroutine addresses* — i.e. function pointers, which Muratori
identifies as virtual functions in 1960: "there is where you basically
have your virtual function staring you right in the face right there in
1960 contemporaneous with lisp" `[caption ≈01:04:30]`.

**Sketchpad (Sutherland, 1963).** Sutherland got the plex from Ross
directly (adjacent MIT labs). Muratori's core historical point: the part
of Sketchpad everyone copied was the drawing and the dispatch-through-
function-pointer trick, and the part nobody copied was the data
structure. Sketchpad's runtime "ring structure" (his "hen"/"chicken"
sentinel-and-link terminology) organises everything into runtime rings of
variables, holders, constraints and topos — "Again, not a compile time
hierarchy, actually a runtime set of rings" `[caption ≈01:35:58]` — and
it is deliberately *not* encapsulated: "it's almost like the most
unencapsulated thing that you could possibly imagine, which is probably
why it was so cool" `[caption ≈01:36:56]`. That is what let the
constraint solver work. He draws it and observes it is an ECS.

**Alan Kay.** Kay called Sutherland's thesis "the most significant single
thesis ever done". But Kay praised Borning's ThingLab for "a nice
approach for dealing with constraints that didn't require the solver to
be omniscient" — and Muratori's response is the hinge of the whole talk:

> "The omniscient part was the good part, right? That was the thing that
> was so powerful." `[caption ≈01:41:57]`

**His causal explanation** for why both Kay and Stroustrup missed it is
biographical, and he flags it as a guess ("this is my best guess"):
Stroustrup came from distributed systems, Kay had a molecular-biology
background; "They're both thinking of little tiny cells that communicate
back and forth but which do not reach across into each other's domain"
`[caption ≈01:43:00]`. He adds that the model is right for its origin
domains — "It's a great idea when thinking about systems that are
actually separated in that way like actual computers talking over a
network" — and wrong inside one machine: "when you're talking about code
that's working inside one computer in the same core memory that's meant
to work together, it's too limiting" `[caption ≈01:43:38]`.

He closes on a quote he attributes to Kay: "the most treacherous
metaphors are the ones that seem to work for a time because they can keep
more powerful insights from bubbling up" `[caption ≈01:48:32]`.

### The two claim types, separated

This is the distinction the draft needs, because he mixes them and his
critics attack across the seam.

**Historical claims** (falsifiable, source-based):

1. Classes and virtual functions in Simula 67 arose from a code-reuse
   problem (the toll bridge), not from any analysis of team size,
   modularity, or architecture. "Nothing about teams, nothing about
   architecture, none of this stuff" `[caption ≈00:39:33]`.
2. Domain-model-shaped hierarchies were in fact *advocated*, not merely
   used in bad tutorials. His evidence: Stroustrup's "What is
   Object-Oriented Programming?" opens with the shape/switch example and
   says object-oriented programming *is* programming using inheritance;
   Smalltalk's own base library ships a `path` class with shapes derived
   from it.
3. The specific advice-chain rebuttal: nobody designed this for large
   teams. "How big was the team that Bjarne Stroustrup was working with
   when he figured this stuff out and thought it was good? one, he's
   doing the same thing we're doing." `[caption ≈00:24:52]`. He repeats
   in the Q&A: "during the course of the development of these core
   ideas, I never once saw anyone talk about that" `[caption ≈01:58:12]`.
4. Discriminated unions predate the class hierarchy in this lineage and
   were dropped from C++ deliberately.
5. Sketchpad's power came from its non-encapsulated runtime structure,
   and Kay explicitly regarded that property as a defect.

**Engineering claims** (his opinions, not established by the history):

1. Encapsulation boundaries drawn around compile-time hierarchies
   matching the domain model are usually more work than they are worth.
   "Sometimes they work like with distributed systems or maybe
   microbiology, but a lot of times they're just more work than they're
   worth" `[caption ≈01:48:32]`.
2. It is "procrustean" — a one-size-fits-all placement. The alternative
   he recommends is not another fixed model: "teaching architecture I
   think it would be better to focus on more flexible thinking and
   thinking about drawing the encapsulation boundaries with intent not
   with a fixed model in mind" `[caption ≈02:20:05]`.
3. He prefers operation-first code and discriminated unions for
   mutually-exclusive cases: "I prefer to write code in like a verb
   oriented way not an object-oriented way" `[caption ≈02:01:08]`, and
   the reason he gives for using a tagged union rather than a fat struct
   is the same reason Stroustrup gave for classes — "the exact same
   reason for [Stroustrup] and everybody else: to catch errors"
   `[caption ≈02:01:33]`.
4. Design for the hardest problems first: "it's almost impossible to
   take something that only solves simple problems and scale it up into
   something that solves hard ones" `[caption ≈02:18:23]`.

He explicitly does *not* claim: that OOP is bad; that encapsulation is
bad ("we can all agree that that's a thing we want to do ... I think
that's certainly a point of commonality", `[caption ≈01:57:19]`); that
virtual functions are useless ("I'm not trying to say that isn't useful.
It's function pointers are good in certain circumstances",
`[caption ≈01:39:50]`); that ECS is good; or that anyone involved acted
badly ("it's nobody's fault", `[caption ≈02:18:23]`).

### Objections from informed critics (HN 44596554, 91 comments)

I pulled the full thread text via the Algolia item API, so these are the
commenters' own words.

**The Kay reading is the strongest specific attack.** `igouy` goes to
page numbers in Kay's *The Early History of Smalltalk* and argues Casey's
"he kind of soured on inheritance" gloss is not supported:

> "Not 'kind-of-soured on it' one page later — 'There were a variety of
> strong desires for a real inheritance mechanism from Adele and me,
> from Larry Tesler, who was working on desktop publishing, and from the
> grad students.' page 83 ... Not 'kind-of-soured on it' but wanting a
> 'comprehensive and clean multiple inheritance scheme'" (p. 84)

`romaniv`: "This video contains many serious misrepresentations. For
example, it makes a claim that Alan Kay only started talking about
message-passing only in 2003 and that it was a kind of backpedaling due
the failures of the inheritance-based OOP model. That is a laughable
claim. Kay had given detailed talks discussing issues of OOP, dynamic
composition and message-passing in mid-80s." Also: "earlier versions of
Smalltalk did not have inheritance."

`Mathnerd314`'s defence, which I think is fair: the dates are the dates
of the *sources*, not of the ideas; and Casey says on stage he "didn't
really cover Alan Kay" — by source count the talk is ~18% Kay. He also
notes Casey's own hedge, "Maybe Alan Kay ... will come to tell us what he
actually was trying to say there exactly."

**The "large teams" premise is challenged as a strawman.** `igouy`
repeatedly asks for a reference: "Is there some example that you can
point me towards, where a lot of people are saying compile time
hierarchies are all about large teams?" The best citation anyone in the
thread produced was Paul Graham's *Why Arc Isn't Especially
Object-Oriented* ("Object-oriented programming is popular in big
companies, because it suits the way they write software..."), and
`Jtsummers` correctly points out it does not support the claim being
rebutted: "Muratori's statement (that he debunks in his talk): OO was
created for teams. Graham's statement: OO is useful for teams. Those are
distinct concepts". Nobody produced a source for the first form.

**The first half is attacked as answering the wrong question.**
`Jtsummers`: "it does not matter why a language or tool or whatever was
made ... Whether it was made for that is immaterial, and no one needs 30
minutes of mostly historically correct video to get to The Truth(tm) of
the matter. What's more interesting, and he never bothered to get into,
is whether OO is *actually* good for working with teams". Same commenter
on accuracy: "It was amusing to hear him talk about Arpanet being used in
the 90s" and "claiming that everything in Lisp was based on lists (even
in 1960 that wasn't true)". Verdict: "the second half is interesting, the
first half is mostly a waste of time."

**Scope omissions.** `hgs3`: "the 'history' omits prototype-based OO
(Self, Io, Lua, etc.) which doesn't suffer from many of the 'issues'
cited by the speaker." `cma`: column-oriented databases (70s–80s) are
missing from the 1963→1998 gap, and are plausibly what actually drove the
ECS resurgence for performance reasons. `crabmusket` notes he "skipped a
fair chunk of the middle" and that Casey "was fairly balanced, and
emphasized near the end of the talk that some of the things under the OOP
umbrella aren't necessarily bad, just overused."

**The "design for the hardest problem" advice.** `abetusk`: "I
understand the context but this, in general, is abysmally bad advice.
I'm not sure about language design or system architecture but this is
almost universally not true for any mathematical or algorithmic
pursuit." `dkbrk` gives the strongest counter-defence (general solutions
often subsume special cases; foundational design decisions are cheap and
high-leverage), and `abetusk` partly concedes.

There is also a long ad-hominem subthread (`_zagj`: Handmade Hero never
shipped, "real heroes ... ship") which does not engage the thesis.

### 2. "Clean Code, Horrible Performance"

Primary source: the computerenhance.com post of 2023-02-28, which is a
free bonus item from the Performance-Aware Programming course and states
"A lightly-edited transcript of the video appears below." The video is
`tD5NrevFtbU` (Feb 2023). I have the full post text and the video's
caption track; they agree except where noted.

### What the benchmark actually varies

The draft's suspicion is correct, and it is stronger than "a union and a
switch". Four things change across the ladder, and only the first is
dispatch:

**(a) Dispatch: virtual call → switch on a tag.** Listing 22/23 is
`class shape_base { virtual f32 Area() = 0; }` with square, rectangle,
triangle, circle; Listing 25/26 is `struct shape_union { shape_type Type;
f32 Width; f32 Height; }` with `GetAreaSwitch`.

**(b) Memory layout and indirection.** This is a separate change bundled
into the same step, and he says so:

> "You may also notice that this loop is over an array of pointers. This
> is a direct consequence of using a class hierarchy: we have no idea how
> big in memory each of these shapes might be."

> "the shapes can just be in an array, no pointers necessary. There is no
> indirection because we've made all our shapes the same size."

So the "clean" side is `shape_base **Shapes` (pointer chase per element,
separate heap objects) and the fast side is `shape_union *Shapes`
(contiguous 12-byte values). That alone is a different memory-traffic
experiment, independent of how the call is made.

**(c) Compiler visibility.**

> "Plus, we get the added benefit that the compiler can now see exactly
> what we're doing in this loop, because it can just look at the
> GetAreaSwitch function and see the entire codepath. It doesn't have to
> assume that anything might happen in some virtualized area function
> only known at run-time."

**(d) The algorithm.** The 10x step is not a dispatch change at all. He
notices the four cases are all `k * w * h`, changes the *representation*
so one-parameter shapes duplicate their width into their height, and
replaces every per-type body with one line:

```
f32 const CTable[Shape_Count] = {1.0f, 1.0f, 0.5f, Pi32};
f32 GetAreaUnion(shape_union Shape) {
    return CTable[Shape.Type]*Shape.Width*Shape.Height;
}
```

That removes the branch *and* the per-type arithmetic. For the second
experiment (corner-weighted area) the constants are folded into the table
too, so the second property costs nothing at all: `{1/(1+4), 1/(1+4),
0.5/(1+3), Pi32}`.

**(e) Hand-written AVX** for the final numbers.

His own summary of what the change is — note that it is not framed as
dispatch: "effectively switching from a type-based mindset to a
function-based mindset".

### The exact numbers he gives

All from the post's prose (the actual result tables in the post are
screenshots; I am not reading numbers off images).

- Virtual (`TotalAreaVTBL`, both the plain and 4-accumulator variants):
  "around 35 cycles ... Maybe it gets down more towards 34 sometimes if
  you're really lucky".
- Switch/union: "24 cycles per shape" — "an immediate 1.5x performance
  increase".
- Table-driven: "3.0-3.5 cycles per shape" — "fully 10x faster or more".
- Corner-weighted area, switch version: "nearly 2x faster".
- Corner-weighted area, table version: "nearly 15x faster".
- AVX vs virtual: "The speed differences range from 20-25x".

The video states the AVX range slightly differently: "in the best case
scenario you're looking at a 21x speed difference between an AVX
optimized routine and the C plus plus v table version and in the worst
case you're looking at more like 24 x".

Hardware-generation analogies he uses: 1.5x = "like taking an iPhone 14
Pro Max and reducing it to an iPhone 11 Pro Max"; 10x = "like going from
the average CPU mark today all the way back to the average CPU mark from
2010"; 15x = "like pushing 2023 hardware all the way back to 2008".

On rule 5: "Honestly, 'don't repeat yourself' seems fine." Final tally:
"out of the five clean code things that actually affect code structure, I
would say you have one you might want to think about and four you
definitely shouldn't."

Methodology detail worth keeping: he times each routine once cold ("the
data should be in L3 but L2 and L1 have been flushed, and the branch
predictor has not 'practiced' on the loop") and then many times hot, and
he hand-unrolls into four accumulators to remove the loop-carried FP
dependency. He also grants the clean side several benefits of the doubt:
no iterators, the corner-weight math left inline rather than pulled into
another function.

### What is *not* in the sources

- **No compiler.** Not named in the post or in the video captions.
- **No flags.** Same.
- **No CPU.** Same. (In the Uncle Bob exchange, on an unrelated point, he
  mentions typing on "a Zen2 chip" — that is about GitHub's editor, not
  this benchmark.)
- **No source.** Listings 22–36 are not in the public
  `cmuratori/computer_enhance` repo; `perfaware/part1` begins at
  `listing_0037`. Nothing under `perfaware/` matches the shape listings.
- Circumstantial only, and I would not state it as fact: the course's
  build scripts are Windows batch files that build each listing with both
  MSVC and clang — `cl -arch:AVX2 -O2 -Zi -W4 -EHsc` and
  `clang++ -mavx2 -O3 -g -Wall` (plus unoptimized debug builds). That is
  the environment the course lives in; it is not evidence about listings
  22–36 specifically.

### What he says the speedup is attributable to

In the post, the attribution is compiler visibility and data/operation
fusion, not dispatch cost:

> "The more you use the 'clean' code methodology, the less a compiler is
> able to see what you're doing. Everything is in separate translation
> units, behind virtual function calls, etc. No matter how smart the
> compiler is, there's very little it can do with that kind of code."

> "And to make matters worse, there's not much you can do with that kind
> of code either!"

And there is a footnote that matters for the draft, because it concedes
the framing point up front:

> "Personally, I wouldn't say that a switch statement is inherently less
> polymorphic than a vtable. They are just two different implementations
> of the same thing. But, the 'clean' code rules say to prefer
> polymorphism to switch statements, so I'm using their terminology
> here"

**The SE Radio interview makes the attribution explicit**, and this is
the single most useful quote for section 3 of the draft:

> "most people look at that video and ... they think that I'm only
> talking about the cost of calling through a V table, but that's not the
> only cost. There are also a lot of optimization costs you pay because
> when you call through a virtual function in languages like C++, if the
> compiler doesn't directly know exactly what type it's dealing with, it
> cannot optimize through that virtual function call. And that is by far
> the biggest cost. Not the dispatch."
> — SE Radio 577, 00:06:12–00:06:54

He continues: "The dispatch can be bad as well, but it's the optimization
cost."

### Does this conflict with the draft's measurement? No.

The draft measured that a hand-rolled C ops-pointer table and C++
`virtual` compile to byte-identical code at gcc 13.3.0 `-O2`. Muratori
never claims otherwise; he says the same thing, in the Uncle Bob
exchange, in as many words:

> "While virtual methods are always implemented with a vtable pointer in
> the object, switch statements can be optimized in a wide variety of
> ways, all of which are more optimal than an indirected function pointer
> **(which is what all virtual calls are)**."

And on devirtualization he states a stricter version of the draft's
finding:

> "The only time you will get similar optimization from a virtual
> function call is if it's not actually virtual because you have an
> explicit pointer to a derived type, and the method has been marked
> 'final' for that type. And that is not a comparable case, because you
> wouldn't need a switch statement to handle that case either."

So: he and the measurement agree that virtual ≡ function pointer, and
that the closed-set case belongs to a tag and a switch. His 10–20x is a
comparison between *virtual dispatch over heap-scattered objects* and
*branch-free table arithmetic over a contiguous array*. It is not a
"C++ vs C dispatch" number and he does not present it as one — but the
video's framing ("polymorphism vs switch") invites that reading, and the
draft is right to say so.

The one place where the identical-code question is argued directly is
Bob Martin's hypothetical compiler, and it is a *different* claim from
the draft's:

> **BOB**: "I propose a hypothetical compiler that produces identical
> binary code irrespective of whether the input is operand or operation
> primal. ... It should be clear that a compiler like this is possible
> since switch statements can be (and often are) compiled as jump
> tables; and polymorphic dispatches can be (and often are) compiled as
> jump tables."

> **CASEY**: "In production, if you are compiling C++, the vast majority
> of programmers will be using CLANG, GCC, or MSVC. None of those do what
> you're describing."

Martin then withdrew it ("I hereby withdraw the hypothetical compiler
from further consideration") and stipulated Casey's revised summary:
"Run-time: Favors operation-primal / Source code: No difference /
Dependency graph: Favors operand-primal". Note the asymmetry the draft
should preserve: Martin claimed *switch ≡ virtual*, which is false on
real compilers; the draft measured *C function pointer ≡ virtual*, which
is true. Different claims.

### The Martin exchange: where they actually disagree

Files: `cleancodeqa.md`, `cleancodeqa-2.md`,
`programmer-cycles-vs-machine-cycles.md` in `unclebob/cmuratori-
discussion`. Martin concedes the measurement immediately:

> **BOB**: "Yes, absolutely, the structures you were presenting are not
> the best way to squeeze every nanosecond of performance out of a
> system. Indeed, using those structures can cost you a lot of
> nanoseconds. They are not efficient at the nanosecond level."

> **BOB**: "It is economically better for most organizations to conserve
> programmer cycles than computer cycles."

**Where they disagree about what the benchmark shows.** Martin reads the
table trick as a resource-constrained special case and a maintainability
liability:

> **BOB**: "The lovely insight that the areas of certain shapes can all
> be calculated using the same basic formula (KxLxW) is one of those
> moments that I think only programmers and mathematicians can truly
> appreciate. ... Clearly (at least I think it should be clear) one would
> not prefer the KxLxW solution in a resource rich environment unless one
> was very sure that the business would not extend the problem to general
> shapes." He then quotes Don Norman: "If you think something is clever
> and sophisticated beware -- it is probably self-indulgence." — "In a
> resource rich environment I fear the KxLxW solution could fall afoul of
> this rule."

Muratori's counter, in the post, is that the compressibility is not a
lucky property of a cherry-picked example:

> "And remember: this is not an example that I picked! This is the
> example that clean code advocates themselves use for illustrative
> purposes. So I didn't intentionally pick an example where you happen to
> be able to pull out a pattern — it's just very likely that you can do
> this, because most things of similar type have similar algorithmic
> structure"

And that the *organisation* of the code is what makes the pattern
visible at all:

> "This is actually one of the reasons that — unlike 'clean' code
> advocates — I think switch statements are great! They make this kind of
> pattern very easy to see. When your code is organized by operation,
> rather than by type, it's straightforward to observe and pull out
> common patterns. By contrast, if you were to look back at the class
> version, you would probably never notice this kind of pattern"

**The architectural disagreement** is dependency inversion. Martin: OO
inverts source dependencies so high-level policy does not depend on
low-level detail. Muratori's reply is a counting argument: with `n` types
and `m` operations you have O(nm) things and are only choosing which
addition is clustered and which is scattered —

> **CASEY**: "So to me, there is no 'win' here in the abstract. You are
> merely choosing *which* programmer behavior you will make hard, and
> which you will make easy."

— plus a claim the draft may find useful, that a vtable is itself a
leaked implementation detail across an ABI boundary:

> **CASEY**: "you *are* actually pushing an implementation detail across
> the boundary with the hierarchy design: you're mandating how operand
> pointers turn into function pointers, which is a *constraint* on the
> layout of the underlying operand. ... This is why, for example, C++
> vtable layouts had to be standardized."

His summary of where they ended: "We disagree on how often they should be
hidden; you think the answer is 'most of the time', I think the answer is
'only in specific circumstances'. We disagree on how important the
computer is."

Martin's own concession on the meta-point:

> **BOB**: "Frankly, I think that's a fair criticism. ... You asked me
> whether I had been taking the importance of performance for granted.
> After some self-reflection I think that's likely. I am not an expert in
> performance." (and, in return: "it is probably for the same reason that
> your video was solely focussed on the amplification of performance to
> the strident denigration of every other concern. To a performance
> hammer, everything looks like a nail.")

Martin's closing position statement, which is *not* the position the
video attacks:

> **BOB**: "Use polymorphism when types change faster than operations.
> Use switch when operations change faster than types. ... Switch
> statements have their place. Dynamic polymorphism has its place."

Muratori's own version of the same trade-off, from the Big OOPs Q&A: "It
also has to do with what type of system you're making whether or not
people are going to be adding types to the system more frequently or
whether they're going to be adding actions. I tend to find that people
add actions more frequently. That's why I focus on that."
`[caption ≈02:01:33]`

### 3. Semantic compression

Primary source: caseymuratori.com/blog_0015, "Semantic Compression",
2014-05-28, part of his Witness series; the follow-up is blog_0016,
"Complexity and Granularity", 2014-06-04. The example is real code — Jon
Blow's Movement Panel UI in The Witness's editor.

### The method

The article opens with a page of straight-faced parody of exactly the
advice a C programmer moving to C++ gets: payroll system, find the plural
nouns, `employee` and `manager`, hoist a `person` base class, discover
that a contract manager breaks the hierarchy, template the manager on its
base class, "As soon as I get all these classes and templates spec'd out,
I'm going to fire up my editor and get to work on the UML diagrams."

The method itself:

> "my experience has led me to conclude that the most efficient way to
> program is to approach your code as if you were a dictionary
> compressor. Like, literally, pretend you were a really great version of
> PKZip, running continuously on your code, looking for ways to make it
> (semantically) smaller. And just to be clear, I mean semantically
> smaller, as in less duplicated or similar code, not physically smaller,
> as in less text, although the two often go hand-in-hand."

The operational rule is a two-instance threshold:

> "Like a good compressor, I don't reuse anything until I have at least
> two instances of it occurring. Many programmers don't understand how
> important this is, and try to write 'reusable' code right off the bat,
> but that is probably one of the biggest mistakes you can make. My
> mantra is, 'make your code usable before you try to make it
> reusable'."

> "I always begin by just typing out exactly what I want to happen in
> each specific case, without any regard to 'correctness' or
> 'abstraction' or any other buzzword, and I get that working. Then, when
> I find myself doing the same thing a second time somewhere else, that
> is when I pull out the reusable portion and share it, effectively
> 'compressing' the code. I like 'compress' better as an analogy, because
> it means something useful, as opposed to the often-used 'abstracting',
> which doesn't really imply anything useful. Who cares if code is
> abstract?"

Why two and not one:

> "Waiting until there are (at least) two examples of a piece of code
> means I not only save time thinking about how to reuse it until I know
> I really need to, but it also means I always have at least two
> different real examples of what the code has to do before I try to make
> it reusable. ... So I try very hard to never make code 'prematurely
> reusable', to evoke Knuth."

The claim about the result — note that it is a readability and
maintainability claim, not a performance one:

> "if you compress your code to a nice compact form, it is easy to read,
> because there's a minimal amount of it, and the semantics tend to
> mirror the real 'language' of the problem ... Well-compressed code is
> also easy to maintain, because all the places in the code that are
> doing identical things all go through the same paths, but code that is
> unique is not needlessly complicated or separated from its use."

And the direct attack on up-front design:

> "the hard part of code is getting the details right. Starting from a
> place where the details don't exist inevitably means you will forget or
> overlook something that will cause your plans to fail or lead to
> suboptimal results. Starting with the details and repeatedly
> compressing to arrive at the eventual architecture avoids all the
> pitfalls of trying to conceive the architecture ahead of time."

The worked example produces a `Panel_Layout` struct with member
functions, and he makes the point explicitly:

> "this is the correct way to give birth to 'objects'. We made a real,
> usable bundle of code and data: the Panel_Layout structure and its
> member functions. It does exactly what we want, it fits perfectly,
> it's really easy to use, it was trivial to design."

> "I spend exactly zero time thinking about 'objects' or what goes where.
> The fallacy of 'object-oriented programming' is exactly that: that code
> is at all 'object-oriented'. It isn't. Code is procedurally oriented,
> and the 'objects' are simply constructs that arise that allow
> procedures to be reused."

He also names a limit in the follow-up article: when the language cannot
express the compression cleanly, take the ugly version. "It's OK to
accept a solution that's a little ugly if the alternatives are uglier.
The important thing to remember is that you must always focus on the end
result. It's easy to fall into the habit of thinking of abstract things
like whether code is 'clean' or whether it is 'elegant'". blog_0016 adds
"continuous granularity" — keeping entry points available at several
levels rather than only the compressed top level; he calls the underlying
idea "multiresolution entry points" and defers it.

### How it relates to the advice a C programmer gets moving to C++

- It inverts the sequence. Received advice: model the domain, define
  interfaces, then fill in implementations. Semantic compression: write
  the concrete duplicated code first, extract only on the second
  occurrence, and let the type fall out.
- It is compatible with DRY and with refactoring — he says so, grudgingly:
  "a pseudo-variant of which has recently gained the monicker
  'refactoring', even though that is a ridiculous term ... they are
  sort-of related". Consistent with his acceptance of DRY as the one
  clean-code rule he keeps.
- It is *not* compatible with designing an interface in order to make
  code testable or to invert dependencies before you have two callers.
  That is precisely the Martin position from the exchange in §2.
- It is directly relevant to the draft's section-3 observation that the
  hand-rolled C vtable example was "built backwards from the C++
  answer". Semantic compression is the argument for why you would never
  arrive at that structure in the first place: you would have written the
  two concrete cases, seen the tag, and compressed to a switch.

### 4. Does he take a position on which C++ features are acceptable?

Yes, but scattered and mostly negative. What I can source:

**Overall stance** — SE Radio 577, 00:45:11:

> "It's not so much that I don't want everyone to start programming C++.
> In fact, I don't really like C++ very much to be honest. I program in a
> very like light C++, it's more C like, right?"

**Accepted, on the record:**

- *Static type checking.* He credits Stroustrup for it directly: "it kind
  of sounds to me like [Stroustrup] was really important in getting type
  checking for us. Like C did not even type check function calls at the
  time" `[caption ≈01:44:40]`. Also: "I do think the type-checking part
  is pretty good. maybe the class part or rather the hierarchy part that
  I'm like a little bit suspicious of" `[caption ≈00:21:26]`.
- *Templates / parameterized types over inheritance-for-reuse*, siding
  with Stroustrup's own later position `[caption ≈00:30:11]`.
- *Interfaces as a bare concept.* "it's not like we can't think of uses
  for things like virtual functions [and] classes like interfaces — just
  that bare concept is a place where we still use those things today
  [in] even new languages" `[caption ≈01:45:37]`.
- *Function pointers* "are good in certain circumstances"
  `[caption ≈01:39:50]`.
- *Exposed struct definitions in headers* when the type is stable — for
  both speed and comprehension (SE Radio 00:18:04: "anytime we have a
  data type that we're very confident we don't need to change, we will
  expose it to you ... the code gets faster when they compile because
  their code doesn't have to call accessor functions that they can't
  see").

**Rejected or disparaged:**

- *Inheritance hierarchies as the default polymorphism mechanism.*
  "discriminated unions ... seem to always be the better rule of thumb"
  (cleancodeqa), and the hierarchy version is "worse at both ends" of the
  isolation/performance spectrum.
- *`std::variant`.* "C++ also has a janky std library version of these
  called 'variants'" (cleancodeqa); "standard variant is not very good in
  my opinion. the real thing that Tony Hoare wanted would would have been
  great" `[caption ≈02:01:56]`; and a slide in the deleted-scenes segment
  was, in his words, "me making fun of standard variant"
  `[caption ≈02:08:21]`.
- *Language size.* "some modern language like C++ with its thousands of
  features" (SE Radio 01:05:57).
- *`new`/`delete` and fragmentation* is described as the failure mode that
  broke Flight Unlimited: "they were using new and delete like you're
  supposed to do in C++. And unfortunately, that totally fragmented
  memory" `[caption ≈02:08:46]`.

**Where even library-boundary polymorphism is allowed** — this is his
sharpest scoping statement, and it lines up with the draft's "open set"
criterion:

> "I think the idea of structuring code around swappable types is
> generally wrong. I think it should only be used when you are
> specifically designing the boundary of a library or plug-in system, and
> rarely anywhere else. I really am 'operation first', never 'operand
> first'." (cleancodeqa)

**Not found in any source I fetched:** a position on RAII/destructors,
exceptions, references, `constexpr`, `iostream`, or `override`. The
`-EHsc` in his course build scripts is not a statement of position. If
the draft's section 4 wants him as a witness for a specific C++ subset,
the only citable line is "a very light C++, it's more C like."

### 5. Orthodox C++ and Eskil Steenberg's Dependable C

**No primary source found for either.** Searching turned up the Orthodox
C++ gist/post (Branimir Karadžić) and Dependable C (dependablec.org) with
no Muratori response, and no Muratori commentary on Steenberg's "How I
Program C". The one adjacency is community, not engagement: Handmade
Network episode 13 is an interview with Eskil Steenberg, hosted by Abner
Coimbre — Muratori is not a participant. The Handmade Network's own
framing names Muratori as an influence on the community, which is not the
same as him endorsing either project.

Treat this as "not found", not "he has no position". The likely venues
for such a statement — Handmade Hero Q&A segments and his Twitter — are
thousands of hours of video and a deleted-ish timeline, and I could not
search them.

### Claims that are secondhand or otherwise weakly sourced

Flag these if any of them make it into the post.

1. **All Big OOPs quotations.** From YouTube auto-generated captions, not
   an authored transcript. Substance primary; wording is ASR. Do not
   present any of them as a written quotation, and fix names silently
   only if you also note the source.
2. **"Marc LeBlanc" as the author of the compile-time-hierarchy quote.**
   My identification from garbled caption names plus context.
3. **The Frontend Masters writeup.** Not fetched (403/429). Nothing in
   these notes derives from it, and I cannot confirm or deny anything it
   says.
4. **The clean-code benchmark's compiler, flags, CPU, and source.** Not
   stated in the post, not stated in the video, not in the public repo.
   The MSVC/clang flags I list are from *other* listings' build scripts
   and are circumstantial.
5. **The clean-code result tables.** Screenshots in the post; every
   number I quote is from his prose, so the table may contain finer
   figures I have not seen.
6. **The HN claim that Muratori refused to produce a transcript**
   (`lproven`: "I asked him on Twitter. The answer was a simple 'sorry,
   no.'"). Uncorroborated.
7. **"First commercially released ECS."** His own hedge, twice: "to the
   best of my knowledge" and "the first time I'm ever aware of anyone".
8. **Kay attributions.** Both the "most significant single thesis ever
   done" praise and the closing "most treacherous metaphors" quote are
   read off slides in the talk; I have not verified either against Kay's
   published text. The HN thread demonstrates that at least one Kay
   attribution in the talk is contested on page-level evidence.
9. **The plex as the earliest structured-data record.** He says so and
   explicitly asks to be corrected: "If anyone out there reads this and
   knows of an earlier example than the plex, please let me know!"

### Reading list — URLs actually fetched

- https://www.computerenhance.com/p/the-big-oops-anatomy-of-a-thirty
- https://www.youtube.com/watch?v=wo84LFzx5nI (auto-caption track, en, via yt-dlp)
- https://news.ycombinator.com/item?id=44596554
- https://hn.algolia.com/api/v1/items/44596554 (full comment text of the above)
- https://www.computerenhance.com/p/clean-code-horrible-performance
- https://www.youtube.com/watch?v=tD5NrevFtbU (auto-caption track, en, via yt-dlp)
- https://se-radio.net/2023/08/se-radio-577-casey-muratori-on-clean-code-horrible-performance/ (full transcript)
- https://raw.githubusercontent.com/unclebob/cmuratori-discussion/main/cleancodeqa.md
- https://raw.githubusercontent.com/unclebob/cmuratori-discussion/main/cleancodeqa-2.md
- https://raw.githubusercontent.com/unclebob/cmuratori-discussion/main/programmer-cycles-vs-machine-cycles.md
- https://caseymuratori.com/blog_0015 (Semantic Compression)
- https://caseymuratori.com/blog_0016 (Complexity and Granularity)
- https://caseymuratori.com/contents
- https://api.github.com/repos/cmuratori/computer_enhance/contents/perfaware (+ part1, part2, part3)
- https://raw.githubusercontent.com/cmuratori/computer_enhance/main/perfaware/part2/build.bat
- https://raw.githubusercontent.com/cmuratori/computer_enhance/main/perfaware/part2/build_single.bat
- https://raw.githubusercontent.com/cmuratori/computer_enhance/main/perfaware/part3/build.bat
- https://mollyrocket.com/handmade
- https://handmade.network/forums/show/t/2942-handmade_ep_13__eskil_steenberg

Attempted and failed:

- https://frontendmasters.com/blog/the-big-oops-anatomy-of-a-thirty-five-year-mistake/ — 302 to blog.master.dev (403); direct fetch 429 twice

---

## The other side, argued at its strongest

### 1. The mainstream position on subsetting

### Stroustrup's own verdict on "C with Classes"

"C with Classes" is not a rhetorical label invented by its critics; it is
the name of a real language Stroustrup shipped and then abandoned. His
HOPL-II history gives the reason, and the reason is exactly the one a
subsetter would least like to hear — the restricted feature set was the
limiting factor:

> The success of C with Classes was, I think, a simple consequence of
> meeting its design aim: C with Classes did help organize a large class of
> programs significantly better than C without the loss of run−time
> efficiency and without requiring enough cultural changes to make its use
> infeasible in organizations that were unwilling to undergo major changes.
> The factors limiting its success were partly the limited set of new
> facilities offered over C and partly the pre−processor technology used to
> implement C with Classes. There simply wasn't enough support in C with
> Classes for people who were willing to invest significant efforts to reap
> matching benefits: C with Classes was an important step in the right
> direction, but only one small step.

— Stroustrup, *A History of C++: 1979−1991*, §3 "From C with
Classes to C++"

Two things are worth noting for the draft. First, the same paper is where
the "affordability" principle is stated, and it is stated as a constraint on
*adding* features, not on removing them: "it was not sufficient to provide a
feature, it had to be provided in an affordable form" (§2.4.1). Second,
Stroustrup's account of why `inline` is a programmer-controlled keyword
rather than a compiler heuristic is a first-principles anti-magic argument
that the anti-abstraction camp would endorse verbatim: "I had poor
experiences with languages that left the job of inlining to compilers
'because clearly the compiler knows best.'"

### The Core Guidelines are explicitly not a subset

The C++ Core Guidelines state their design principle in the first rule,
In.0, and it is a direct answer to the subsetting position:

> These guidelines are designed according to the "subset of superset"
> principle ([Stroustrup05]). They do not simply define a subset of C++ to
> be used (for reliability, safety, performance, or whatever). Instead, they
> strongly recommend the use of a few simple "extensions" (library
> components) that make the use of the most error-prone features of C++
> redundant, so that they can be banned (in our set of rules).

And In.not:

> The rules are not intended to force you to write in an impoverished subset
> of C++. They are *emphatically* not meant to define a, say, Java-like
> subset of C++. They are not meant to define a single "one true C++"
> language. We value expressiveness and uncompromised performance.

The argued cost of a hand-rolled restricted subset is stated in In.0 as
well, and it is the strongest single sentence on this side:

> Build your ideal small foundation library and use that, rather than
> lowering your level of programming to glorified assembly code.

Note also that In.0 explicitly *blesses* domain restrictions as addenda
rather than treating them as heresy: "We expect that most large
organizations, specific application areas, and even large projects will need
further rules, possibly further restrictions, and further library support.
For example, hard-real-time programmers typically can't use free store
(dynamic memory) freely and will be restricted in their choice of
libraries." So the mainstream position is not "never restrict"; it is
"restrict by adding a better primitive, not by subtracting and open-coding
the replacement."

The Guidelines' own advice to a C programmer is CPL.1 "Prefer C++ to C" and
CPL.2 "If you must use C, use the common subset of C and C++, and compile
the C code as C++", justified as "when compiled as C++ is better type
checked than 'pure C.'"

### "Remember the Vasa!", read the other way round

P0977r0 is quoted constantly as committee-insider support for shrinking C++.
Read whole, it is a warning about *uncoordinated growth*, and it contains an
explicit repudiation of the subsetting reading:

> There are people who concluded from the Vasa story that all incremental
> improvement is a bad strategy. However, if the Vasa had been sent to sea
> as originally designed, it could not have served its purpose. Being
> under-gunned, someone would have sent it to the bottom full of holes. […]
> so my reading of the Vasa story is: Work hard on a solid foundation, learn
> from experience, and don't scrimp on the testing.

The paper's actual complaint is about surface complexity added without
integration — "it added significant surface complexity and increased the
number of features people need to learn" — and its target audience is
"'ordinary programmers' whose main concern is to ship great applications on
time." It never proposes a subset.

### The one Stroustrup quote the subsetters use, and his gloss on it

"Within C++, there is a much smaller and cleaner language struggling to get
out" is from *The Design and Evolution of C++*, p. 207, in a section called
"Beyond Files and Syntax". On his own quotes page Stroustrup says the
smaller cleaner language is not Java or C#, that he was "pointing out that
the C++ semantics is much cleaner than its syntax", and that he "was
thinking of programming styles, libraries and programming environments that
emphasized the cleaner and more effective practices over archaic uses
focused on the low-level aspects of C."

That is a specific and checkable claim: the quote is about *style and
libraries*, and the "archaic uses focused on the low-level aspects of C" are
the thing being criticised — i.e. roughly the target the Orthodox C++
position occupies. Anyone citing the quote in support of a C-flavoured
subset is citing it against its author's stated meaning. Worth saying
plainly in the draft.

### The anti-paradigm argument (P0976R0)

P0976R0, "The Evils of Paradigms, or Beware of one-solution-fits-all
thinking", is the sharpest mainstream statement and it is short enough to
mine directly:

> I think the very notion of a paradigm does harm to use and to design
> because people all too easily fall into the trap of considering only one
> paradigm "good" and then try to fit everything into it, discarding all
> aspects of alternative "paradigms" as wrong or inferior (aka "If your only
> tool is a hammer, everything looks like a nail").
>
> I reject that notion, as did Kristen Nygaard, who invented object-oriented
> programming.

On error handling specifically, and directly relevant to a codebase-level
ban:

> The real problem was and is that it is really hard to deal with a
> multiplicity of error-reporting mechanisms: errno (yuck!), returning a
> struct, a std::pair, a std::optional, a pointer that might be the nullptr,
> an int that might be -1, an "expected", an out-parameter, or simple
> termination. Adding a mechanism to "solve the error-signaling problem" is
> more likely to add yet-another-alternative to this mess, than to solve it;
> as a user of N libraries, I now potentially have N+1 ways of signaling
> errors to deal with.

And the honest closing line, which belongs in the draft's §5 discussion:

> Unfortunately, data necessary to resolve "paradigm choices" is hard to
> come by and available data is often ambiguous, biased, or hard to
> translate into concrete design choices.

### 2. The exceptions case, argued well

### P0709 is the strongest indictment of exceptions, written by a defender

Sutter's *Zero-overhead deterministic exceptions: Throwing values* (P0709R0,
2018-05-02) is the document to cite for both halves. It is far harsher on
today's exceptions than the draft's §5 currently is.

The indictment (§2.5, "Root causes"):

> The root cause of these problems is that today's dynamic exception
> handling model violates two of C++'s core principles, zero-overhead and
> determinism, because it requires: • throwing objects of dynamic types,
> which requires dynamic allocation and handling; and • using non-local
> by-reference propagation and handling semantics, which requires non-local
> coordination and overheads […]

> Exception handling is one of two C++ language features that violates the
> zero-overhead principle […] For example, just turning on exception
> handling support in a project previously compiled without exception
> support — i.e., one that is not yet throwing any exceptions at all —
> commonly incurs significant binary space overhead; I regularly hear +15%
> reported (Chris Guzak in personal communication regarding Windows internal
> examples, and +16% reported by Ben Craig on the SG14 mailing list for a
> different code base and environment), and I have recently seen other
> Windows internal examples with +38% bloat, down from +52% after recent
> additional back-end optimization (Ryan Shepherd, personal communication).

> This is an intolerable rift: Large numbers of "C++" projects are not
> actually using standard C++.

Note the survey number, which is a better citation than "Google banned
exceptions": in the 2018 Standard C++ Foundation developer survey, "52% of
C++ developers reported that exceptions were banned in part or all of their
project code". Sutter also points out that JSF++ — the Joint Strike Fighter
standard co-authored by Stroustrup and hosted on Stroustrup's own site —
bans exceptions. That is a much stronger version of the draft's "some
restrictions are cargo-culted" line: the bans are endorsed by the model's
own advocates.

The defence of the model, in the same paper (§3.1). The table is the useful
artefact; the prose around it is the argument:

> Group B: True errors (as opposed to partial-success or other
> success-with-info) are important and should be handled even if by
> explicitly doing nothing. Any approach that allows them to be silently
> ignored will incur long-term cost to program robustness and security, and
> to a language's reputation.

> But switching to error codes isn't the answer either — error codes cannot
> be used in constructors and operators, are ignored by default, and make it
> difficult to separate error handling from normal control flow.

> The one place that exception handling fails the ideals shown here is that
> exception propagation between the throw site and the catch handler is
> invisible in source code, which makes exception-neutral code (which
> predominates) harder to reason about and is primarily addressed by
> widespread use of RAII stack-based variables.

Sutter's framing of the terminology is worth quoting in the draft verbatim,
because it settles a definitional fight:

> Importantly, "zero overhead" is not claiming zero cost — of course using
> something always incurs some cost. Rather, C++'s zero-overhead principle
> has always meant that (a) "you don't pay for what you don't use" and (b)
> "when you do use it you can't [reasonably] write it more efficiently by
> hand."

And on the security consequence of banning RTTI (which is the exceptions
ban's companion in practice, since `catch` matching needs type identity):

> The projects work around their lack of dynamic_cast by using static_cast
> downcasts, using a visitor pattern, or rolling their own homegrown dynamic
> casting method (e.g., storing a type tag for a known class hierarchy,
> which does not scale universally). This continues to cause new C++ code
> security exploits due to type confusion vulnerabilities, where the root
> cause analysis of many recent security incidents has observed that the
> code should have used dynamic_cast, but did not because of its binary
> image space and/or run-time costs (for example, see [Lee 2015] […])

`[Lee 2015]` is B. Lee, C. Song, T. Kim, W. Lee, "Type Casting Verification:
Stopping an Emerging Attack Vector", 24th USENIX Security Symposium — i.e.
there is a real citation behind that claim, not just an assertion.

### The one hard datum where exceptions won a measured head-to-head

P0709 §4.1.5 quotes Joe Duffy on Midori, whose exception model was
isomorphic to error codes and so could be compiled either way — the only
apples-to-apples comparison I found anywhere:

> "A nice accident of our model […] was that we could have compiled it with
> either return codes or [table-based] exceptions. Thanks to this, we
> actually did the experiment, to see what the impact was to our system's
> size and speed. The exception[-table]s-based system ended up being roughly
> 7% smaller and 4% faster on some key benchmarks." — [Duffy 2015]

This is the number to use if the draft wants one, and its caveats should
travel with it: it is Midori's model, not C++'s, and "some key benchmarks"
is not "all benchmarks".

### The Core Guidelines' rebuttal list (NR.3, "Don't avoid exceptions")

NR.3 enumerates the four objections and answers each. The two answers most
relevant to the draft:

> * Exceptions are inefficient: Compared to what? When comparing make sure
> that the same set of errors are handled and that they are handled
> equivalently. In particular, do not compare a program that immediately
> terminates on seeing an error to a program that carefully cleans up
> resources before logging an error.

> * The exception-handling run-time support takes up too much space. This
> can be the case in small (usually embedded) systems. However, before
> abandoning exceptions consider what space consistent error-handling using
> error-codes would require and what failure to catch an error would cost.

And the concessions, which the draft should keep because they make the rest
credible:

> There are specialized applications where exceptions indeed can be
> inappropriate (e.g., hard-real-time systems without support for reliable
> estimates of the cost of handling an exception).

> If your system consists of a million lines of such code, you probably will
> not be able to use exceptions, but that's a problem with excessive and
> undisciplined pointer use, rather than with exceptions.

E.27, "If you can't throw exceptions, use error codes systematically", is
the other half of the argument delivered as code rather than prose: it walks
through `std::pair<Gadget, error_indicator>`, then the multi-resource
cleanup version, then concedes the `goto` version. Its own summary:
"Simulating RAII can be non-trivial, especially in functions with multiple
resources and multiple possible errors."

### The empirical record on error-code discipline

This is where the draft's §5 currently has a claim I could not support (see
§6 below). What *is* sourceable:

**EIO: Error Handling is Occasionally Correct** (Gunawi, Rubio-González,
Arpaci-Dusseau, Arpaci-Dusseau, Liblit; FAST '08). Static dataflow analysis
of every filesystem plus SCSI/IDE/software-RAID in Linux 2.6 — pure C, pure
error-code discipline:

> Running our EDP analysis on all file systems and 3 major storage device
> drivers in Linux 2.6, we find that errors are often incorrectly
> propagated; 1153 calls (13%) drop an error code without handling it.

> In conclusion, error propagation appears complex and hard to perform
> correctly in modern systems.

Per-subsystem, from their figures: HFS+ 22/84 (26%), ext3 37/188 (20%), IBM
JFS 61/340 (18%), ReiserFS 35/218 (16%), NFS client 54/446 (12%), XFS
105/1453 (7%). Their finding that this is often deliberate is the strongest
part for the draft: "many violations are not corner-case mistakes: the
return codes of some functions are consistently ignored, which makes us
suspect that the omissions are intentional."

**Simple Testing Can Prevent Most Critical Failures** (Yuan et al., OSDI
'14). Widely cited on this topic, and it needs a caveat the draft should not
omit:

> almost all (92%) of the catastrophic system failures are the result of
> incorrect handling of non-fatal errors explicitly signaled in software.

> In fact, in 35% of the catastrophic failures, the faults in the error
> handling code fall into three trivial patterns: (i) the error handler is
> simply empty or only contains a log printing statement, (ii) the error
> handler aborts the cluster on an overly-general exception, and (iii) the
> error handler contains expressions like "FIXME" or "TODO" in the comments.

The caveat: four of the five systems studied (HDFS, Hadoop MapReduce, HBase,
Cassandra) are Java, i.e. exception-based, and pattern (ii) is an
exception-specific failure mode. So this paper does *not* support
"exceptions beat error codes"; it supports the weaker and more interesting
claim that error-handling code is undertested regardless of mechanism. Only
Redis in that set is C. Using it as pro-exception evidence would be a
misreading.

### Google and LLVM in their own words, and whether they revisited

Google's C++ Style Guide is the single most useful quote for the draft's §4,
because it is a retraction in place:

> On their face, the benefits of using exceptions outweigh the costs,
> especially in new projects. However, for existing code, the introduction
> of exceptions has implications on all dependent code. […] Given that
> Google's existing code is not exception-tolerant, the costs of using
> exceptions are somewhat greater than the costs in a new project.

> Our advice against using exceptions is not predicated on philosophical or
> moral grounds, but practical ones. Because we'd like to use our
> open-source projects at Google and it's difficult to do so if those
> projects use exceptions, we need to advise against exceptions in Google
> open-source projects as well. Things would probably be different if we had
> to do it all over again from scratch.

That last sentence is the whole "some restrictions are cargo-culted"
argument, conceded by the most-cited banner. The ban is a compatibility
artefact of a codebase started in 1998, not a technical verdict. It has not
been lifted; the text has stood, unchanged in substance, for well over a
decade, and Chromium still compiles with exceptions disabled.

Google's RTTI section is a weaker case, because there the rationale *is*
design-based rather than legacy-based: "Querying the type of an object at
run-time frequently means a design problem", plus "Undisciplined use of RTTI
makes code hard to maintain. It can lead to type-based decision trees or
switch statements scattered throughout the code". Note the irony worth a
sentence in the draft: the stated objection to RTTI is that it degenerates
into type switches, and the recommended replacement (LLVM's
`classof`/`isa<>`) *is* a type switch.

LLVM's own words are short and are about the zero-overhead principle rather
than about design:

> In an effort to reduce code and executable size, LLVM does not use
> exceptions or RTTI (runtime type information, for example,
> `dynamic_cast<>`). These two language features violate the general C++
> principle of "you only pay for what you use", causing executable bloat
> even if exceptions are never used in the code base, or if RTTI is never
> used for a class.

> LLVM does make extensive use of a hand-rolled form of RTTI that use
> templates like `isa<>`, `cast<>`, and `dyn_cast<>`. This form of RTTI is
> opt-in and can be added to any class.

I found no LLVM RFC revisiting either ban; the rule text is stable across
releases from LLVM 4 to LLVM 22. In the archival llvm-dev thread on the
topic, Duncan Sands calls it "a definite design rule" and Alasdair Grant
gives the rationale as enabling "doing optimization and codegen on very
constrained platforms". No participant argues the reasons are historical.
So: Google's ban is documented as legacy; LLVM's is documented as a live
engineering choice. The draft should not lump them.

### Where the mainstream is going: fix the cost, don't accept the ban

Sutter's CppCon 2019 talk, *De-fragmenting C++: Making exceptions and RTTI
more affordable and usable*, is the follow-through, and it carries data the
draft's §8 can use directly. From the 2019 Standard C++ Foundation survey
(N≈2,058): RTTI is "not allowed" in 18% of projects and partially allowed in
14%; every run-time casting method — including hand-rolled type tags — is
banned outright in more than 20% of projects, which he labels "a measure of
fragmentation into dialects" and notes is "Worse than EH's 10%".

The slides also record the root-cause chain for type-confusion CVEs as
`can't afford RTTI → static_cast downcast → type confusion`, and present
**CastGuard** (Peter Collingbourne, Kostya Serebryany of Google; Jim
Radigan, Joe Bialek of Microsoft) as the fix: a Clang-CFI-based *range
check* on `static_cast` downcasts, no ABI or vtable change, no RTTI, "Check
is a simple range check. No tree walks. Vtables are arranged in memory so
'IS-A related type' is a SUB", constant time within a DLL, with "Current
worst case: One Windows DLL has +1.5% binary size".

That is the shape of the mainstream reply to Orthodox C++ on RTTI: the cost
model is a fixable implementation property, not a property of the feature.

Status, stated honestly: P0709 reached R4 (2019) and then stalled; I found
no later revision. Lewis Baker's P3166R0 (2024-03-16), "Static Exception
Specifications", picks up the same goal with a different design and
acknowledges P0709R4's motivation while avoiding "yet another error-handling
mechanism". P3166R0 restates the performance claim — "In some cases, taking
the exceptional path can be 100-1000x slower than the normal return-path" —
but presents no benchmarks of its own. Neither proposal is in a standard as
of my sources.

### Measured here: the global-unwinder-lock result no longer reproduces

Thomas Neumann's P2544R0 (2022), "C++ exceptions are becoming more and more
problematic", is the best-measured critique of exceptions in the paper
record. Its central mechanism claim: "exception unwinding is effectively
single-threaded, because the table driven unwinder logic used by modern C++
compilers grabs a global mutex to protect the tables from concurrent
changes." His numbers: on a Ryzen 9 5900X, 10% failure rate with 12 threads
took 247 ms versus 19 ms single-threaded.

This is the kind of number that becomes folklore, so I re-ran the scenario.
Machine: Intel i5-12600K (10 physical cores, 16 logical), Ubuntu 24.04, gcc
13.3.0, glibc 2.39, `-O2 -pthread`. Program: 2,000,000 `sqrt`-or-`throw`
iterations per thread, catch in the immediate caller, one frame unwound;
failure rate varied.

| failure rate | 1 thread | 12 threads | 16 threads | total throw/s, 1 → 16 thr |
|---|---|---|---|---|
| 0%   | 4.4 ms  | 7.0 ms   | 7.0 ms   | — |
| 0.1% | 4.8 ms  | 8.5 ms   | 8.6 ms   | 0.4 → 3.7 M/s |
| 1%   | 16.1 ms | 23.2 ms  | 25.0 ms  | 1.2 → 12.8 M/s |
| 10%  | 104.4 ms| 177.9 ms | 224.2 ms | 1.9 → 14.3 M/s |

Throughput scales roughly with physical core count; wall time for the same
per-thread work grows 1.7x going from 1 to 12 threads, not 13x. The
serialisation is gone. Mechanism, verified rather than assumed: `objdump -T
/lib/x86_64-linux-gnu/libgcc_s.so.1` shows the unwinder importing
`_dl_find_object@GLIBC_2.35` — the lock-free replacement for the
`dl_iterate_phdr` path that took the loader lock. So Neumann's measurement
was correct and is now largely a toolchain-generation artefact on glibc ≥
2.35 / gcc ≥ 12.

Single-frame throw+catch cost on this machine, derived from the same runs
(subtracting the 0% baseline): roughly 200–600 ns per throw. That is the
number to quote against "exceptions are slow" — three orders of magnitude
above a branch, and utterly irrelevant unless failures are routine.

### 3. The zero-cost-abstraction claim, examined

### Who claims what, precisely

Stroustrup, "Foundations of C++" (ETAPS 2012 keynote), is the canonical
statement, and the wording matters:

> In general, C++ implementations obey the zero-overhead principle: What you
> don't use, you don't pay for [BS94]. And further: What you do use, you
> couldn't hand code any better.

He immediately qualifies it, in a sentence that never travels with the
quote:

> Naturally, not every application meets these ideals and C++ provides no
> mechanisms for enforcing ideals.

The Core Guidelines restate it as a design constraint on the guidelines
themselves (In.aims): "they are meant to follow the zero-overhead principle
('what you don't use, you don't pay for' or 'when you use an abstraction
mechanism appropriately, you get at least as good performance as if you had
handcoded using lower-level language constructs')."

**Finding: "zero-cost abstraction" is not Stroustrup's phrase.** I grepped
every Stroustrup document I fetched — ETAPS 2012, HOPL-II, P0976, P0977 —
plus the full Core Guidelines. Every occurrence is "zero-overhead", never
"zero-cost". Search results and secondary blogs routinely assert he "coined
the term zero-cost abstractions"; I could not source that anywhere. The
distinction is not pedantry: it is exactly the distinction Sutter has to
spell out in P0709 ("'zero overhead' is not claiming zero cost — of course
using something always incurs some cost"), and it is the distinction
Carruth's talk title trades on. If the draft uses the phrase, it should
attribute it to common usage, not to Stroustrup.

### What Carruth actually argues

*There Are No Zero-cost Abstractions* (CppCon 2019). His own abstract: "C++
is often described as providing zero-cost abstractions. Libraries offer up
facilities documented as such…" and the talk "challenges this conventional
wisdom". Slides were never posted to the CppCon2019 repository; what follows
is from the YouTube auto-generated captions, which I cleaned into a
transcript — so treat the wording as approximate and the substance as
reliable.

He opens by retracting his own past advocacy: he says he has talked about
zero cost abstractions at CppCon before and "maybe even advocated that you
all should use zero cost abstractions", and is "here to kind of apologize
and say that I was wrong a lot of other people were wrong and in fact there
are no zero cost abstractions and imagining that there are is causing us
serious problems".

The framework is three cost dimensions — runtime, build time, human time —
and three case studies, one per dimension:

1. **Build time.** Protocol-buffer arena allocation at Google. The runtime
   cost was optimised to near zero; nobody benchmarked compile time. From
   late 2013 the p90 and p99 per-file compile times bent sharply upward, and
   builds were "routinely hitting a 15-minute compile time out" for a single
   C++ file. His summary: "moving abstractions from runtime to compile time
   doesn't make them free doesn't make it zero cost it just means the cost
   is paid somewhere else". Modules helped with the quadratic scaling but
   "they don't make protocol buffers free".
2. **Runtime.** `std::unique_ptr` passed by value is not free relative to a
   raw pointer, because the Itanium ABI passes a non-trivially-destructible
   type in memory and C++ has no destructive move. "getting this abstraction
   to be zero cost is roughly the same as causing memory latency to be zero
   which we can't do because of the speed of light". Fixing it needs an ABI
   break *and* destructive move; `[[trivial_abi]]` doesn't work because
   moving destruction into the callee un-nests object lifetimes.
3. **Human time.** His over-factoring story: he took a 400-line function,
   correctly criticised as unreadable, split it into helpers as advised,
   "and I got to the end of it and I looked at my code and I couldn't read
   it".

Crucially — and this is the half the anti-abstraction camp drops — his
conclusion is not "avoid abstractions". His prescriptions are: use the
simplest abstraction that works ("don't use a type when a function would do
just fine, don't use a template when a function would do just fine, and
please don't use generated code"); decide deliberately where to pay the
cost; reduce it; and "please please please please measure that cost […] it's
really important to measure the places where you expect the cost to be
zero". His explicit disclaimer: "I don't want your takeaway from all this
talk to be gosh our abstractions bad […] abstractions are like fire". And
the reason zero-cost framing is the actual problem: "when you imagine you
have zero cost you stop making a trade-off […] as soon as you make it not
zero cost you can have a trade-off discussion".

Two further documented failures he names in Q&A, both useful and both cheap
to state: `std::tuple`'s compile-time cost; and lambdas, where dead code in
the body still forces captures because "the ABI decides on the exact capture
size and capture list before anything like optimizations are applied", plus
no empty-base optimisation for captures. Also the tagged-integer case:
splitting one type into two forces two `std::vector` instantiations, "which
is going to require generating twice as much code", and at scale i-cache
pressure is a real runtime cost from a purely compile-time abstraction.

### Measured here: where the claim holds and where it fails

Machine and toolchain as above (i5-12600K, gcc 13.3.0, clang 18.1.3).

**(a) Carruth's `unique_ptr` result still reproduces, and is not about
exceptions.** His exact example (`void foo(unique_ptr<T> p) { bar(p.get());
baz(std::move(p)); }` vs the raw-pointer equivalent), `-O2
-fno-stack-protector`:

| | gcc 13.3 | clang 18 |
|---|---|---|
| raw pointer, hot path | 7 instructions, 0 memory ops, tail call | 6 instructions, 0 memory ops |
| `unique_ptr` by value, `-fno-exceptions` | 18 instructions, 5 memory ops, no tail call | similar |
| `unique_ptr` by value, `-fexceptions` | + landing pad (9 more insns) + LSDA table | + landing pad + LSDA |

The `unique_ptr` version loads through the incoming pointer, stores the
value to the stack, passes the *address* of the by-value parameter, reloads
it after the call, null-tests it and branches to `operator delete`. The
important detail for the draft's §4/§5: `-fno-exceptions` removes the
landing pad and the exception table but **not** the extra memory traffic.
Banning exceptions does not make `unique_ptr` free; the residual cost is the
ABI.

**(b) Container/iterator/algorithm abstractions really are free at `-O1` and
above, and expensive at `-O0`.** Summing 4 Mi `int`s, 40 reps, total ms:

| | gcc -O0 | gcc -O2 | clang -O0 | clang -O2 |
|---|---|---|---|---|
| raw pointer loop | 262 | 20.0 | 98 | 23.4 |
| `vector::operator[]` | 230 | 18.2 | 175 | 23.2 |
| `vector::at()` | 566 | 18.4 | 456 | 22.1 |
| iterator loop | 757 | 19.0 | 604 | 25.2 |
| range-`for` | 504 | 18.5 | 432 | 30.7 |
| `std::accumulate` | 455 | 18.4 | 423 | 23.8 |
| raw + inline lambda | 241 | 23.8 | 169 | 31.0 |
| raw + `std::function` | 2147 | 169.5 | 1078 | 144.0 |

Read across the `-O2` columns: every STL abstraction except `std::function`
is within noise of the hand-written loop, which is the zero-overhead claim
holding exactly as advertised. Read down the `-O0` columns: the iterator
loop is 2.9x (gcc) / 6.1x (clang) the raw loop and `at()` is 2.2x / 4.6x.
This is the strongest *pro*-subsetting datum in the whole file, and it is a
debug-build argument, not a release-build argument — which is precisely why
game and emulator people, who debug at `-O0`, feel it and server people
don't.

`std::function` is the clear, reproducible failure of the claim: 7-8x the
raw loop at `-O2`, on both compilers, in a case where the target is
statically known and could in principle be devirtualised. That belongs in
the draft as a named exception rather than a general indictment.

**(c) Compile-time cost of headers is real but small; the folklore
overstates it.** Time to compile a TU containing only `#include <X>` and an
empty `main`, `-std=c++20 -O2 -c`:

| header | gcc | clang |
|---|---|---|
| (nothing) | 0.01 s | 0.01 s |
| `<variant>` | 0.04 | 0.04 |
| `<algorithm>` | 0.07 | 0.09 |
| `<vector>` | 0.08 | 0.10 |
| `<string>` | 0.12 | 0.15 |
| `<functional>` | 0.12 | 0.15 |
| `<iostream>` | 0.15 | 0.21 |
| `<ranges>` | 0.17 | 0.22 |
| `<memory>` | 0.19 | 0.22 |
| `<format>` | 0.33 | 0.37 |

`<format>` is 33x an empty TU, which sounds alarming and is a third of a
second. Carruth's protobuf story is about *generated* code multiplied across
100,000 translation units, not about including `<vector>`; the draft should
keep those separate.

**(d) RTTI's size cost is real and is paid without use.** A program with 41
polymorphic classes in a deep template hierarchy, containing no `typeid` and
no `dynamic_cast` at all, `g++-13 -O2`:

| section | `-frtti` | `-fno-rtti` |
|---|---|---|
| `.text` | 3662 | 3662 |
| `.rodata` | 1021 | 168 |
| `.data.rel.ro` | 2640 | 1640 |
| `.rela.dyn` | 7128 | 3144 |
| section total | 19987 | 13992 |

+43% on the sum of sections, with `.text` byte-identical. The growth is
mangled type-name strings, `type_info` objects, and — the largest single
item — dynamic relocations. One name string in this program is 178
characters. This confirms the draft's §8 claim ("you pay in size whether or
not you use it") and identifies where the bytes actually go, which the draft
currently doesn't.

**(e) `dynamic_cast` is ~3x a virtual call here, not "hundreds of cycles".**
4 Mi scattered heap objects, 4 concrete types, one with virtual inheritance;
`-O2`; ns per operation:

| operation | gcc 13.3 | clang 18 |
|---|---|---|
| virtual call `kind()` | 6.91 | 6.97 |
| tag switch on `kind()` | 7.07 | 6.86 |
| `dynamic_cast<D1*>` (single inheritance) | 22.83 | 23.26 |
| `dynamic_cast<Deep*>` (through virtual inheritance) | 19.58 | 20.54 |
| `dynamic_cast<M2*>` (cross-cast) | 23.10 | 22.72 |
| `typeid(*p) == typeid(D1)` | 4.00 | 4.09 |

Caveats: the loop is pointer-chasing so the absolute numbers include cache
misses, and everything is in one executable, so `__dynamic_cast` compares
`type_info` *addresses* rather than falling back to `strcmp`. The draft's §8
"hundreds of cycles" figure is defensible only for the cross-shared-library
case; within one binary I measured roughly 70–90 cycles, ~3x a virtual call.
Also notable and slightly awkward for the anti-RTTI position: `typeid`
comparison came out *faster* than a virtual call, and a tag switch was
indistinguishable from virtual dispatch.

### 4. The counter-case to data-oriented / anti-OOP arguments

### The best-sourced reply is Martin's, in Muratori's own repository

The `cmuratori/misc` repo contains the full `cleancodeqa.md` and
`cleancodeqa-2.md` exchange with Robert C. Martin. It is the ideal citation
for the draft because both sides are verbatim and neither can be accused of
being strawmanned. Martin's opening concession is total on the technical
point:

> So…. Yes, absolutely, the structures you were presenting are not the best
> way to squeeze every nanosecond of performance out of a system. Indeed,
> using those structures can cost you a lot of nanoseconds.

His counter is a domain claim, not a technical one:

> But the kinds of environments where that kind of parsimony is important
> are nowadays few and far between. The vast majority of software systems
> require less than 1% of a modern processor's power. […] It is economically
> better for most organizations to conserve programmer cycles than computer
> cycles. So if there is a disconnect between us, I think it is only in the
> kinds of contexts that we prioritize.

**On the shapes/area benchmark being unrepresentative** — this is the
precise argument the draft asked for, and Martin makes it explicitly:

> From the point of view of counting nanoseconds, OO is less efficient. You
> made this point in your video. However, the cost is relatively small if
> the functionality being deployed is relatively large. The _shape_ example,
> used in your video, is one of those cases where the deployed functionality
> is small. On the other hand, if you are deploying a particular algorith
> for calculating the pay of an employee, the cost of the polymorphic
> dispatch pales in comparison to the cost of the deployed algorithm.

And separately, on the specific `KxLxW` optimisation:

> Clearly (at least I think it should be clear) one would not prefer the
> KxLxW solution in a resource rich environment unless one was very sure
> that the business would not extend the problem to general shapes.

That is a maintainability-cost argument stated as a hypothesis about future
requirements — falsifiable in principle, unfalsifiable in practice, and the
draft should say so.

### The distinction both parties converge on is the expression problem

Martin concedes the closed-set case in as many words:

> Are there cases where using OO does not help conform to the OCP?
> Certainly. Again, if you know all the types, and you expect variation to
> be new basic functionality operating over all those types, then dynamic
> polymorphism (OO) works _against_ the OCP and switch statements work for
> it.

Muratori's reply generalises it into the n×m argument:

> Specifically, suppose you have n types each supporting m operations. Any
> system design supporting this will therefore have O(nm) "things" in it,
> and the design question is how do you want to group them. […] So to me,
> there is no "win" here in the abstract. You are merely choosing _which_
> programmer behavior you will make hard, and which you will make easy.

Neither of them names it, but this is the **expression problem**, stated by
Philip Wadler in 1998:

> The goal is to define a datatype by cases, where one can add new cases to
> the datatype and new functions over the datatype, without recompiling
> existing code, and while retaining static type safety (e.g., no casts).

Naming it is the single most useful thing the draft can do in §8. It
converts "inheritance vs tagged union" from a taste war into a known,
formally studied trade-off with a known answer: neither grouping dominates;
you pick based on which axis is open. For an emulator the answer is
unambiguous — the opcode set of a fixed 1994 CPU is the most closed set
imaginable, and the operations over it (interpret, JIT, disassemble, trace)
are the open axis. That is *why* the tag switch is right there, and it is a
much stronger justification than "OOP is slow".

Where the dialogue leaves genuine disagreement: Martin's summary is "When
operations proliferate more rapidly than types we both use switches. When
types proliferate more rapidly than operations we both use dynamic
dispatch." Muratori rejects even that, using OS device drivers as the
counterexample — "enums are _more_ important in a system where types
proliferate rapidly, _not_ less" — because adding one operation across
thousands of vendor driver types costs more than adding one type across a
handful of operations. This is a claim about real-world n and m, and it is
empirical in principle.

Also worth quoting for the draft's §5, because it is the cleanest statement
of a pure values position anywhere in my sources:

> In my work I don't care about nanoseconds. I almost never care about
> microseconds. I sometimes care about milliseconds. Therefore I make the
> software engineering tradeoff towards _programmer convenience_, and long
> term readability and maintainability. This means that I don't want to
> think about the hardware. […] I am willing to spend billions of computer
> cycles to attain that abstraction and separation. My concern is
> _programmer cycles_ not machine cycles. — Martin

### Stroustrup rejected OO-as-doctrine before the critics did

The historical narrative in the anti-OOP talks tends to treat C++ as the
vehicle that spread inheritance dogma. P0976R0 is Stroustrup's own account,
and it says the opposite:

> A class is just a class until you start adding virtual functions and
> derived classes. There was no attempt to force everybody to fit every
> class into a hierarchy or to make every function a virtual member
> function. This may seem obvious today (as it did to me then), but the
> clamor for OO purity was dominant. The zero-overhead principle saved me
> (see D&E).

> A class is a generalization of a struct offering the opportunity for
> member functions and encapsulation. There were no attempts to ban structs
> or to make every function a member function. There was no attempt to force
> all access to data to go through getters and setters.

If the draft wants a one-line version: the "everything must be an object"
doctrine was a 1990s methodology fashion that C++ resisted, not one it
imposed. The `struct`/`class`/free-function design was a deliberate refusal.

### The historical narrative, checked against the Simula primary source

I checked Muratori's claim that inheritance arose from concrete
implementation and code-reuse pressures rather than principled design,
against Nygaard and Dahl's own HOPL-I paper, *The Development of the SIMULA
Languages* (1978). It substantially **supports** him. Their own list of
motivations, §"the background for our language discussions during the autumn
of 1966", says the two that mattered were attribute accessing and "common
properties of processes", and describes the latter as:

> When writing simulation programs we had observed that processes often
> shared a number of common properties, both in data attributes and actions,
> but were structurally different in other respects so that they had to be
> described by separate declarations. Such partial similarity fairly often
> applied to processes in different simulation models, indicating that
> programming effort could be saved by somehow preprogramming the common
> properties.

That is code reuse, verbatim, as the motivation. Their sixth motivation is
frankly an implementation concern: the UNIVAC ALGOL compiler "was terribly
wasteful of storage space whenever the number of process activation records
was large". And the prefix idea arrived as a fix after months of failure:
"Much time was spent during the autumn of 1966 in trying to adapt Hoare's
record class construct to meet our requirements, without success. The
solution came suddenly, with the idea of 'prefixing', in December 1966."

So the honest counter to the historical narrative is not that it is wrong.
It is narrower: the *open-set* requirement was explicit in the design from
the start, not a later rationalisation. Requirement 2 in their list reads:

> We also needed to group together common process properties in such a way
> that they could be applied later, in a variety of different situations not
> necessarily known in advance.

"Not necessarily known in advance" is the open set. Simula's authors wanted
subclassing for exactly the case where a tagged union does not work, and
they said so in 1978. A draft section that presents the tagged union as
strictly superior has to answer that sentence.

### Where this counter-case is weak

Stated plainly, because the draft should not oversell it:

- Martin's "vast majority of software systems require less than 1% of a
  modern processor's power" is asserted, not measured, and Muratori
  immediately challenges it with Visual Studio and Clang/LLVM as
  counterexamples. I found no data behind it.
- Martin's dependency-inversion / recompilation argument is about a build
  model (many small DLLs, expensive full rebuilds) that many of the domains
  under discussion — emulators, game engines — simply do not have.
- I looked for a *measured* rebuttal of Acton's or Muratori's benchmarks and
  did not find one from a named source. There are blog replies (e.g. a Rust
  reimplementation noting that failing to randomise the shape array changes
  the result) but nothing I would cite as a serious empirical counter. The
  performance claims of the data-oriented camp appear to be substantially
  unrebutted on their own terms; the entire live disagreement is about
  scope, not about the numbers.

### 5. Empirical vs domain vs values

### (a) Settled or settleable by measurement

These have answers. Anyone still arguing them is arguing against a
measurement.

| Claim | Status |
|---|---|
| Virtual dispatch costs more than a tag switch in a hot loop | Yes, but small. On an *unpredictable* opcode stream I measured virtual 7.9 ns/op vs switch 6.8 ns/op (gcc) and 8.1 vs 6.3 (clang) — ~15–20%. Both are dominated by indirect-branch misprediction. |
| Grouping/batching by type beats dispatch-mechanism choice | Decisively. Sorting the same opcode stream so like ops are adjacent: switch 6.8 → 1.5 ns/op (gcc, 4.4x) and 6.3 → 0.46 ns/op (clang, 14x). Sorted virtual: 1.6 ns/op (gcc), 1.5 (clang). Best-to-worst spread is 17x (clang sorted switch vs random virtual) and almost all of it is predictability plus the optimiser's ability to vectorise the monomorphic loop — *not* the vtable indirection. This is the strongest empirical support for the data-oriented position, and it does not require abandoning virtual functions to obtain. |
| `dynamic_cast` is slower than a virtual call | Yes, ~3x within one binary (~70–90 cycles). Not "hundreds of cycles" unless casting across shared library boundaries. |
| RTTI costs binary size even when unused | Yes: +43% on section totals for a 41-class hierarchy with no `typeid`/`dynamic_cast`, `.text` unchanged. Mostly relocations and mangled name strings. |
| STL containers/iterators/algorithms are free at `-O2` | Yes, within noise, on both compilers. |
| STL abstractions are free at `-O0` | No. 2–6x penalty. Matters if and only if you debug unoptimised. |
| `std::function` is free | No. 7–8x a direct loop at `-O2`. |
| `unique_ptr` by value is as cheap as a raw pointer | No, and `-fno-exceptions` does not fix it. ABI, not EH. |
| Enabling exceptions costs binary size in code that never throws | Yes. Sutter's reported range is +15% to +38%; the draft's own §6 measurement (10.9% at `-O2`) is in the same family. |
| Throwing serialises across threads on a global unwinder lock | **No longer true.** Reproduced Neumann's P2544 setup on gcc 13.3 / glibc 2.39: throughput scales with core count. libgcc uses `_dl_find_object@GLIBC_2.35`. A pre-2022 measurement, still widely repeated. |
| Error codes get dropped in practice in disciplined C codebases | Yes. 13% of 9,022 error-propagating calls in Linux 2.6 filesystems and storage drivers (EIO, FAST '08), with evidence that many omissions are deliberate. |
| A compiler could make switch and virtual dispatch generate identical code | Not on gcc 13.3 or clang 18. Martin proposes it as a hypothetical; Muratori's reply ("None of those do what you're describing") is correct today. On the sorted stream clang got the switch to 0.46 ns/op and the virtual version to 1.5 ns/op — a 3x gap that devirtualisation did not close. |

### (b) Not empirical — a question of which costs matter in a given domain

These cannot be settled by a benchmark because the disagreement is over the
weighting function, not the numbers. Both sides usually agree on the
numbers.

- **Emulator hot interpreter loop.** 6 ns/op vs 1.5 ns/op is 4x of your
  entire frame budget. Debug builds are where you live, so the `-O0`
  abstraction penalty is a first-order cost, not a footnote. A PS1 opcode
  set is a closed set that will never gain a member, so the expression
  problem resolves in favour of the tag switch on the merits, before any
  performance argument. Unbounded throw latency is unacceptable in an audio
  callback. Every one of these is a real constraint, and none of them
  generalises.
- **Business application / internal service.** Martin's "less than 1% of a
  modern processor" may be unsourced but it is often *true*, and when it is,
  169 ms vs 20 ms on a `std::function` loop is invisible next to one network
  round trip. Error-handling correctness across a large team dominates. The
  type set is open — new payment providers, new device drivers, new report
  formats arrive forever — so the expression problem resolves the other way.
- **The `unique_ptr` cost is the cleanest illustration.** The measurement is
  identical for both domains: 18 instructions and 5 memory ops instead of 7
  and 0. Whether that is "a significant cost" (Carruth's words, from a
  codebase where this shape appears in hundreds of millions of lines) or
  "irrelevant" depends only on how many times per second it executes. No
  further measurement helps.
- **Whether the shapes benchmark is representative.** Martin's objection is
  structurally correct — the ratio of dispatch cost to work-per-call is what
  determines the answer, and the shapes case picks the ratio that maximises
  the effect. Muratori's counter is that this ratio is the common case in
  the code he cares about. Both are right about their own domains. A
  benchmark cannot arbitrate "representative".
- **Binary size.** +43% for RTTI is decisive on a 64 KB microcontroller and
  meaningless for a desktop emulator. Same number, opposite conclusion.

### (c) Not measurable — taste, team scale, unfalsifiable forecasts

- **"A smaller subset is easier for a team to master."** Plausible, widely
  believed, and I found no study. It is also in tension with a measurable
  fact: the substitute has to be built and maintained by that same team, and
  the Core Guidelines' counter ("Build your ideal small foundation library
  and use that, rather than lowering your level of programming to glorified
  assembly code") is equally unmeasured.
- **Readability.** Carruth's over-factoring story is the honest treatment:
  the same code was unreadable both before and after refactoring, and he
  offers no metric, only "you have to get in between these two things".
  Every party to this debate makes readability claims; none has evidence.
- **"You won't need to extend it to general shapes."** Martin's condition
  for preferring the fast solution is a forecast about future requirements.
  Nobody can measure a forecast. This is where most real arguments about
  abstraction actually live.
- **Whether hidden control flow is acceptable.** The draft's §5 has this
  right: the fact that any call may exit early is not a cost you can put a
  number on. Sutter concedes it as the one place exceptions fail his own
  ideal table ("exception propagation between the throw site and the catch
  handler is invisible in source code"). Whether the RAII answer suffices is
  a judgement about how a team reads code.
- **Whether "not standard C++" is itself a cost.** Sutter's whole framing
  rests on it: "Large numbers of 'C++' projects are not actually using
  standard C++." For a one-person emulator with no library consumers, this
  cost is approximately zero. For a library shipped to strangers it is
  large. It is a real cost and it is not a measurable one.
- **The "design smell" argument.** Google: "Querying the type of an object
  at run-time frequently means a design problem." That is an aesthetic claim
  dressed as an engineering one, and it collapses under the closed-set case,
  where branching on concrete type is simply correct.

### 6. Claims I found to be folklore, with no primary source

1. **"Stroustrup coined 'zero-cost abstraction'."** He wrote
   *zero-overhead*, in every document I checked (ETAPS 2012, HOPL-II, P0976,
   P0977) and so do the Core Guidelines. Sutter has to explicitly disclaim
   the "zero cost" reading in P0709. Multiple secondary sources assert the
   attribution; none cites a Stroustrup text, and I found none.
2. **"Most real-world C security bugs are unchecked returns."** The draft's
   §5 asserts this. CWE-252 (Unchecked Return Value) and CWE-391 (Unchecked
   Error Condition) do **not** appear anywhere in the 2024 CWE Top 25. The
   memory- safety entries that do are out-of-bounds write (#2),
   out-of-bounds read (#6) and use-after-free (#8). What is sourceable is
   the narrower and still useful claim that dropped error codes are
   pervasive in disciplined C (EIO: 13% of propagating calls in Linux 2.6
   storage code) — pervasive, but not the leading CVE class. Recommend
   rewording.
3. **"Exceptions can't cross a C ABI boundary."** True as a practical rule
   but I found no primary specification statement; the Itanium ABI does not
   forbid it and in practice `-fexceptions` on C code makes it work on
   GCC/Clang. Fine as a rule of thumb; not a standards fact.
4. **"Throwing takes a global lock, so exceptions don't scale."** Was true
   and measured (Neumann, P2544R0, 2022). No longer reproduces on gcc ≥ 12 /
   glibc ≥ 2.35 (measured above). This is now stale folklore that is still
   being repeated.
5. **"Google banned exceptions because exceptions are bad."** The style
   guide says the opposite in as many words. The ban is documented as a
   compatibility decision about a pre-existing codebase, with the explicit
   admission "Things would probably be different if we had to do it all over
   again from scratch." Any draft sentence that cites Google as evidence
   *against* exceptions is citing a source that disagrees with it.
6. **"`dynamic_cast` costs hundreds of cycles."** Measured ~70–90 cycles
   here, ~3x a virtual call, within a single executable. The "hundreds"
   figure and the string-comparison mechanism apply to the
   cross-shared-library case; the Itanium ABI's `strcmp` fallback is real
   but is not the common path in a statically linked binary. The draft's §8
   should scope this.
7. **"The vast majority of software systems require less than 1% of a modern
   processor's power."** Martin's, asserted without data, and immediately
   contested. Widely repeated on the pro-abstraction side. Symmetrically
   unsourced with the folklore on the other side.

### 7. What I could not verify

- **Whether P0709 is formally dead.** R4 (2019) is the last revision I
  found; P3166R0 (Baker, 2024) supersedes the goal with a different design.
  I found no EWG poll record either way, and no statement from Sutter
  retiring it. The draft should say "stalled since 2019", not "rejected".
- **Whether CastGuard shipped.** Sutter's 2019 slides call the +1.5%-binary-
  size result "Preliminary". I did not find a follow-up measurement or a
  statement that it is enabled in production MSVC or Clang.
- **Whether Google or LLVM have formally revisited.** I found no RFC, issue,
  or design-doc revisiting either ban. Absence of evidence, not evidence of
  absence — I searched, I did not exhaust.
- **Carruth's exact wording.** The CppCon2019 repository has no slide deck
  for this talk. Everything I attribute to him beyond the published abstract
  comes from YouTube auto-captions that I cleaned up. The substance is
  unambiguous; do not put the transcript's wording in quotation marks in the
  published post without checking the video at the relevant timestamps.
- **A measured rebuttal to Acton/Muratori.** Does not appear to exist from a
  named source. If the draft claims the data-oriented benchmarks are wrong,
  it will be making a new claim, not reporting one.
- **Chandler Carruth's earlier pro-zero-cost talks.** He says he advocated
  the position at previous CppCons; I did not locate which talk, so I cannot
  quote the position he is retracting.

### 8. Reading list — URLs I actually fetched

- https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0709r0.pdf — Sutter, "Zero-overhead deterministic exceptions: Throwing values" (P0709R0)
- https://www.stroustrup.com/P0977-remember-the-vasa.pdf — Stroustrup, "Remember the Vasa!" (P0977r0)
- https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0976r0.pdf — Stroustrup, "The Evils of Paradigms" (P0976r0)
- https://raw.githubusercontent.com/isocpp/CppCoreGuidelines/master/CppCoreGuidelines.md — C++ Core Guidelines source (In.0, In.not, NR.3, E.27, Per.6, CPL.*)
- https://google.github.io/styleguide/cppguide.html#Exceptions — Google C++ Style Guide, Exceptions and RTTI sections
- https://llvm.org/docs/CodingStandards.html — LLVM Coding Standards, "Do not use RTTI or Exceptions"
- https://groups.google.com/g/llvm-dev/c/ae_2CVL2R9A — llvm-dev, "LLVM use of C++ exceptions and RTTI"
- https://www.stroustrup.com/hopl2.pdf — Stroustrup, "A History of C++: 1979−1991"
- https://www.stroustrup.com/ETAPS-corrected-draft.pdf — Stroustrup, "Foundations of C++" (ETAPS 2012)
- https://www.stroustrup.com/quotes.html — Stroustrup's own gloss on the "smaller and cleaner language" quote
- https://cppcon2019.sched.com/event/Sfq4/there-are-no-zero-cost-abstractions — Carruth's own abstract
- https://www.youtube.com/watch?v=rHIkrotSwcc — Carruth, "There Are No Zero-cost Abstractions" (auto-captions)
- https://raw.githubusercontent.com/CppCon/CppCon2019/master/Presentations/defragmenting_cpp_making_exceptions_and_rtti_more_affordable_and_usable/defragmenting_cpp_making_exceptions_and_rtti_more_affordable_and_usable__herb_sutter__cppcon_2019.pdf — Sutter, CppCon 2019 slides (survey data, CastGuard)
- https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2022/p2544r0.html — Neumann, "C++ exceptions are becoming more and more problematic"
- https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3166r0.html — Baker, "Static Exception Specifications"
- https://research.cs.wisc.edu/wind/Publications/eio-fast08.pdf — Gunawi et al., "EIO: Error Handling is Occasionally Correct" (FAST '08)
- https://www.eecg.toronto.edu/~yuan/papers/failure_analysis_osdi14.pdf — Yuan et al., "Simple Testing Can Prevent Most Critical Failures" (OSDI '14)
- https://raw.githubusercontent.com/cmuratori/misc/main/cleancodeqa.md — Muratori / Robert C. Martin dialogue, part 1
- https://raw.githubusercontent.com/cmuratori/misc/main/cleancodeqa-2.md — Muratori / Robert C. Martin dialogue, part 2
- https://homepages.inf.ed.ac.uk/wadler/papers/expression/expression.txt — Wadler, "The Expression Problem" (1998)
- https://hannemyr.com/cache/knojd_acm78.pdf — Nygaard & Dahl, "The Development of the SIMULA Languages" (HOPL-I, 1978)
- https://cwe.mitre.org/top25/archive/2024/2024_top25_list.html — 2024 CWE Top 25 (checked for CWE-252 / CWE-391)
- https://api.github.com/repos/CppCon/CppCon2019/contents/Presentations — checked for Carruth slides (absent)

### Benchmark provenance

All measurements above: Intel i5-12600K (10 physical / 16 logical cores),
Ubuntu 24.04, glibc 2.39, `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` and
`Ubuntu clang version 18.1.3`. Sources in `scratchpad/exp/`: `uptr.cpp`,
`dispatch.cpp`, `dispatch2.cpp`, `absp.cpp`, `rtti.cpp`, `dyncast.cpp`,
`throwscale.cpp`. Three repetitions each, medians reported; single-run
numbers are marked as such where relevant. These are microbenchmarks on one
machine and should be presented as such.

