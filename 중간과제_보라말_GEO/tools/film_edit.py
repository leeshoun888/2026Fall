"""AI 영화 편집: Kling 클립 7개 + 엔딩 카드를 교차 전환으로 잇고, 자막·대화 UI·라벨을 얹고, 음향을 붙인다.
사용: python3 tools/film_edit.py [--draft]"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
FF = "/Users/shoun/Documents/zyxcad-ax-film/tools/ffmpeg"
OV = ROOT / "film/edit/ov"; OV.mkdir(parents=True, exist_ok=True)
W, H = 1920, 1080
CLIP, XF = 10.0, 0.5
STEP = CLIP - XF
CLIPS = ["k1", "k2", "k3", "k4", "k5", "k6", "k7"]
END_LEN = 4.0
TOTAL = STEP * len(CLIPS) + END_LEN  # 66.5 + 4 = 70.5 → 마지막 XF 만큼 겹쳐 70.0
TOTAL = TOTAL - XF
FONT = lambda w, s: ImageFont.truetype(str(ROOT / f"assets/fonts/Pretendard-{w}.otf"), s)
VO = {"f1": 1.4, "f2": 10.2, "f3": 20.5, "f4": 29.5, "f5": 38.8, "f6": 48.6, "f7": 64.0}
LINES = json.loads((ROOT / "audio/film_lines.json").read_text())


def canvas():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def shadow_text(d, xy, s, f, fill=(255, 255, 255, 255), anchor="mm"):
    x, y = xy
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)]:
        d.text((x + dx, y + dy), s, font=f, fill=(0, 0, 0, 170), anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def subtitle(text):
    im = canvas(); d = ImageDraw.Draw(im); f = FONT("Bold", 44)
    # 쉼표 기준으로 두 줄 나누기(너무 길 때)
    lines = [text]
    if d.textlength(text, font=f) > 1500:
        cut = text.rfind(",", 0, len(text) // 2 + 8)
        cut = cut if cut > 0 else text.find(" ", len(text) // 2)
        lines = [text[:cut + 1].strip(), text[cut + 1:].strip()]
    y0 = H - 80 - (len(lines) - 1) * 62
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f)
        d.rounded_rectangle([W / 2 - tw / 2 - 26, y0 + i * 62 - 34, W / 2 + tw / 2 + 26, y0 + i * 62 + 30], 14, fill=(0, 0, 0, 120))
        shadow_text(d, (W / 2, y0 + i * 62), l, f)
    return im


def chat(msgs, x=1240, y=150, w=560):
    """휴대폰 AI 대화 화면 카드."""
    im = canvas(); d = ImageDraw.Draw(im)
    h = 120 + sum(60 * len(m[1].split("\n")) + 50 for m in msgs)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x + 8, y + 14, x + w + 8, y + h + 14], 40, fill=(0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    d.rounded_rectangle([x, y, x + w, y + h], 40, fill=(18, 14, 38, 235), outline=(90, 76, 170, 255), width=3)
    d.text((x + w / 2, y + 48), "AI 어시스턴트", font=FONT("Bold", 26), fill=(185, 178, 217), anchor="mm")
    yy = y + 100
    for who, s, col in msgs:
        ls = s.split("\n"); f = FONT("SemiBold", 32)
        tw = max(d.textlength(l, font=f) for l in ls) + 48; th = len(ls) * 46 + 28
        bx = x + w - 30 - tw if who == "me" else x + 30
        d.rounded_rectangle([bx, yy, bx + tw, yy + th], 24, fill=col)
        for i, l in enumerate(ls): d.text((bx + 24, yy + 16 + i * 46), l, font=f, fill="white")
        yy += th + 22
    return im


def chip(text, x=80, y=80, col=(139, 108, 255, 230)):
    im = canvas(); d = ImageDraw.Draw(im); f = FONT("Bold", 34)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + tw + 56, y + 68], 34, fill=col)
    d.text((x + 28, y + 34), text, font=f, fill="white", anchor="lm")
    return im


def lower_third(title, sub):
    im = canvas(); d = ImageDraw.Draw(im)
    d.rectangle([80, 760, 88, 880], fill=(139, 108, 255, 255))
    shadow_text(d, (112, 800), title, FONT("Black", 64), anchor="lm")
    shadow_text(d, (114, 860), sub, FONT("Bold", 34), fill=(225, 218, 255, 255), anchor="lm")
    return im


def title_card():
    im = canvas(); d = ImageDraw.Draw(im)
    shadow_text(d, (W / 2, 470), "읽히지 않는 제품", FONT("Black", 110))
    shadow_text(d, (W / 2, 580), "보라말 GEO · AI 영화", FONT("Bold", 38), fill=(215, 205, 255, 255))
    return im


def overlays():
    t = lambda k: CLIPS.index(k) * STEP
    ov = [("title", title_card(), 0.4, 4.2)]
    ov += [("chat1a", chat([("me", "이 분유, 알레르기 성분 있어?", (139, 108, 255))]), 3.4, 6.2),
           ("chat1b", chat([("me", "이 분유, 알레르기 성분 있어?", (139, 108, 255)), ("ai", "확인된 공식 정보를\n찾지 못했어요.", (110, 40, 60))]), 6.2, 9.6)]
    ov += [("c2", chip("자사몰 상세페이지 · 정보는 전부 사진 속"), t("k2") + 1.0, t("k2") + 9.0)]
    ov += [("c3", lower_third("보라말", "이소운 · 이시운  |  AI가 읽는 제품 정보"), t("k3") + 1.6, t("k3") + 8.6)]
    ov += [("c4", chip("STEP 1  AI 이미지 분석: 사진 속 글자를 데이터로"), t("k4") + .8, t("k4") + 9.0)]
    ov += [("c5a", chip("STEP 2  식약처 공공 영양성분 DB와 대조"), t("k5") + .8, t("k5") + 4.8),
           ("c5b", chip("STEP 3  AI 전용 공식 제품정보 사이트 발행"), t("k5") + 4.8, t("k5") + 9.0)]
    ov += [("chat6", chat([("me", "이 분유, 알레르기 성분 있어?", (139, 108, 255)), ("ai", "우유·대두를 함유하고 있어요.\n출처: 제조사 공식 제품 가이드", (28, 110, 88))], x=120, y=170), t("k6") + 1.6, t("k6") + 9.2)]
    for lid, st in VO.items():
        en = st + LINES[lid]["dur"] + .2
        if lid == "f7": en = min(en, STEP * len(CLIPS) + .2)  # 엔딩 카드 위에는 자막을 두지 않음
        ov.append((f"sub_{lid}", subtitle(LINES[lid]["text"]), st, en))
    return ov


def main():
    draft = "--draft" in sys.argv
    if "--origami" in sys.argv:
        # 종이접기 버전: 첫 프레임을 종이접기로 바꾼 Kling std 컷 7개
        clips = ["../origami/o1", "../origami/o2", "../origami/o3", "../origami/o4", "../origami/o5", "../origami/o6", "../origami/o7"]
    else:
        clips = [c + "r" if (ROOT / f"film/clips/{c}r.mp4").exists() else c for c in CLIPS]
    end_png = ROOT / "film/edit/endcard.jpg"
    if not end_png.exists():
        subprocess.run(["node", "tools/render.mjs", "stills", "69.2", "--dir", "film/edit/end"], cwd=ROOT, check=True)
        (ROOT / "film/edit/end/t069.2.jpg").rename(end_png)
    # 1단계: 클립 7개 + 엔딩 카드를 교차 전환으로 잇기
    base = ROOT / "film/edit/base.mp4"
    args = [FF, "-v", "error", "-y"]
    for k in clips: args += ["-i", str(ROOT / f"film/clips/{k}.mp4")]
    end_mp4 = ROOT / "film/edit/endcard.mp4"
    subprocess.run([FF, "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", str(END_LEN), "-i", str(end_png),
                    "-c:v", "h264_videotoolbox", "-b:v", "8M", "-pix_fmt", "yuv420p", "-r", "30", str(end_mp4)], check=True)
    args += ["-i", str(end_mp4)]
    def fit(c):
        # 정사각형 프리셋 결과는 얼굴이 잘리지 않게 위쪽에 맞춰 16:9로 자른다
        if c.endswith("_preset"): return "crop=iw:iw*9/16:0:ih*0.08,scale=1920:1080"
        return "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"
    fc = [f"[{i}:v]{fit(c)},trim=0:{CLIP},setpts=PTS-STARTPTS,fps=30,format=yuv420p[v{i}]" for i, c in enumerate(clips)]
    n = len(clips)
    fc.append(f"[{n}:v]scale=1920:1080,setpts=PTS-STARTPTS,fps=30,format=yuv420p[v{n}]")
    cur = "v0"
    for i in range(1, n + 1):
        fc.append(f"[{cur}][v{i}]xfade=transition=fade:duration={XF}:offset={STEP * i:.3f}[x{i}]"); cur = f"x{i}"
    args += ["-filter_complex", ";".join(fc), "-map", f"[{cur}]", "-c:v", "h264_videotoolbox", "-b:v", "20M", str(base)]
    subprocess.run(args, check=True)
    # 2단계: 자막·대화 UI·라벨을 프레임마다 알파 합성
    import numpy as np
    ov = [(np.asarray(im, dtype=np.float32), a, b) for _, im, a, b in overlays()]
    nfr = int(TOTAL * 30)
    dec = subprocess.Popen([FF, "-v", "error", "-i", str(base), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    name = "2_AI영화_보라말_GEO_읽히지않는제품.mp4" if "--origami" in sys.argv else "../film/alt/AI영화_실사풍_버전.mp4"
    out = ROOT / ("film/edit/draft.mp4" if draft else f"deliverables/{name}")
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "30", "-i", "-",
                            "-i", str(ROOT / "audio/film_mix.wav"), "-t", f"{TOTAL:.2f}", "-c:v", "h264_videotoolbox", "-b:v", "6M" if draft else "5M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    sz = W * H * 3
    for f in range(nfr):
        buf = dec.stdout.read(sz)
        if len(buf) < sz: break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
        t = f / 30
        if t < .8: fr *= t / .8
        for im, a, b in ov:
            if not (a <= t <= b): continue
            k = min(1, (t - a) / .35, (b - t) / .35)
            al = im[..., 3:4] / 255 * k
            fr = fr * (1 - al) + im[..., :3] * al
        enc.stdin.write(fr.clip(0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()
    print("wrote", out, f"{TOTAL:.1f}s", clips)


if __name__ == "__main__":
    main()
