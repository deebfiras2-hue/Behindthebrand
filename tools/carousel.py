"""Render a carousel from a JSON spec: python3 tools/carousel.py spec.json outdir"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import *
W,H,M = 1080,1350,84

def footer(img, d, dark, right):
    c = RULE_D if dark else RULE
    d.line((M,1248,W-M,1248), fill=c, width=2)
    wordmark(d, M, 1268, 30, dark=dark)
    spaced(d, (W-M,1272), right, barlow(26), GRAY, 3, "r")

def header(img, d, label, dark):
    spaced(d, (M,76), label, barlow(26), GRAY if not dark else CREAM, 4)
    logo(img, W-M-84, 64, 84)

def cover(spec):
    img = Image.new("RGB",(W,H),INK); d = ImageDraw.Draw(img)
    # pill
    f = barlow(26); t = spec["pill"]; w = tw(d,t,f,4)+56
    d.rounded_rectangle((M,60,M+w,60+58), radius=29, outline=CREAM, width=2)
    spaced(d,(M+28,74),t,f,CREAM,4)
    logo(img, W-M-84, 64, 84)
    # hero
    hero = spec["hero"]; size = spec.get("hero_size", 360)
    cur = spec.get("hero_cur", "")
    fh = gel(size); fc = gel(int(size*0.42))
    wc = d.textlength(cur, font=fc) if cur else 0
    wh = d.textlength(hero, font=fh)
    total = wc + (10 if cur else 0) + wh
    x = (W-total)/2; base = spec.get("hero_y", 250)
    if cur:
        d.text((x, base+size*0.05), cur, font=fc, fill=GREEN)
        x += wc+10
    d.text((x, base), hero, font=fh, fill=CREAM)
    # label box
    fl = barlow(34, True); lt = spec["label"]; lw = tw(d,lt,fl,5)+72
    ly = base + size*1.22 + 10
    d.rectangle((M, ly, M+lw, ly+78), fill=GREEN)
    spaced(d,(M+36,ly+17),lt,fl,WHITE,5)
    # headline
    hy = ly+78+54
    draw_rich(img, d, M, hy, spec["headline"], 78, W-2*M, 98, CREAM, gel, True)
    footer(img, d, True, "SWIPE ›")
    return img

def inner(spec, n, total):
    img = Image.new("RGB",(W,H),CREAM); d = ImageDraw.Draw(img)
    header(img, d, spec["label"], False)
    y = 330
    if spec.get("kicker"):
        spaced(d,(M,y),spec["kicker"],barlow(30,True),GREEN,4); y += 62
    kind = spec.get("kind","text")
    if kind == "quote":
        d.text((M-6,y-30),"“",font=gel(260),fill=GREEN)
        y += 150
        y = draw_rich(img,d,M,y,spec["quote"],(qs:=spec.get("qsize",72)),W-2*M,qs*1.34,INK,lambda s,bold=False:gel(s,bold,True),False,GREEN)
        y += 14
        if spec.get("by"): 
            d.text((M,y),spec["by"],font=barlow(28,True),fill=GRAY); y += 70
        if spec.get("body"):
            y += 20; draw_rich(img,d,M,y,spec["body"],38,W-2*M,54,INK)
    else:
        if spec.get("headline"):
            y = draw_rich(img,d,M,y,spec["headline"],spec.get("hsize",90),W-2*M,spec.get("hsize",90)*1.12,INK,gel,True)+36
        if kind == "rows":
            for left, right in spec["rows"]:
                fl = gel(spec.get("lsize",56))
                d.text((M,y),left,font=fl,fill=GREEN)
                end = draw_rich(img,d,M+270,y+4,right,38,W-2*M-270,52,INK)
                y = max(end, y+84)+34
                d.line((M,y-18,W-M,y-18),fill=RULE,width=2)
        if spec.get("body"):
            draw_rich(img,d,M,y,spec["body"],(bs:=spec.get("bsize",40)),W-2*M,bs*1.44,INK)
    if spec.get("source"):
        d.text((M,1190),"Source: "+spec["source"],font=barlow(21),fill=GRAY)
    footer(img,d,False,f"{n:02d} / {total:02d}")
    return img

def last(spec, n, total):
    img = Image.new("RGB",(W,H),INK); d = ImageDraw.Draw(img)
    header(img,d,"THE LESSON",True)
    y=330
    spaced(d,(M,y),"THE BUSINESS MOVE",barlow(30,True),GREEN,4); y+=62
    y = draw_rich(img,d,M,y,spec["headline"],88,W-2*M,100,CREAM,gel,True)+30
    y = draw_rich(img,d,M,y,spec["body"],40,W-2*M,56,(215,210,200))+50
    f=barlow(34,True); t="FOLLOW FOR MORE"; w=tw(d,t,f,5)+96+60
    d.rounded_rectangle((M,y,M+w,y+96),radius=48,fill=GREEN)
    wt=spaced(d,(M+48,y+27),"FOLLOW FOR MORE",f,WHITE,5)
    ax=M+48+wt+22; ay=y+48
    d.line((ax,ay,ax+34,ay),fill=WHITE,width=5); d.line((ax+22,ay-13,ax+36,ay),fill=WHITE,width=5); d.line((ax+22,ay+13,ax+36,ay),fill=WHITE,width=5)
    footer(img,d,True,f"{n:02d} / {total:02d}")
    return img

def render(spec, out):
    os.makedirs(out, exist_ok=True)
    total = 2 + len(spec["slides"])
    imgs = [cover(spec["cover"])] + [inner(s,i+2,total) for i,s in enumerate(spec["slides"])] + [last(spec["last"],total,total)]
    paths=[]
    for i,im in enumerate(imgs,1):
        p=os.path.join(out,f"{i}.jpg"); im.save(p,"JPEG",quality=95,subsampling=0); paths.append(p)
    return paths, imgs[0]

if __name__=="__main__":
    spec=json.load(open(sys.argv[1])); print(render(spec,sys.argv[2])[0])
