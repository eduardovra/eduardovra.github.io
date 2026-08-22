#!/usr/bin/env python3
"""Generate the animated pipeline SVG includes for the PS1 CPU post.

Writes _includes/diagrams/r3000a-pipeline.svg (the five-stage assembly
line) and _includes/diagrams/load-delay-hazard.svg (the load delay).
Both share one visual language and one clock of CYCLE_SECONDS per CPU
cycle. Colours come from the site's --syn-* syntax palette so every
instruction keeps its own tint in light and dark themes.

Each figure animates with CSS only, collapses to a complete static
image under prefers-reduced-motion and in print, and carries a
checkbox-driven pause control.
"""

import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "_includes/diagrams"

CYCLE_SECONDS = 1.15
MOVE = 2.5  # percent of the loop spent sliding between two cells

STAGES = ["IF", "RD", "ALU", "MEM", "WB"]

# Grid geometry, shared by both diagrams so they read as one figure.
GX0 = 172
GPITCH = 38
GW = 34
GH = 24
LABEL_END = 148
MNEMONIC_X = 17
OPERAND_X = 58


def pct(value: float) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return (text or "0") + "%"


def keyframes(name: str, stops: list[tuple[str, str]]) -> str:
    body = "\n".join(f"    {sel} {{ {decls} }}" for sel, decls in stops)
    return f"  @keyframes {name} {{\n{body}\n  }}"


def appear_keyframes(prefix: str, slot: float, count: int) -> list[str]:
    """One block per reveal time: hidden, then visible until loop end."""
    blocks = [keyframes(f"{prefix}-0", [("0%, 100%", "opacity: 1")])]
    for n in range(1, count):
        start = n * slot
        blocks.append(
            keyframes(
                f"{prefix}-{n}",
                [
                    (f"0%, {pct(start)}", "opacity: 0"),
                    (f"{pct(start + MOVE)}, 100%", "opacity: 1"),
                ],
            )
        )
    return blocks


def now_keyframes(name: str, slot: float) -> str:
    """Tint the cycle number that the clock is currently on."""
    return keyframes(
        name,
        [
            (f"0%, {pct(slot)}", "fill: var(--accent)"),
            (f"{pct(slot + MOVE)}, 100%", "fill: var(--faint)"),
        ],
    )


def cursor_keyframes(name: str, slot: float, cycles: int) -> str:
    """Step the highlight band one grid column per cycle."""
    stops = [("0%", "opacity: 0; transform: translateX(0)")]
    stops.append((pct(MOVE), "opacity: .1"))
    stops.append((pct(slot), "transform: translateX(0)"))
    for c in range(2, cycles + 1):
        arrive = (c - 1) * slot + MOVE
        x = (c - 1) * GPITCH
        stops.append((pct(arrive), f"transform: translateX({x}px)"))
        stops.append((pct(c * slot), f"transform: translateX({x}px)"))
    rest = (cycles - 1) * GPITCH
    stops.append((pct(cycles * slot), "opacity: .1"))
    stops.append((pct(cycles * slot + MOVE), "opacity: 0"))
    stops.append(("100%", f"opacity: 0; transform: translateX({rest}px)"))
    return keyframes(name, stops)


def cycle_numbers(cls: str, count: int, y: int) -> list[str]:
    out = []
    for c in range(1, count + 1):
        cx = GX0 + GW / 2 + GPITCH * (c - 1)
        out.append(
            f'  <text class="{cls} {cls}-{c}" x="{cx:g}" y="{y}" '
            f'text-anchor="middle" font-size="11.5">{c}</text>'
        )
    return out


def row_label(
    y: int,
    tint: str,
    mnemonic: str,
    operands: str,
) -> list[str]:
    baseline = y + 16.5
    return [
        f'  <rect x="8" y="{y + 5}" width="3" height="14" rx="1.5" '
        f'fill="{tint}"/>',
        f'  <text x="{MNEMONIC_X}" y="{baseline:g}" font-size="11.5" '
        f'fill="var(--ink)">{mnemonic}</text>',
        f'  <text x="{OPERAND_X}" y="{baseline:g}" font-size="11.5" '
        f'fill="var(--muted)">{operands}</text>',
    ]


