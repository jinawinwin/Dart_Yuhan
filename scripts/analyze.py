"""OpenDART 원자료에서 가이드 기반 주요 재무비율과 대시보드 JSON을 생성한다."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def number(value: str | None) -> float | None:
    return float(value) if value and value.strip() else None

def pct(numerator: float | None, denominator: float | None) -> float | None:
    return None if numerator is None or denominator in (None, 0) else numerator / denominator * 100

def average(current: float | None, previous: float | None) -> float | None:
    return None if current is None or previous is None else (current + previous) / 2

def main() -> None:
    source = ROOT / "data" / "financial_summary.csv"
    with source.open(encoding="utf-8-sig", newline="") as file:
        rows = []
        for raw in csv.DictReader(file):
            rows.append({key: int(value) if key in {"year", "period_order"} else value if key in {"report_code", "report_name"} else number(value) for key, value in raw.items()})
    rows.sort(key=lambda row: (row["year"], row["period_order"]))
    prior_by_report: dict[str, dict] = {}; ratios = []
    for row in rows:
        previous = prior_by_report.get(row["report_code"])
        average_assets = average(row["total_assets"], previous["total_assets"]) if previous else None
        average_equity = average(row["total_equity"], previous["total_equity"]) if previous else None
        average_receivables = average(row["accounts_receivable"], previous["accounts_receivable"]) if previous else None
        ratios.append({
            "year": row["year"], "report_code": row["report_code"], "report_name": row["report_name"], "period_order": row["period_order"],
            "revenue_growth_pct": pct(row["revenue"] - previous["revenue"], previous["revenue"]) if previous else None,
            "operating_margin_pct": pct(row["operating_income"], row["revenue"]), "net_margin_pct": pct(row["net_income"], row["revenue"]),
            "current_ratio_pct": pct(row["current_assets"], row["current_liabilities"]), "debt_to_equity_pct": pct(row["total_liabilities"], row["total_equity"]), "equity_ratio_pct": pct(row["total_equity"], row["total_assets"]),
            "roa_pct": pct(row["net_income"], average_assets), "roe_pct": pct(row["net_income"], average_equity), "cfo_conversion_pct": pct(row["operating_cash_flow"], row["net_income"]),
            "dso_days": average_receivables / row["revenue"] * 365 if average_receivables and row["revenue"] else None,
        })
        prior_by_report[row["report_code"]] = row
    if not ratios:
        raise RuntimeError("분석할 데이터가 없습니다. fetch_opendart.py를 먼저 실행하세요.")
    data = ROOT / "data"; data.mkdir(exist_ok=True)
    with (data / "ratios.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=ratios[0].keys()); writer.writeheader(); writer.writerows(ratios)
    annual = [row for row in rows if row["report_code"] == "11011"]
    annual_ratios = [row for row in ratios if row["report_code"] == "11011"]
    dashboard = {"company": "유한양행", "stock_code": "000100", "corp_code": "00145109", "basis": "연결 기준, 단위: 원. 분기·반기 손익과 현금흐름은 누적 기준일 수 있습니다.", "updated_at": datetime.now(timezone.utc).isoformat(), "source": {"provider": "OpenDART 단일회사 재무제표 API", "report_url": "https://dart.fss.or.kr/navi/searchNavi.do?naviCode=B001&naviCrpCik=00145109"}, "financials": rows, "ratios": ratios, "annual_financials": annual, "annual_ratios": annual_ratios}
    (data / "dashboard.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"분석 완료: {len(ratios)}개 기간")

if __name__ == "__main__":
    main()
