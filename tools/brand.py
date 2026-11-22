"""Brand constants + drawing helpers for BEHIND THE BRAND."""
import os, re
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "assets", "fonts")
CREAM=(243,238,228); INK=(17,17,17); GREEN=(14,159,110); GRAY=(107,103,95)
RULE=(217,210,196); RULE_D=(42,42,42); WHITE=(255,255,255)

def gel(size, bold=True, italic=False):
    p = os.path.join(F, "Gelasio-Italic-VF.ttf" if italic else "Gelasio-VF.ttf")
    f = ImageFont.truetype(p, size)
    f.set_variation_by_name("Bold Italic" if italic and bold else ("Italic" if italic else ("Bold" if bold else "Regular")))
    return f
def barlow(size, bold=False):
    return ImageFont.truetype(os.path.join(F, "Barlow-Bold.ttf" if bold else "Barlow-SemiBold.ttf"), size)

def tw(d, text, font, spacing=0):
    return d.textlength(text, font=font) + spacing*max(len(text)-1, 0)

def spaced(d, xy, text, font, fill, spacing=4, anchor="l"):
    """Letter-spaced text. anchor l/r on x; xy is baseline-top (y = top)."""
    x, y = xy
    w = tw(d, text, font, spacing)
    if anchor == "r": x -= w
    elif anchor == "c": x -= w/2
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + spacing
    return w

def tag_polygon(x, y, w, h):
    """Price tag pointing LEFT: left point at mid-height, body to the right."""
    pt = h*0.42
    return [(x, y+h/2), (x+pt, y), (x+w, y), (x+w, y+h), (x+pt, y+h)]

def logo(img, x, y, w=84, ss=4):
    """Mini price-tag logo (ratio ~1.7:1), green, hole near left point, cream serif B."""
    h = int(w/1.7)
    S = Image.new("RGBA", (w*ss, h*ss), (0,0,0,0)); d = ImageDraw.Draw(S)
    d.polygon(tag_polygon(0,0,w*ss,h*ss), fill=GREEN+(255,))
    r = h*ss*0.075; cx = h*ss*0.42*0.92; cy = h*ss/2
    d.ellipse((cx-r,cy-r,cx+r,cy+r), fill=(0,0,0,0))
    # punch hole: composite transparent
    hole = Image.new("L", S.size, 255); ImageDraw.Draw(hole).ellipse((cx-r,cy-r,cx+r,cy+r), fill=0)
    S.putalpha(Image.composite(S.getchannel("A"), Image.new("L",S.size,0), hole))
    d = ImageDraw.Draw(S)
    f = gel(int(h*ss*0.66))
    bx = h*ss*0.42 + (w*ss - h*ss*0.42)/2
    d.text((bx, h*ss*0.52), "B", font=f, fill=CREAM+(255,), anchor="mm")
    S = S.resize((w,h), Image.LANCZOS)
    img.paste(S, (int(x),int(y)), S)
    return h

def wordmark(d, x, y, size, dark=True, anchor="l"):
    """BEHIND the BRAND wordmark; returns width."""
    base = CREAM if dark else INK
    fb = gel(size); fi = gel(size, italic=True)
    parts = [("BEHIND ", fb, base), ("the", fi, GREEN), (" BRAND", fb, base)]
    total = sum(d.textlength(t, font=f) for t,f,_ in parts)
    if anchor == "r": x -= total
    xx = x
    for t,f,c in parts:
        d.text((xx,y), t, font=f, fill=c); xx += d.textlength(t, font=f)
    return total

# ---- rich text: *bold*  {green}  ==highlight==  ----
TOK = re.compile(r"(\{[^}]*\}|\*[^*]*\*|==[^=]*==)")
def parse(text):
    out=[]
    for p in TOK.split(text):
        if not p: continue
        if p.startswith("{"): out.append((p[1:-1],"g"))
        elif p.startswith("*"): out.append((p[1:-1],"b"))
        elif p.startswith("=="): out.append((p[2:-2],"h"))
        else: out.append((p,""))
    return out

def layout(d, text, size, maxw, fontfn, line_h, base_bold=False):
    """Wrap rich text -> list of lines, each list of (word, style, x)."""
    words=[]
    for seg, st in parse(text):
        for i, w in enumerate(re.split(r"(\s+)", seg)):
            if w.strip(): words.append((w, st))
    def font(st): return fontfn(size, bold=(base_bold or st in ("b","g","h")))
    lines=[]; cur=[]; x=0
    sp = d.textlength(" ", font=font(""))
    for w, st in words:
        ww = d.textlength(w, font=font(st))
        if cur and x+sp+ww > maxw:
            lines.append(cur); cur=[]; x=0
        if cur: x += sp
        cur.append((w, st, x)); x += ww
    if cur: lines.append(cur)
    return lines

def draw_rich(img, d, x, y, text, size, maxw, line_h, fill, fontfn=gel, base_bold=False, gcolor=GREEN, hl=True):
    lines = layout(d, text, size, maxw, fontfn, line_h, base_bold)
    def font(st): return fontfn(size, bold=(base_bold or st in ("b","g","h")))
    # highlighter bands first
    for i, ln in enumerate(lines):
        j=0
        while j < len(ln):
            if ln[j][1] == "h":
                k=j
                while k+1 < len(ln) and ln[k+1][1]=="h": k+=1
                x0 = x+ln[j][2]; x1 = x+ln[k][2]+d.textlength(ln[k][0], font=font("h"))
                ty = y+i*line_h
                d.rectangle((x0-4, ty+size*0.62, x1+4, ty+size*0.62+size*0.34), fill=(190,232,212))
                j=k+1
            else: j+=1
    for i, ln in enumerate(lines):
        for w, st, wx in ln:
            d.text((x+wx, y+i*line_h), w, font=font(st), fill=gcolor if st=="g" else fill)
    return y + len(lines)*line_h
