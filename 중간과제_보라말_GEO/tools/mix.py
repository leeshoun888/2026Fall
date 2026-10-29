"""나레이션 + 배경음악(나레이션 구간 덕킹) + 전환 효과음 → 48kHz 스테레오 WAV, -14 LUFS.
사용: python tools/mix.py motion|film"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf
ROOT = Path(__file__).resolve().parent.parent
FF = "/Users/shoun/Documents/zyxcad-ax-film/tools/ffmpeg"
SR = 48000
which = sys.argv[1]
CFG = {
  # 나레이션 시작 시각은 motion/index.html 의 VO 와 같아야 한다
  "motion": dict(dur=71.0, bgm="audio/music/175.mp3", bgm_start=0.0, bgm_db=-17, duck_db=-9, fade_out=2.5,
                 vo={"m1": 0.6, "m2": 5.5, "m3": 13.2, "m4": 24.4, "m5": 35.2, "m6": 53.4, "m7": 61.3, "m8": 66.5},
                 whoosh=[5.15, 12.85, 24.05, 34.85, 53.05, 60.95, 66.15]),
  "film": dict(dur=70.0, bgm="audio/music/543.mp3", bgm_start=8.0, bgm_db=-12, duck_db=-7, fade_out=3.0,
               vo={"f1": 1.4, "f2": 10.2, "f3": 20.5, "f4": 29.5, "f5": 38.8, "f6": 48.6, "f7": 64.0},
               whoosh=[]),
}[which]

def load(p, start=0.0, dur=None):
    args = [FF, "-v", "error", "-ss", str(start), "-i", str(ROOT / p)]
    if dur: args += ["-t", str(dur)]
    raw = subprocess.run(args + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

n = int(CFG["dur"] * SR)
vo = np.zeros((n, 2), np.float32); mask = np.zeros(n, np.float32)
for lid, t in CFG["vo"].items():
    x = load(f"audio/takes/{lid}.mp3"); a = int(t * SR); b = min(n, a + len(x))
    vo[a:b] += x[:b - a]; mask[max(0, a - int(.25 * SR)):min(n, b + int(.35 * SR))] = 1
# 덕킹 곡선을 부드럽게
k = int(.3 * SR); mask = np.convolve(mask, np.ones(k) / k, mode="same")
m = load(CFG["bgm"], CFG["bgm_start"], CFG["dur"] + 1)[:n]
if len(m) < n: m = np.pad(m, ((0, n - len(m)), (0, 0)))
gain_db = CFG["bgm_db"] + CFG["duck_db"] * mask
g = 10 ** (gain_db / 20)
fi = np.clip(np.arange(n) / (1.0 * SR), 0, 1); fo = np.clip((n - np.arange(n)) / (CFG["fade_out"] * SR), 0, 1)
m = m * (g * fi * fo)[:, None]
# 전환 효과음: 걸러낸 잡음 스윕
rng = np.random.default_rng(3); sfx = np.zeros((n, 2), np.float32)
for t in CFG["whoosh"]:
    L = int(.6 * SR); e = np.sin(np.linspace(0, np.pi, L)) ** 2
    w = rng.standard_normal(L).astype(np.float32)
    # 간단한 1차 저역 통과(차단 주파수가 올라가는 스윕)
    y = np.zeros(L, np.float32); acc = 0.0
    for i in range(L):
        a_ = .02 + .25 * (i / L); acc += a_ * (w[i] - acc); y[i] = acc
    y *= e * .18; a = int((t - .3) * SR)
    pan = np.linspace(-1, 1, L)
    sfx[a:a + L, 0] += y * (1 - pan) / 2 * 1.4; sfx[a:a + L, 1] += y * (1 + pan) / 2 * 1.4
mix = vo * 1.0 + m + sfx
out = ROOT / f"audio/{which}_mix_raw.wav"; sf.write(out, mix, SR, subtype="FLOAT")
final = ROOT / f"audio/{which}_mix.wav"
subprocess.run([FF, "-v", "error", "-y", "-i", str(out), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), str(final)], check=True)
out.unlink(); print("wrote", final)
