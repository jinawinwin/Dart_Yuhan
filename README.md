# 유한양행 OpenDART 재무 분석 에이전트

<p align="center"><a href="https://jinawinwin.github.io/Dart_Yuhan/"><img src="assets/yuhan-ci-original.webp" alt="🔗 대시보드 바로가기" width="320"></a></p>

<p align="center"><strong>🔗 <a href="https://jinawinwin.github.io/Dart_Yuhan/">대시보드 바로가기</a></strong></p>

유한양행(종목코드 `000100`, DART 고유번호 `00145109`)의 정기공시 재무제표를 OpenDART API에서 수집하고, 핵심 재무비율과 **Annual / Half-year / Quarterly** 데이터를 분석해 GitHub Pages로 제공합니다.

## Dashboard 구성

- 상단: KPI와 연간 실적, 수익성, 최근 분기, 재무구조 figures
- 하단: **Annual / Half-year / Quarterly** 3개 독립 재무 데이터 테이블
- 우측 플로팅 창: **PDF 저장** + 기간 선택형 **Excel 다운로드**
- Quarterly: OpenDART 누적 공시값을 차분해 단일분기 값으로 환산
- 최하단: 국내 Peer Firms table

## 데이터 수집 및 자동화

- `scripts/fetch_opendart.py`: **2010년부터** 연간·1분기·반기·3분기 연결재무제표를 수집
- `scripts/analyze.py`: 연간·반기·분기 데이터와 핵심 비율을 계산해 `data/dashboard.json` 생성
- `.github/workflows/update-data.yml`: **매월 1일 09:30 KST** 자동 실행 + 수동 실행
- GitHub Actions Secret 이름: **`DART_API_KEY`**
- GitHub Pages: `https://jinawinwin.github.io/Dart_Yuhan/`

## OpenDART 인증키

1. OpenDART에서 인증키를 발급합니다.
2. GitHub **Settings → Secrets and variables → Actions**에서 `DART_API_KEY`를 생성하고 키를 저장합니다.
3. 키는 코드·README·Issue 등에 직접 기록하지 않습니다.

로컬 실행:

~~~text
DART_API_KEY=발급받은_40자리_인증키
~~~

## 국내 Peer Firms

| 회사 | 종목코드 | 주요 사업 | 비교 포인트 |
|---|---:|---|---|
| **종근당** | 185750 | 전문의약품·일반의약품·바이오 | 대형 국내 제약사 |
| **GC녹십자** | 006280 | 백신·혈액제제·의약품 | 제약·바이오 비교 |
| **한미약품** | 128940 | 개량신약·신약개발·해외사업 | R&D·신약 비교 |
| **대웅제약** | 069620 | 전문의약품·보툴리눔 톡신·신약 | R&D·수익성 비교 |
| **보령** | 003850 | 전문의약품·헬스케어 | 국내 상장 제약사 |
| **HK이노엔** | 195940 | 전문의약품·헬스드링크 | 종합 제약·헬스케어 |

## 해석 유의사항

연간 재무제표는 사업보고서 기준입니다. 반기·분기 손익과 현금흐름은 OpenDART 공시 누적값을 사용하며, 대시보드의 Quarterly는 누적값 간 차이로 단일분기 값을 환산합니다. 재무상태표는 보고기간 말 잔액입니다. 일부 과거 연도는 OpenDART API 제공 범위에 따라 누락될 수 있습니다. 본 프로젝트는 투자 권유가 아닙니다.

## GitHub 저장소 바로가기

저장소 오른쪽 **About → Website**에 `https://jinawinwin.github.io/Dart_Yuhan/`를 등록하면 저장소에서 대시보드로 바로 이동할 수 있습니다.
