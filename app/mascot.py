"""Дасгалжуулагчийн дүр: хэрэглэгчтэй хамт "шинэчлэгддэг" робот.

- Шат (level-ээс): 1 = зөвхөн толгой, 2 = их бие, гар хөл, 3 = чихэвч, цэнэг, булчин, 4 = алтан "Аварга"
- Зорилго (хэрэглэгчийн сонгосноос, биеийн хэмжээнээс БИШ): lose = гүйгч (улаан тууз, гутал),
  gain = гантельтай (цэнхэр), fit = усны савтай, зүрхтэй (ногоон)

Зураг нь файл биш, эндээс SVG болж гардаг — өнгө, хэлбэрийг энэ файлаас л өөрчилнө.
"""
from markupsafe import Markup, escape

INK, STEEL, GLOW, GOLD = "#16213a", "#8fa3c8", "#6ff0c0", "#ffc94d"
ACCENT = {"lose": "#ff6b4a", "gain": "#2d5bff", "fit": "#17a673"}
SHELL = ["#e6ecf8", "#d5dff5", "#c3d1f3", "#f1ead6"]


def stage_of(level: int) -> int:
    """Level → шат (1–4). xp.stage()-тэй ижил босго."""
    return 4 if level >= 8 else 3 if level >= 5 else 2 if level >= 3 else 1


