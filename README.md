# 유한양행 OpenDART 재무 분석 에이전트

[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97-%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C%20%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-0969da?style=for-the-badge)](https://jinawinwin.github.io/Dart_Yuhan/)

유한양행(종목코드 `000100`, DART 고유번호 `00145109`)의 정기공시 재무제표를 OpenDART API에서 수집하고, 주요 재무비율을 계산해 GitHub Pages 대시보드로 공개합니다. 원문 사업보고서 ZIP, 공시 목록, API 응답 원문과 정규화된 분석 데이터를 함께 GitHub에 보관합니다.

## 구성

- `scripts/fetch_opendart.py`: 2020년부터 연간·1분기·반기·3분기 연결 재무제표와 사업보고서 원문 ZIP을 수집합니다.
- `scripts/analyze.py`: 첨부 가이드의 원칙에 따라 수익성·유동성·안정성·현금흐름·활동성 지표를 계산합니다. ROA·ROE·DSO는 평균 잔액을 사용합니다.
- `index.html`: API 키 없이 `data/dashboard.json`만 읽는 GitHub Pages 대시보드입니다.
- `.github/workflows/update-data.yml`: 매월 1일 09:30 KST 및 수동 실행 시 데이터를 갱신합니다.
- `.github/workflows/deploy-pages.yml`: `main` 변경 시 대시보드를 GitHub Pages로 배포합니다.

## OpenDART 인증키 설정

1. [OpenDART](https://opendart.fss.or.kr/)에서 인증키를 발급받습니다.
2. 로컬 실행은 `.env.example`을 `.env`로 복사한 뒤 인증키를 입력합니다.

```text
DART_API_KEY=발급받은_40자리_인증키
```

3. GitHub 저장소 **Settings → Secrets and variables → Actions → New repository secret**에서 이름을 `DART_API_KEY`로 만들고 같은 키를 넣습니다. 인증키는 코드, README, Issue에 절대 기록하지 마세요.

## 최초 실행과 GitHub 배포

```powershell
git init
git branch -M main
git remote add origin https://github.com/jinawinwin/Dart_Yuhan.git
python scripts/fetch_opendart.py --start-year 2020
python scripts/analyze.py
git add .
git commit -m "feat: add Yuhan OpenDART dashboard"
git push -u origin main
```

1. 저장소 **Settings → Pages → Build and deployment → Source**에서 **GitHub Actions**를 선택합니다.
2. **Actions → Update OpenDART financial data → Run workflow**로 최초 수집을 실행합니다.
3. 대시보드 주소 `https://jinawinwin.github.io/Dart_Yuhan/`를 저장소 우측 **About → ⚙ → Website**에 등록합니다. 이 주소는 README 최상단 배지에도 연결되어 있습니다.

## 산출 지표와 해석

영업이익률, 순이익률, 유동비율, 부채비율, 자기자본비율, ROA, ROE, CFO 전환율, DSO를 제공합니다. FCF·ROIC는 CAPEX와 투자자본 정의를 주석에서 일관되게 검증하기 전에는 계산하지 않습니다. 순이익은 처분이익 등 비경상 항목의 영향을 받을 수 있으므로 영업이익률·CFO 전환율·운전자본 변화를 함께 확인해야 합니다. 이 프로젝트는 투자 권유가 아닙니다.
