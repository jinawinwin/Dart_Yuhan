"""OpenDART 원자료를 연간·반기·분기 데이터로 정규화하고 대시보드 JSON을 생성한다."""
from __future__ import annotations
import csv, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FLOW=["revenue","operating_income","profit_before_tax","net_income","operating_cash_flow","investing_cash_flow","financing_cash_flow"]
BAL=["current_assets","noncurrent_assets","total_assets","current_liabilities","noncurrent_liabilities","total_liabilities","total_equity","cash_and_cash_equivalents","accounts_receivable","inventory"]

def number(v):
    return float(v) if v and str(v).strip() else None
def pct(a,b):
    return None if a is None or b in (None,0) else a/b*100
def avg(a,b):
    return None if a is None or b is None else (a+b)/2

def ratios(rows, default_days=365):
    out=[]; prev=None
    for r in rows:
        aa=avg(r.get("total_assets"),prev.get("total_assets") if prev else None)
        ae=avg(r.get("total_equity"),prev.get("total_equity") if prev else None)
        ar=avg(r.get("accounts_receivable"),prev.get("accounts_receivable") if prev else None)
        days=r.get("days_in_period") or default_days
        out.append({
            "year":r["year"],"period_label":r.get("period_label"),
            "revenue_growth_pct":pct(r["revenue"]-prev["revenue"],prev["revenue"]) if prev else None,
            "operating_margin_pct":pct(r["operating_income"],r["revenue"]),
            "net_margin_pct":pct(r["net_income"],r["revenue"]),
            "current_ratio_pct":pct(r["current_assets"],r["current_liabilities"]),
            "debt_to_equity_pct":pct(r["total_liabilities"],r["total_equity"]),
            "equity_ratio_pct":pct(r["total_equity"],r["total_assets"]),
            "roa_pct":pct(r["net_income"],aa),"roe_pct":pct(r["net_income"],ae),
            "cfo_conversion_pct":pct(r["operating_cash_flow"],r["net_income"]),
            "dso_days":ar/r["revenue"]*days if ar and r["revenue"] else None,
        })
        prev=r
    return out

def quarterly(rows):
    grouped={}
    for r in rows: grouped.setdefault(r["year"],{})[r["report_code"]]=r
    specs=[("11013",1,"Q1",90),("11012",2,"Q2",91),("11014",3,"Q3",92),("11011",4,"Q4",92)]
    out=[]
    for year in sorted(grouped):
        g=grouped[year]
        for i,(code,q,label,days) in enumerate(specs):
            cur=g.get(code); prev=g.get(specs[i-1][0]) if i else None
            if not cur or (i and not prev): continue
            r={"year":year,"period_order":q,"period_label":f"{year} {label}","quarter":q,"days_in_period":days}
            for k in FLOW: r[k]=cur[k] if not i else (cur[k]-prev[k] if cur[k] is not None and prev[k] is not None else None)
            for k in BAL: r[k]=cur[k]
            out.append(r)
    return out

def label(rows,kind):
    out=[]
    for r in sorted(rows,key=lambda x:(x["year"],x["period_order"])):
        x=dict(r); x["period_label"]=str(x["year"]) if kind=="annual" else f'{x["year"]} H1'; out.append(x)
    return out

def main():
    src=ROOT/"data"/"financial_summary.csv"
    with src.open(encoding="utf-8-sig",newline="") as f:
        rows=[]
        for raw in csv.DictReader(f):
            rows.append({k:int(v) if k in {"year","period_order"} else v if k in {"report_code","report_name"} else number(v) for k,v in raw.items()})
    rows.sort(key=lambda x:(x["year"],x["period_order"]))
    if len(rows)<2: raise RuntimeError("분석할 재무제표 기간이 2개 미만입니다.")
    annual=label([r for r in rows if r["report_code"]=="11011"],"annual")
    half=label([r for r in rows if r["report_code"]=="11012"],"half")
    quarter=quarterly(rows)
    raw_r=ratios(rows); annual_r=ratios(annual); half_r=ratios(half,181); quarter_r=ratios(quarter,91)
    data=ROOT/"data"; data.mkdir(exist_ok=True)
    with (data/"ratios.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=raw_r[0].keys()); w.writeheader(); w.writerows(raw_r)
    payload={
        "company":"유한양행","stock_code":"000100","corp_code":"00145109",
        "basis":"연결 기준. OpenDART 손익·현금흐름은 보고서 누적값이며, Quarterly는 누적값 간 차이로 단일분기 값을 환산합니다.",
        "updated_at":datetime.now(timezone.utc).isoformat(),
        "source":{"provider":"OpenDART 단일회사 재무제표 API","report_url":"https://dart.fss.or.kr/navi/searchNavi.do?naviCode=B001&naviCrpCik=00145109"},
        "financials":rows,"ratios":raw_r,
        "annual_financials":annual,"annual_ratios":annual_r,
        "half_year_financials":half,"half_year_ratios":half_r,
        "quarterly_financials":quarter,"quarterly_ratios":quarter_r,
    }
    (data/"dashboard.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"분석 완료: raw={len(rows)}, annual={len(annual)}, half={len(half)}, quarterly={len(quarter)}")
if __name__=="__main__": main()