def cell(
    cycle: int,
    y: int,
    label: str,
    tint: str,
    strong: bool,
    extra_class: str,
) -> list[str]:
    x = GX0 + GPITCH * (cycle - 1)
    cx = x + GW / 2
    baseline = y + 16.5
    if strong:
        rect = (
            f'fill="{tint}" fill-opacity=".3" stroke="{tint}" '
            'stroke-width="1.4"'
        )
        text = 'fill="var(--ink)" font-weight="600"'
    else:
        rect = (
            f'fill="{tint}" fill-opacity=".1" stroke="{tint}" '
            'stroke-opacity=".32"'
        )
        text = 'fill="var(--muted)"'
    return [
        f'  <g class="cell {extra_class}">',
        f'    <rect x="{x}" y="{y}" width="{GW}" height="{GH}" rx="3" '
        f'{rect}/>',
        f'    <text x="{cx:g}" y="{baseline:g}" text-anchor="middle" '
        f'font-size="10.5" {text}>{label}</text>',
        "  </g>",
    ]


SHELL_CSS = """  .dgm { max-width: 680px; margin: 1.9rem auto; }
  .dgm-scroll { overflow-x: auto; }
  .dgm-scroll svg { width: 100%; min-width: 520px; height: auto;
    display: block; font-family: var(--mono); }
  .dgm-toggle { position: absolute; width: 1px; height: 1px;
    opacity: 0; pointer-events: none; }
  .dgm-btn { display: block; width: max-content; margin: .5rem 0 0 auto;
    padding: .35em .75em; cursor: pointer; border: 1px solid var(--line);
    border-radius: 4px; font: 500 11px/1 var(--text);
    letter-spacing: .06em; text-transform: uppercase; color: var(--faint); }
  .dgm-btn:hover { color: var(--accent); border-color: var(--accent); }
  .dgm-toggle:focus-visible ~ .dgm-btn { outline: 2px solid var(--accent);
    outline-offset: 2px; }
  .dgm-btn .dgm-resume { display: none; }
  .dgm-toggle:checked ~ .dgm-btn .dgm-resume { display: inline; }
  .dgm-toggle:checked ~ .dgm-btn .dgm-hold { display: none; }
  .dgm-toggle:checked ~ .dgm-scroll svg * {
    animation-play-state: paused !important; }"""


def wrap(wrap_id: str, svg_id: str, svg: str) -> str:
    """Put the figure in its scroller, with the pause checkbox."""
    toggle_id = f"{svg_id}-pause"
    return "\n".join(
        [
            f'<div class="dgm" id="{wrap_id}">',
            f'  <input type="checkbox" class="dgm-toggle" id="{toggle_id}">',
            '  <div class="dgm-scroll">',
            svg,
            "  </div>",
            f'  <label class="dgm-btn" for="{toggle_id}">'
            '<span class="dgm-hold">Pause</span>'
            '<span class="dgm-resume">Play</span></label>',
            "</div>",
            "",
        ]
    )


# --------------------------------------------------------------------------
# Diagram 1: the assembly line
# --------------------------------------------------------------------------

PIPE_INSTRS = [
    ("lw", "$t0, 0($a0)", "var(--syn-builtin)"),
    ("addiu", "$a0, $a0, 4", "var(--syn-str)"),
    ("addu", "$t1, $t1, $t2", "var(--syn-fn)"),
    ("sll", "$t3, $t3, 2", "var(--syn-num)"),
    ("or", "$t4, $t5, $t6", "var(--syn-cls)"),
]

P_CYCLES = 9
P_SLOTS = 12  # nine cycles plus a three-slot pause before looping
P_SLOT = 100 / P_SLOTS
P_DUR = P_SLOTS * CYCLE_SECONDS

MX0, MPITCH, MW, MY, MH = 45, 96, 86, 34, 52
TOK_W, TOK_H = 74, 22
TOK_Y = MY + 26
ROW_Y = [182 + 30 * i for i in range(5)]
GRID_TOP = 164
GRID_BOTTOM = ROW_Y[-1] + GH
TOK_EXIT = 4 * MPITCH + 40


