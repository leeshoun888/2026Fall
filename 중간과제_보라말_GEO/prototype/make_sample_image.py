"""데모용 가상 제품 상세 이미지(통이미지) 생성. 실제 회사·제품 아님."""
from PIL import Image, ImageDraw, ImageFont
F = "../assets/fonts/Pretendard-"
f = lambda w, s: ImageFont.truetype(F + w + ".otf", s)
W, H = 860, 1500
im = Image.new("RGB", (W, H), "#fff7ec"); d = ImageDraw.Draw(im)
d.rectangle([0, 0, W, 520], fill="#ffd9a8")
d.text((60, 70), "고소함 그대로", font=f("Bold", 40), fill="#7a4a12")
d.text((60, 130), "보라 데모 두유", font=f("Black", 84), fill="#3b2208")
d.text((60, 240), "국산 콩 98% · 190mL", font=f("Bold", 40), fill="#7a4a12")
d.rounded_rectangle([560, 120, 780, 470], 30, fill="#fff", outline="#d29a5a", width=6)
d.text((598, 270), "DEMO", font=f("Black", 50), fill="#d29a5a")
y = 580
d.text((60, y), "영양정보", font=f("Black", 48), fill="#222"); d.text((300, y + 14), "총 내용량 190mL  105kcal", font=f("Bold", 32), fill="#222")
d.line([60, y + 80, W - 60, y + 80], fill="#222", width=6)
rows = [("나트륨", "120mg", "6%"), ("탄수화물", "7g", "2%"), ("당류", "3g", "3%"), ("지방", "5g", "9%"), ("트랜스지방", "0g", ""), ("포화지방", "0.8g", "5%"), ("콜레스테롤", "0mg", "0%"), ("단백질", "8g", "15%")]
for i, (a, b, c) in enumerate(rows):
    yy = y + 100 + i * 62
    d.text((70, yy), a, font=f("Bold", 34), fill="#222"); d.text((330, yy), b, font=f("SemiBold", 34), fill="#222"); d.text((W - 150, yy), c, font=f("Bold", 34), fill="#222")
    d.line([60, yy + 54, W - 60, yy + 54], fill="#bbb", width=2)
yy = y + 100 + len(rows) * 62 + 30
d.text((60, yy), "1일 영양성분 기준치에 대한 비율(%)은 2,000kcal 기준", font=f("SemiBold", 24), fill="#555")
d.text((60, yy + 70), "원재료명  대두(국산) 98%, 정제수, 천일염", font=f("Bold", 32), fill="#222")
d.text((60, yy + 120), "대두 함유 · 이 제품은 우유, 땅콩을 사용한 제품과", font=f("Bold", 30), fill="#c0392b")
d.text((60, yy + 160), "같은 제조 시설에서 제조하고 있습니다", font=f("Bold", 30), fill="#c0392b")
d.text((60, yy + 230), "보관  직사광선을 피해 서늘한 곳에 실온 보관", font=f("SemiBold", 28), fill="#222")
im.save("samples/demo_detail.jpg", quality=90); print("ok")