def _body(st: int, goal: str | None) -> str:
    acc = ACCENT.get(goal, ACCENT["gain"])
    limb = GOLD if st == 3 else STEEL
    gid = f"rb{st}"
    hy = [56, 40, 34, 34][st]                      # толгойн дээд ирмэг
    scale = [0.9, 0.88, 0.94, 1][st]
    o = [f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/>'
         f'<stop offset="1" stop-color="{SHELL[st]}"/></linearGradient></defs>',
         f'<g transform="translate(100 190) scale({scale}) translate(-100 -190)">']
    # Антен
    if st < 3:
        o.append(f'<path d="M100 {hy}v-18" stroke="{STEEL}" stroke-width="6" stroke-linecap="round"/><circle cx="100" cy="{hy - 22}" r="8" fill="{acc}"/>')
    else:
        o.append(f'<path d="M84 {hy}l-8-18M116 {hy}l8-18" stroke="{GOLD}" stroke-width="6" stroke-linecap="round"/>'
                 f'<circle cx="75" cy="{hy - 22}" r="7" fill="{GOLD}"/><circle cx="125" cy="{hy - 22}" r="7" fill="{GOLD}"/>')
    if st == 0:
        o.append('<ellipse cx="100" cy="184" rx="34" ry="6" fill="#16213a" opacity=".12"/>')
    else:
        # Гар
        if st == 1:
            o.append(f'<path d="M56 150q-20 6-22 24M144 150q20 6 22 24" stroke="{limb}" stroke-width="12" fill="none" stroke-linecap="round"/>')
        else:
            o.append(f'<path d="M54 148q-26-4-24-30" stroke="{limb}" stroke-width="13" fill="none" stroke-linecap="round"/><circle cx="30" cy="115" r="10" fill="{limb}"/>')
            if goal == "gain":      # гантель барьсан
                o.append(f'<path d="M146 150q28 2 32-22" stroke="{limb}" stroke-width="13" fill="none" stroke-linecap="round"/>'
                         f'<path d="M166 122h28" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
                         f'<rect x="158" y="108" width="11" height="28" rx="4.5" fill="{acc}"/><rect x="190" y="108" width="11" height="28" rx="4.5" fill="{acc}"/>')
            elif goal == "fit":     # усны сав
                o.append(f'<path d="M146 150q22 4 26-14" stroke="{limb}" stroke-width="13" fill="none" stroke-linecap="round"/>'
                         f'<rect x="164" y="106" width="18" height="32" rx="6" fill="{acc}"/><rect x="168" y="98" width="10" height="10" rx="3" fill="{INK}"/>')
            else:
                o.append(f'<path d="M146 148q26-4 24-30" stroke="{limb}" stroke-width="13" fill="none" stroke-linecap="round"/><circle cx="170" cy="115" r="10" fill="{limb}"/>')
        # Их бие, хөл
        foot = acc if goal == "lose" and st >= 2 else limb
        o.append(f'<rect x="56" y="126" width="88" height="58" rx="20" fill="url(#{gid})" stroke="{SHELL[st]}" stroke-width="2"/>'
                 f'<rect x="68" y="182" width="26" height="12" rx="6" fill="{foot}"/><rect x="106" y="182" width="26" height="12" rx="6" fill="{foot}"/>')
        if st == 1:
            o.append(f'<rect x="82" y="146" width="36" height="8" rx="4" fill="{acc}"/><rect x="82" y="160" width="22" height="8" rx="4" fill="{STEEL}"/>')
        elif goal == "fit":
            o.append(f'<path d="M100 172C80 158 82 142 92 142C97 142 100 147 100 150C100 147 103 142 108 142C118 142 120 158 100 172Z" fill="{acc}"/>')
        else:
            o.append(f'<circle cx="100" cy="155" r="15" fill="{acc}"/><path d="M103 144l-9 12h7l-3 10 10-13h-7Z" fill="#fff"/>')
        if st == 3:
            o.append(f'<path d="M62 132q38 14 76 0" stroke="{GOLD}" stroke-width="5" fill="none" stroke-linecap="round"/>')
    if st >= 2:  # чихэвч
        o.append(f'<rect x="28" y="{hy + 26}" width="15" height="32" rx="7.5" fill="{acc}"/><rect x="157" y="{hy + 26}" width="15" height="32" rx="7.5" fill="{acc}"/>')
    # Толгой, дэлгэц, царай
    hh = 112 if st == 0 else 88
    cy = hy + hh / 2 - 3
    ry = 11 if st < 2 else 9
    o.append(f'<rect x="38" y="{hy}" width="124" height="{hh}" rx="32" fill="url(#{gid})" stroke="{SHELL[st]}" stroke-width="2"/>'
             f'<rect x="51" y="{hy + 14}" width="98" height="{hh - 28}" rx="21" fill="{INK}"/>'
             f'<ellipse cx="79" cy="{cy}" rx="8.5" ry="{ry}" fill="{GLOW}"/><ellipse cx="121" cy="{cy}" rx="8.5" ry="{ry}" fill="{GLOW}"/>'
             f'<circle cx="82" cy="{cy - 3}" r="2.6" fill="#fff"/><circle cx="124" cy="{cy - 3}" r="2.6" fill="#fff"/>'
             f'<path d="M89 {cy + 17}Q100 {cy + 26} 111 {cy + 17}" stroke="{GLOW}" stroke-width="4.5" fill="none" stroke-linecap="round"/>'
             f'<ellipse cx="64" cy="{cy + 12}" rx="6" ry="3.5" fill="#ff8f7a" opacity=".6"/><ellipse cx="136" cy="{cy + 12}" rx="6" ry="3.5" fill="#ff8f7a" opacity=".6"/>')
    if st >= 2:  # шийдэмгий хөмсөг
        o.append(f'<path d="M66 {cy - 18}l20 5M134 {cy - 18}l-20 5" stroke="{GLOW}" stroke-width="4.5" stroke-linecap="round"/>')
    if goal == "lose" and st >= 2:  # гүйгчийн тууз
        o.append(f'<path d="M40 {hy + 12}Q100 {hy - 4} 160 {hy + 12}" stroke="{acc}" stroke-width="10" fill="none" stroke-linecap="round"/>')
    o.append("</g>")
    return "".join(o)


def svg(size: int, level: int, goal: str | None = None, label: str = "") -> Markup:
    """Template-д: {{ avatar(56, coach.level) }} (_coach.html-ийн macro үүнийг дуудна)."""
    st = stage_of(int(level or 1)) - 1
    aria = f'role="img" aria-label="{escape(label)}"' if label else 'aria-hidden="true"'
    return Markup(f'<svg width="{int(size)}" height="{int(size)}" viewBox="-6 -4 212 208" {aria} class="flex-none">{_body(st, goal)}</svg>')