def pipe_token_keyframes() -> str:
    """Slide one instruction chip through the five stage boxes."""
    stops = [("0%", f"opacity: 0; transform: translateX(-{MPITCH}px)")]
    stops.append((pct(MOVE), "opacity: 1; transform: translateX(0)"))
    stops.append((pct(P_SLOT), "transform: translateX(0)"))
    for s in range(2, 6):
        arrive = (s - 1) * P_SLOT + MOVE
        x = (s - 1) * MPITCH
        stops.append((pct(arrive), f"transform: translateX({x}px)"))
        stops.append((pct(s * P_SLOT), f"transform: translateX({x}px)"))
    exit_at = 5 * P_SLOT
    last_stage = 4 * MPITCH
    stops.append(
        (pct(exit_at), f"opacity: 1; transform: translateX({last_stage}px)")
    )
    stops.append(
        (
            pct(exit_at + MOVE),
            f"opacity: 0; transform: translateX({TOK_EXIT}px)",
        )
    )
    stops.append(
        ("100%", f"opacity: 0; transform: translateX({TOK_EXIT}px)")
    )
    return keyframes("pipe-tok", stops)


def pipe_css() -> str:
    lines = [SHELL_CSS]
    a = lines.append
    a("  #pipe-anim .tok { opacity: 0;")
    a(f"    animation: pipe-tok {P_DUR:g}s linear infinite; }}")
    for k in range(1, 6):
        delay = (k - 1) * CYCLE_SECONDS
        a(f"  #pipe-anim .tok-{k} {{ animation-delay: {delay:g}s; }}")
    a("  #pipe-anim .cyc { fill: var(--faint);")
    a(f"    animation: pipe-now {P_DUR:g}s linear infinite; }}")
    for c in range(1, P_CYCLES + 1):
        delay = (c - 1) * CYCLE_SECONDS
        a(f"  #pipe-anim .cyc-{c} {{ animation-delay: {delay:g}s; }}")
    a("  #pipe-anim .cell { opacity: 0; }")
    for n in range(P_CYCLES):
        a(
            f"  #pipe-anim .in-{n} {{ animation: pipe-in-{n} "
            f"{P_DUR:g}s linear infinite; }}"
        )
    a("  #pipe-anim .chip { opacity: .14; }")
    for k in range(1, 6):
        a(
            f"  #pipe-anim .chip-{k} {{ animation: pipe-done-{k} "
            f"{P_DUR:g}s linear infinite; }}"
        )
    a(
        "  #pipe-anim .cursor { opacity: 0; animation: pipe-cursor "
        f"{P_DUR:g}s linear infinite; }}"
    )
    a(pipe_token_keyframes())
    a(now_keyframes("pipe-now", P_SLOT))
    lines.extend(
        appear_keyframes(
            prefix="pipe-in",
            slot=P_SLOT,
            count=P_CYCLES,
        )
    )
    for k in range(1, 6):
        lit = (k - 1) * P_SLOT + 5 * P_SLOT
        a(
            keyframes(
                f"pipe-done-{k}",
                [
                    (f"0%, {pct(lit)}", "opacity: .14"),
                    (f"{pct(lit + MOVE)}, 100%", "opacity: 1"),
                ],
            )
        )
    a(
        cursor_keyframes(
            name="pipe-cursor",
            slot=P_SLOT,
            cycles=P_CYCLES,
        )
    )
    # The static fallback freezes on cycle 5, where all five stages are
    # busy. The tally means nothing without a running clock, so it goes.
    still = [
        "  @media (prefers-reduced-motion: reduce), print {",
        "    #pipe-anim * { animation: none !important; }",
        "    #pipe-anim .tok { opacity: 1; }",
    ]
    for k in range(1, 6):
        x = (5 - k) * MPITCH
        still.append(
            f"    #pipe-anim .tok-{k} {{ transform: translateX({x}px); }}"
        )
    still += [
        "    #pipe-anim .cell { opacity: 1; }",
        "    #pipe-anim .cursor, #pipe-anim .tally { opacity: 0; }",
        "    #pipe-anim .cyc { fill: var(--faint); }",
        "    #dgm-pipe .dgm-btn { display: none; }",
        "  }",
    ]
    lines.extend(still)
    return "\n".join(lines)


