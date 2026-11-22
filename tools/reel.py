"""Build a reel. usage: python3 tools/reel.py spec.json workdir out_dir
spec: {script, shots:[{at, kind:card|clip, ...}], keywords:[...]}; needs workdir/voice.mp3 + align.json (ElevenLabs with-timestamps)."""
import sys, os, json, re, subprocess, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import *
import numpy as np
W,H,FPS = 1080,1920,30
SPEED=1.08; LEAD=0.3
ROOT_=ROOT

def words_from_alignment(al, text):
    ch=al["characters"]; st=al["character_start_times_seconds"]; en=al["character_end_times_seconds"]
    words=[]; cur=""; s=None; e=None
    for c,a,b in zip(ch,st,en):
        if c.isspace():
            if cur: words.append((cur,s,e)); cur=""
            continue
        if not cur: s=a
        cur+=c; e=b
    if cur: words.append((cur,s,e))
    return [(w, s/SPEED+LEAD, e/SPEED+LEAD) for w,s,e in words]

def find(words, phrase):
    toks=phrase.lower().split()
    clean=lambda w: re.sub(r"[^\w'’-]","",w.lower())
    for i in range(len(words)-len(toks)+1):
        if all(clean(words[i+j][0])==clean(t) for j,t in enumerate(toks)): return words[i][1]
    raise ValueError("phrase not found: "+phrase)

def cover_bg(kind_card):
    return Image.new("RGB",(W,H), INK if kind_card=="ink" else CREAM)

def card_image(s):
    dark = s.get("bg","ink")=="ink"
    img = cover_bg(s.get("bg","ink")); d=ImageDraw.Draw(img)
    fg = CREAM if dark else INK
    if s.get("logo",True): logo(img,(W-84)//2,270,84)
    big=s["big"]; size=s.get("size",320)
    cur=s.get("cur","")
    fh=gel(size)
    # shrink to fit
    while d.textlength(big,font=fh)+ (d.textlength(cur,font=gel(int(size*.42)))+10 if cur else 0) > W-120 and size>80:
        size-=10; fh=gel(size)
    y=max(380,850-size*1.28-84)
    fc=gel(int(size*.42)); wc=d.textlength(cur,font=fc)+10 if cur else 0
    wb=d.textlength(big,font=fh); x=(W-wb-wc)/2
    if cur: d.text((x,y+size*.05),cur,font=fc,fill=GREEN); x+=wc
    d.text((x,y),big,font=fh,fill=fg if not s.get("bigGreen") else GREEN)
    ly=y+size*1.28
    if s.get("label"):
        fl=barlow(38,True); lw=tw(d,s["label"],fl,5)+80
        d.rectangle(((W-lw)/2,ly,(W+lw)/2,ly+84),fill=GREEN)
        spaced(d,(W/2,ly+20),s["label"],fl,WHITE,5,"c")
    return img

def intro_overlay(img):
    pass

def render_clip(src, dur, out):
    # cover-crop to 1080x1920, darken ~35%, from start offset 0.5s
    subprocess.run(["ffmpeg","-y","-v","error","-ss","0.5","-t",f"{dur+0.2:.2f}","-i",src,"-vf",
      f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},eq=brightness=-0.18:contrast=0.95,setsar=1",
      "-an","-pix_fmt","yuv420p",out],check=True)

