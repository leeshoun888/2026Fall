"""ElevenLabs 나레이션: 줄마다 따로 생성(장면 시간 맞추기 쉬움). 응답은 audio/takes/ 에 저장해 재사용.
사용: python tools/vo.py motion|film [--force]"""
import base64, json, sys, urllib.request, urllib.error, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
FF = "/Users/shoun/Documents/zyxcad-ax-film/tools/ffmpeg"
key = [l.split("=",1)[1].strip() for l in (ROOT/".env").read_text().splitlines() if l.startswith("ELEVENLABS_API_KEY=")][0]
which = sys.argv[1]
cfg = json.loads((ROOT/"script/narration.json").read_text())[which]
out = ROOT/"audio/takes"; out.mkdir(parents=True, exist_ok=True)
prev = None
info = {}
for lid, text in cfg["lines"]:
    mp3 = out/f"{lid}.mp3"
    if not mp3.exists() or "--force" in sys.argv:
        body = {"text": text, "model_id": "eleven_v4", "language_code": "ko", "seed": 7}
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice']}/with-timestamps?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
        try: d = json.load(urllib.request.urlopen(req, timeout=300))
        except urllib.error.HTTPError as e: print("ERR", e.code, e.read()[:300]); sys.exit(1)
        mp3.write_bytes(base64.b64decode(d["audio_base64"]))
        (out/f"{lid}.json").write_text(json.dumps(d["alignment"], ensure_ascii=False))
    dur = float(subprocess.run([FF, "-i", str(mp3)], capture_output=True, text=True).stderr.split("Duration: ")[1].split(",")[0].split(":")[-1])
    info[lid] = {"text": text, "dur": round(dur, 2)}
    print(lid, info[lid]["dur"], text)
(ROOT/f"audio/{which}_lines.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
print("total", round(sum(v["dur"] for v in info.values()), 2))