def build_pipe() -> str:
    height = GRID_BOTTOM + 32
    out = [
        f'  <svg id="pipe-anim" viewBox="0 0 560 {height}" role="img" '
        'aria-labelledby="pipe-anim-title">',
        '  <title id="pipe-anim-title">An animated R3000A pipeline. One '
        "instruction enters the five stages every cycle, so from cycle five "
        "onward five instructions are in flight at once and one finishes "
        "per cycle. A timeline below records the same nine "
        "cycles.</title>",
        "  <style>",
        pipe_css(),
        "  </style>",
        '  <text x="8" y="16" fill="var(--faint)" font-size="11.5" '
        'font-family="var(--text)">One instruction enters every cycle. '
        'By cycle 5, all five stages are busy at once.</text>',
    ]

    # The machine: five fixed stages.
    for i, name in enumerate(STAGES):
        x = MX0 + MPITCH * i
        out.append(
            f'  <rect x="{x}" y="{MY}" width="{MW}" height="{MH}" rx="5" '
            'fill="var(--code-bg)" fill-opacity=".55" '
            'stroke="var(--line)"/>'
        )
        out.append(
            f'  <text x="{x + MW / 2:g}" y="{MY + 15}" '
            'text-anchor="middle" font-size="10" letter-spacing=".1em" '
            f'fill="var(--faint)">{name}</text>'
        )
    out.append(
        f'  <text x="34" y="{TOK_Y + 15}" text-anchor="middle" '
        'font-size="13" fill="var(--faint)">&#8594;</text>'
    )

    # Instruction chips, one per instruction, sliding stage to stage.
    for k, (mnemonic, _, tint) in enumerate(PIPE_INSTRS, start=1):
        tx = MX0 + (MW - TOK_W) / 2
        out += [
            f'  <g class="tok tok-{k}">',
            f'    <rect x="{tx:g}" y="{TOK_Y}" width="{TOK_W}" '
            f'height="{TOK_H}" rx="4" fill="{tint}" fill-opacity=".18" '
            f'stroke="{tint}" stroke-opacity=".55"/>',
            f'    <text x="{tx + TOK_W / 2:g}" y="{TOK_Y + 15}" '
            'text-anchor="middle" font-size="11.5" fill="var(--ink)" '
            f'font-weight="500">{mnemonic}</text>',
            "  </g>",
        ]

    # Tally of instructions that have left the pipeline.
    out.append('  <g class="tally">')
    out.append(
        '    <text x="417" y="112" text-anchor="end" fill="var(--faint)" '
        'font-size="11.5" font-family="var(--text)">completed</text>'
    )
    for k, (_, _, tint) in enumerate(PIPE_INSTRS, start=1):
        x = 425 + 19 * (k - 1)
        out.append(
            f'    <rect class="chip chip-{k}" x="{x}" y="101" width="14" '
            f'height="14" rx="3" fill="{tint}"/>'
        )
    out.append("  </g>")

    # The timeline.
    out.append(
        '  <text x="8" y="148" fill="var(--faint)" font-size="11.5" '
        'font-family="var(--text)">The same nine cycles, as a '
        'timeline.</text>'
    )
    out.append(
        f'  <rect class="cursor" x="{GX0}" y="{GRID_TOP}" width="{GW}" '
        f'height="{GRID_BOTTOM - GRID_TOP}" rx="3" fill="var(--accent)"/>'
    )
    out.append(
        f'  <text x="{LABEL_END}" y="176" text-anchor="end" '
        'fill="var(--faint)" font-size="11.5" '
        'font-family="var(--text)">cycle</text>'
    )
    out += cycle_numbers(cls="cyc", count=P_CYCLES, y=176)
    for k, (mnemonic, operands, tint) in enumerate(PIPE_INSTRS, start=1):
        y = ROW_Y[k - 1]
        out += row_label(
            y=y,
            tint=tint,
            mnemonic=mnemonic,
            operands=operands,
        )
        for s, stage in enumerate(STAGES, start=1):
            cycle = k + s - 1
            out += cell(
                cycle=cycle,
                y=y,
                label=stage,
                tint=tint,
                strong=(s == 1),
                extra_class=f"in-{cycle - 1}",
            )

    legend_y = GRID_BOTTOM + 10
    out += [
        f'  <rect x="8" y="{legend_y}" width="24" height="15" rx="3" '
        'fill="var(--syn-builtin)" fill-opacity=".3" '
        'stroke="var(--syn-builtin)" stroke-width="1.4"/>',
        f'  <text x="20" y="{legend_y + 11}" text-anchor="middle" '
        'font-size="9.5" fill="var(--ink)" font-weight="600">IF</text>',
        f'  <text x="40" y="{legend_y + 11}" fill="var(--muted)" '
        'font-size="11.5" font-family="var(--text)">The diagonal of IF '
        'cells is <tspan font-family="var(--mono)" '
        'fill="var(--ink)">pc</tspan>, fetching a new instruction every '
        'cycle.</text>',
        "  </svg>",
    ]
    return "\n".join(out)


