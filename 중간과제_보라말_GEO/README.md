# 보라말 GEO 구독 서비스: AI가 읽어야, 선택됩니다

영어음성학응용 중간고사 프로젝트(사업 구상). 팀 보라말: 이소운, 이시운.

식품 회사의 영양성분·원재료·알레르기 정보는 대부분 자사몰 상세페이지의 **이미지 안**에 있어 AI가 읽지 못합니다. 보라말은 공공 식품영양성분 DB와 AI 이미지 분석으로 이 정보를 꺼내고, GEO(생성형 AI 최적화) 방식으로 가공해 **AI 전용 공식 제품정보 사이트**로 발행하고 매달 관리하는 구독 서비스를 만듭니다. 매일유업 공식 제품 가이드(productguide.maeil.com)를 먼저 만들어 납품한 방식을 다른 회사로 넓히는 사업입니다.

## 제출물

| 번호 | 파일 | 내용 |
|---|---|---|
| 1 | [deliverables/1_모션그래픽_보라말_GEO.mp4](deliverables/1_모션그래픽_보라말_GEO.mp4) | 모션그래픽, 1분 11초, 1920×1080 30fps |
| 2 | [deliverables/2_AI영화_보라말_GEO_읽히지않는제품.mp4](deliverables/2_AI영화_보라말_GEO_읽히지않는제품.mp4) | AI 영화 《읽히지 않는 제품》, 1분 10초, 1920×1080 30fps |
| 3 | [deliverables/3_사업계획서_보라말_GEO.pdf](deliverables/3_사업계획서_보라말_GEO.pdf) | 사업계획서 14쪽(이유·내용·계획·절차, 제작 과정 포함) |

## 사업 요약

- **문제:** 보라말이 점검한 식품 회사 17곳의 제품 페이지 51개 중 영양성분표가 본문 글자로 있는 곳은 0개
- **해법:** 공공 DB 수집 → AI 이미지 분석 → GEO 가공 → AI 전용 사이트 발행·매달 측정
- **근거:** 매일유업 공식 제품 가이드를 AI에 넣었을 때 제품 사실 정답률 21% → 99%(보라말 시험, 최대치)
- **수익:** 무료 AI 성적표 → 90일 시범 2,400만 원 → 월 구독 450만 / 850만 원 / 별도 협의(VAT 별도)
- **계획:** 3년 차(2029) 고객 14곳, 매출 14.4억 원, 영업이익 7.4억 원(재무 모델, 가정 포함)

## 폴더 구성

```
deliverables/   제출물 3종
prototype/      작동하는 GEO 파이프라인 시제품(가상 제품으로 시연)
motion/         모션그래픽 소스(HTML Canvas, 결정적 렌더러)
film/           AI 영화: 장면 프롬프트, 첫 프레임, 기준 인물 이미지
report/         사업계획서 HTML 원본과 그림
script/         나레이션 대본
audio/          나레이션 줄별 길이, 믹스
tools/          렌더·나레이션·믹스·영화 편집 스크립트
```

## 시제품 실행

```bash
cd prototype
python3 make_sample_image.py                         # 가상 제품 상세 이미지 생성
python3 boramal_geo.py extract samples/demo_detail.jpg   # AI 이미지 분석(claude CLI 필요)
python3 boramal_geo.py public "두유"                  # 공공 DB(DATA_GO_KR_KEY 없으면 fixtures 사용)
python3 boramal_geo.py build                          # 대조 + GEO 가공 + site/ 생성
```

결과 `prototype/site/`: 제품 페이지(JSON-LD Product·FAQPage), index, sitemap.xml, robots.txt(검색용 AI 봇 허용), llms.txt, 대조 결과(qa_report.json).

## 영상 다시 만들기

```bash
python3 tools/vo.py motion && python3 tools/vo.py film          # ElevenLabs 나레이션(.env 의 ELEVENLABS_API_KEY)
python3 tools/mix.py motion && python3 tools/mix.py film        # 음악·덕킹·효과음, -14 LUFS
node tools/render.mjs video --audio audio/motion_mix.wav --out deliverables/1_모션그래픽_보라말_GEO.mp4
python3 tools/film_edit.py                                       # AI 영화 편집(클립 + 자막 + 대화 UI + 엔딩)
```

AI 영화 생성(Higgsfield): 종이접기 질감. 실사 첫 프레임(GPT Image 2.5)을 같은 구도의 종이접기 디오라마로 다시 그리고(`film/origami/frames.sh`), Kling 3.0 std 이미지→영상 10초 × 7(Origami 영상 변환 프리셋도 시험했으나 8fps로 끊겨 교체). 편집은 `python3 tools/film_edit.py --origami`. 처음 만든 실사풍 버전은 로컬 `film/alt/`에 보관. 프롬프트는 `film/keyframes/prompts.tsv`, `film/motion.tsv`, `film/motion_real.tsv`, `film/regen_real.sh`. 보라말 형제 장면은 본인 사진을 참조해 다시 만들었고(옷만 보라 계열로 변경), 사용 크레딧은 실사풍 버전 약 272, 종이접기 버전 약 302(Origami 프리셋 시험 160 포함)입니다.

## 출처와 라이선스

- 소비자 조사: 오픈서베이 'AI 검색 트렌드 리포트 2026', 한국경제 2026-01-28
- 업계 동향: 회사 발표·보도(2026-03~09), 보고서 14쪽에 정리
- 공공 데이터: 식품의약품안전처 식품영양성분 DB(공공데이터포털 Open API)
- 음악: Mixkit Free License('Digital Clouds', 'A New Life'), 폰트: Pretendard(OFL), 나레이션: ElevenLabs

## 정직성 메모

시험 수치는 자료를 AI에 직접 넣은 조건의 결과이며 실제 AI 검색 답의 보장값이 아닙니다. 재무 수치는 가정이 포함된 모델 값입니다. 영상 속 인물(보라말 형제 제외)·제품·대화는 연출이고, 시제품의 제품은 가상 제품입니다.