def reader(path):
    p=subprocess.Popen(["ffmpeg","-v","error","-i",path,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
    n=W*H*3
    def nxt():
        b=p.stdout.read(n)
        return None if len(b)<n else Image.frombytes("RGB",(W,H),b)
    return nxt

def outline_text(d, xy, text, font, fill, stroke=12, anchor="mm"):
    d.text(xy,text,font=font,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=INK)

def build(spec, work, outdir):
    words = words_from_alignment(json.load(open(f"{work}/align.json")), "")
    vdur = json.load(open(f"{work}/align.json"))["character_end_times_seconds"][-1]/SPEED
    T = LEAD + vdur + 0.5
    nframes = int(T*FPS)
    shots=[]
    for s in spec["shots"]:
        t = 0.0 if s["at"]=="start" else find(words,s["at"])
        shots.append(dict(s,t=t))
    shots.sort(key=lambda s:s["t"])
    for i,s in enumerate(shots): s["end"]=shots[i+1]["t"] if i+1<len(shots) else T
    os.makedirs(f"{work}/seg",exist_ok=True)
    for i,s in enumerate(shots):
        if s["kind"]=="clip":
            s["seg"]=f"{work}/seg/{i}.mp4"; render_clip(os.path.join(ROOT_,s["src"]) if not os.path.isabs(s["src"]) else s["src"], s["end"]-s["t"]+0.1, s["seg"])
        else: s["img"]=card_image(s)
    # caption groups
    key=set(k.lower() for k in spec.get("keywords",[]))
    groups=[]; cur=[]
    for i,(w,a,b) in enumerate(words):
        cur.append(i)
        if len(cur)>=3 or re.search(r"[.,?!]$",w) or (len(cur)>=2 and sum(len(words[k][0])+1 for k in cur)>=12) or (i+1<len(words) and sum(len(words[k][0])+1 for k in cur)+len(words[i+1][0])>15):
            groups.append(cur); cur=[]
    if cur: groups.append(cur)
    fcap=gel(112); 
    out=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-an","-c:v","libx264","-profile:v","high","-pix_fmt","yuv420p","-crf","18","-preset","medium","-movflags","+faststart",f"{work}/silent.mp4"],stdin=subprocess.PIPE)
    readers={}
    for f in range(nframes):
        t=f/FPS
        s=next(x for x in reversed(shots) if x["t"]<=t+1e-6)
        if s["kind"]=="clip":
            if id(s) not in readers: readers[id(s)]=reader(s["seg"])
            fr=readers[id(s)]()
            img=(fr if fr is not None else Image.new("RGB",(W,H),INK))
        else:
            img=s["img"].copy()
        d=ImageDraw.Draw(img)
        # intro (first 1s): small logo top on every non-card? hook text handled by first card
        if t<1.0 and s["kind"]=="clip": logo(img,(W-84)//2,290,84)
        # outro last 2s
        if t>=T-2.4:
            a=min(1,(t-(T-2.4))/0.3)
            ov=Image.new("RGB",(W,H),INK); img=Image.blend(img,ov,min(1,a)); d=ImageDraw.Draw(img)
            logo(img,(W-220)//2,640,220)
            wordmark(d,W/2,860,70,True,"c") if False else None
            fb=gel(72); wm_w=sum(d.textlength(x,font=ff) for x,ff in [("BEHIND ",fb),("the",gel(72,italic=True)),(" BRAND",fb)])
            wordmark(d,(W-wm_w)/2,860,72,True)
            spaced(d,(W/2,990),"FOLLOW @behindthebrand.explained".upper().replace("@BEHINDTHEBRAND.EXPLAINED","@behindthebrand.explained"),barlow(32,True),GREEN,3,"c")
        else:
            # captions
            g=next((g for g in groups if words[g[0]][1]-0.02<=t<(words[g[-1]][2]+0.12 if g is not groups[-1] else T)),None)
            if g is not None and s["kind"]!="never":
                cw=[]
                for i in g:
                    w=words[i][0]; cl=re.sub(r"[^\w$%]","",w.lower())
                    cw.append((w, cl in key or bool(re.search(r"\d",w))))
                cur_i=max([k for k,i in enumerate(g) if words[i][1]<=t] or [0])
                dummy=ImageDraw.Draw(img)
                # pop scale of current word
                age=(t-words[g[cur_i]][1])*FPS
                sc=1.15-0.15*min(1,age/4)
                fonts=[gel(int(112*(sc if k==cur_i else 1))) for k in range(len(g))]
                widths=[dummy.textlength(cw[k][0],font=fonts[k]) for k in range(len(g))]
                gap=26; total=sum(widths)+gap*(len(g)-1)
                # wrap to two lines if too wide
                lines=[list(range(len(g)))]
                if total>W-120:
                    half=len(g)//2 or 1; lines=[list(range(half)),list(range(half,len(g)))]
                y0=1114-(len(lines)-1)*70
                for li,ln in enumerate(lines):
                    lw=sum(widths[k] for k in ln)+gap*(len(ln)-1); x=(W-lw)/2
                    for k in ln:
                        outline_text(dummy,(x+widths[k]/2,y0+li*140),cw[k][0],fonts[k],GREEN if cw[k][1] else CREAM,12)
                        x+=widths[k]+gap
        # progress bar
        d.rectangle((0,0,W*t/T,10),fill=GREEN)
        out.stdin.write(img.tobytes())
    out.stdin.close(); out.wait()
    # audio
    sfx=os.path.join(ROOT_,"assets","sfx")
    cuts=[s["t"] for s in shots[1:]]
    hits=[s["t"] for s in shots if s.get("hit")]
    inputs=["-i",f"{work}/voice.mp3","-i",f"{sfx}/whoosh.mp3","-i",f"{sfx}/hit.mp3"]
    fc=[f"[0:a]atempo={SPEED},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[v]"]
    mix=["[v]"]
    for i,c in enumerate(cuts):
        fc.append(f"[1:a]volume=0.22,aresample=48000,adelay={int(max(0,c-0.08)*1000)}|{int(max(0,c-0.08)*1000)}[w{i}]"); mix.append(f"[w{i}]")
    for i,c in enumerate(hits):
        fc.append(f"[2:a]volume=0.3,aresample=48000,adelay={int(c*1000)}|{int(c*1000)}[h{i}]"); mix.append(f"[h{i}]")
    fc.append("".join(mix)+f"amix=inputs={len(mix)}:normalize=0:duration=longest,apad,atrim=0:{T:.3f},aformat=channel_layouts=stereo:sample_rates=48000[a]")
    os.makedirs(outdir,exist_ok=True)
    subprocess.run(["ffmpeg","-y","-v","error",*inputs,"-i",f"{work}/silent.mp4","-filter_complex",";".join(fc),"-map","3:v","-map","[a]",
        "-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-movflags","+faststart","-t",f"{T:.3f}",f"{outdir}/reel.mp4"],check=True)
    return shots,words,T

if __name__=="__main__":
    spec=json.load(open(sys.argv[1])); shots,words,T=build(spec,sys.argv[2],sys.argv[3])
    print(T); [print(round(s["t"],2),s["kind"],s.get("big",s.get("src"))) for s in shots]