# --------------------------------------------------------------------------
# Diagram 2: the load delay hazard
# --------------------------------------------------------------------------

L_CYCLES = 6
L_SLOTS = 9
L_SLOT = 100 / L_SLOTS
L_DUR = L_SLOTS * CYCLE_SECONDS

LW_TINT = "var(--syn-builtin)"
ADDU_TINT = "var(--syn-fn)"
L_ROW_Y = [48, 78]
L_STRIP_Y = 118
L_HELD = ["0", "0", "0", "42", "42", "42"]
L_READ_CYCLE = 3   # addu reads $t0 in RD here, and gets the stale 0
L_LAND_CYCLE = 4   # the loaded value only reaches $t0 here


def load_css() -> str:
    lines = [SHELL_CSS]
    a = lines.append
    a("  #load-anim .cyc { fill: var(--faint);")
    a(f"    animation: load-now {L_DUR:g}s linear infinite; }}")
    for c in range(1, L_CYCLES + 1):
        delay = (c - 1) * CYCLE_SECONDS
        a(f"  #load-anim .cyc-{c} {{ animation-delay: {delay:g}s; }}")
    a("  #load-anim .cell { opacity: 0; }")
    for n in range(L_CYCLES):
        a(
            f"  #load-anim .in-{n} {{ animation: load-in-{n} "
            f"{L_DUR:g}s linear infinite; }}"
        )
    a(
        "  #load-anim .cursor { opacity: 0; animation: load-cursor "
        f"{L_DUR:g}s linear infinite; }}"
    )
    a(now_keyframes("load-now", L_SLOT))
    lines.extend(
        appear_keyframes(
            prefix="load-in",
            slot=L_SLOT,
            count=L_CYCLES,
        )
    )
    a(
        cursor_keyframes(
            name="load-cursor",
            slot=L_SLOT,
            cycles=L_CYCLES,
        )
    )
    lines += [
        "  @media (prefers-reduced-motion: reduce), print {",
        "    #load-anim * { animation: none !important; }",
        "    #load-anim .cell { opacity: 1; }",
        "    #load-anim .cursor { opacity: 0; }",
        "    #load-anim .cyc { fill: var(--faint); }",
        "    #dgm-load .dgm-btn { display: none; }",
        "  }",
    ]
    return "\n".join(lines)


def stale_read_cell(cycle: int, y: int, stage: str) -> list[str]:
    """The RD cell that reads $t0 too early, flagged in the accent."""
    x = GX0 + GPITCH * (cycle - 1)
    return [
        f'  <g class="cell in-{cycle - 1}">',
        f'    <rect x="{x}" y="{y}" width="{GW}" height="{GH}" rx="3" '
        'fill="var(--accent)" fill-opacity=".22" stroke="var(--accent)" '
        'stroke-width="1.6"/>',
        f'    <text x="{x + GW / 2:g}" y="{y + 16.5:g}" '
        'text-anchor="middle" font-size="10.5" fill="var(--ink)" '
        f'font-weight="600">{stage}</text>',
        "  </g>",
    ]


def build_load() -> str:
    grid_bottom = L_STRIP_Y + GH
    out = [
        '  <svg id="load-anim" viewBox="0 0 560 234" role="img" '
        'aria-labelledby="load-anim-title">',
        '  <title id="load-anim-title">An animated load delay hazard. The '
        "load reaches memory in cycle four, but the instruction behind it "
        "reads its registers in cycle three, so it adds the stale value "
        "of $t0 and produces 1 instead of 43.</title>",
        "  <style>",
        load_css(),
        "  </style>",
        '  <text x="8" y="16" fill="var(--faint)" font-size="11.5" '
        'font-family="var(--text)">Memory at '
        '<tspan font-family="var(--mono)">0($a0)</tspan> holds 42, '
        '<tspan font-family="var(--mono)">$t2</tspan> is 1, and '
        '<tspan font-family="var(--mono)">$t0</tspan> starts at 0.</text>',
        f'  <rect class="cursor" x="{GX0}" y="30" width="{GW}" '
        f'height="{grid_bottom - 30}" rx="3" fill="var(--accent)"/>',
        f'  <text x="{LABEL_END}" y="42" text-anchor="end" '
        'fill="var(--faint)" font-size="11.5" '
        'font-family="var(--text)">cycle</text>',
    ]
    out += cycle_numbers(cls="cyc", count=L_CYCLES, y=42)

    rows = [
        ("lw", "$t0, 0($a0)", LW_TINT, 1, L_LAND_CYCLE),
        ("addu", "$t1, $t0, $t2", ADDU_TINT, 2, L_READ_CYCLE),
    ]
    for mnemonic, operands, tint, k, hot_cycle in rows:
        y = L_ROW_Y[k - 1]
        out += row_label(
            y=y,
            tint=tint,
            mnemonic=mnemonic,
            operands=operands,
        )
        for s, stage in enumerate(STAGES, start=1):
            cycle = k + s - 1
            hot = cycle == hot_cycle
            if hot and k == 2:
                out += stale_read_cell(cycle=cycle, y=y, stage=stage)
            else:
                out += cell(
                    cycle=cycle,
                    y=y,
                    label=stage,
                    tint=tint,
                    strong=hot,
                    extra_class=f"in-{cycle - 1}",
                )

    # What $t0 actually holds, aligned to the same columns.
    out.append(
        f'  <text x="{LABEL_END}" y="{L_STRIP_Y + 16.5:g}" '
        'text-anchor="end" fill="var(--muted)" font-size="11.5">'
        '$t0 holds</text>'
    )
    for c, value in enumerate(L_HELD, start=1):
        x = GX0 + GPITCH * (c - 1)
        if c == L_READ_CYCLE:
            rect = (
                'fill="var(--accent)" fill-opacity=".1" '
                'stroke="var(--accent)" stroke-width="1.6"'
            )
            fill = 'fill="var(--accent)" font-weight="600"'
        else:
            rect = 'fill="var(--code-bg)" stroke="var(--line)"'
            fill = 'fill="var(--muted)"'
        out += [
            f'  <g class="cell in-{c - 1}">',
            f'    <rect x="{x}" y="{L_STRIP_Y}" width="{GW}" '
            f'height="{GH}" rx="3" {rect}/>',
            f'    <text x="{x + GW / 2:g}" y="{L_STRIP_Y + 16.5:g}" '
            f'text-anchor="middle" font-size="11" {fill}>{value}</text>',
            "  </g>",
        ]

    notes = [
        (
            168,
            L_READ_CYCLE,
            "var(--accent)",
            '<tspan font-family="var(--mono)" '
            'fill="var(--ink)">addu</tspan> reads '
            '<tspan font-family="var(--mono)" '
            'fill="var(--ink)">$t0</tspan> in RD &#8212; the load is '
            'still in ALU, so it gets the old 0.',
        ),
        (
            190,
            L_LAND_CYCLE,
            LW_TINT,
            'The loaded 42 reaches <tspan font-family="var(--mono)" '
            'fill="var(--ink)">$t0</tspan> in MEM &#8212; one cycle '
            'after it was needed.',
        ),
    ]
    for y, num, tint, text in notes:
        out += [
            f'  <rect x="8" y="{y - 12}" width="16" height="16" rx="3" '
            f'fill="{tint}" fill-opacity=".22" stroke="{tint}" '
            'stroke-width="1.4"/>',
            f'  <text x="16" y="{y}" text-anchor="middle" '
            'font-size="10.5" fill="var(--ink)" '
            f'font-weight="600">{num}</text>',
            f'  <text x="34" y="{y}" fill="var(--muted)" '
            f'font-size="11.5" font-family="var(--text)">{text}</text>',
        ]

    out += [
        '  <text x="8" y="222" fill="var(--ink)" font-size="12.5" '
        'font-family="var(--text)">So '
        '<tspan font-family="var(--mono)">$t1</tspan> ends up 0 + 1 = 1, '
        'where it should have been 42 + 1 = 43.</text>',
        "  </svg>",
    ]
    return "\n".join(out)


def main() -> None:
    figures = [
        ("r3000a-pipeline.svg", "dgm-pipe", "pipe-anim", build_pipe()),
        ("load-delay-hazard.svg", "dgm-load", "load-anim", build_load()),
    ]
    for filename, wrap_id, svg_id, svg in figures:
        target = OUT / filename
        target.write_text(
            wrap(
                wrap_id=wrap_id,
                svg_id=svg_id,
                svg=svg,
            )
        )
        print(f"wrote {target.relative_to(OUT.parent.parent)}")


if __name__ == "__main__":
    main()
