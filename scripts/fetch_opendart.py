"""유한양행 정기공시 재무정보를 OpenDART에서 수집한다."""
from __future__ import annotations
import argparse,csv,json,os
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
API="https://opendart.fss.or.kr/api"; CORP_CODE="00145109"
REPORTS={"11013":("1분기보고서",1),"11012":("반기보고서",2),"11014":("3분기보고서",3),"11011":("사업보고서",4)}
ACCOUNTS={
"revenue":({"매출액","수익(매출액)","영업수익"},{"ifrs-full_Revenue","ifrs-full_RevenueFromContractsWithCustomers","dart_OperatingRevenue"}),
"operating_income":({"영업이익","영업이익(손실)"},{"dart_OperatingIncomeLoss","ifrs-full_ProfitLossFromOperatingActivities"}),
"profit_before_tax":({"법인세비용차감전순이익","법인세비용차감전순이익(손실)"},{"ifrs-full_ProfitLossBeforeTax"}),
"net_income":({"당기순이익","당기순이익(손실)"},{"ifrs-full_ProfitLoss"}),
"current_assets":({"유동자산"},{"ifrs-full_CurrentAssets"}),"noncurrent_assets":({"비유동자산"},{"ifrs-full_NoncurrentAssets"}),
"total_assets":({"자산총계"},{"ifrs-full_Assets"}),"current_liabilities":({"유동부채"},{"ifrs-full_CurrentLiabilities"}),
"noncurrent_liabilities":({"비유동부채"},{"ifrs-full_NoncurrentLiabilities"}),"total_liabilities":({"부채총계"},{"ifrs-full_Liabilities"}),
"total_equity":({"자본총계"},{"ifrs-full_Equity"}),"operating_cash_flow":({"영업활동으로인한현금흐름","영업활동현금흐름"},{"ifrs-full_CashFlowsFromUsedInOperatingActivities"}),
"investing_cash_flow":({"투자활동으로인한현금흐름","투자활동현금흐름"},{"ifrs-full_CashFlowsFromUsedInInvestingActivities"}),
"financing_cash_flow":({"재무활동으로인한현금흐름","재무활동현금흐름"},{"ifrs-full_CashFlowsFromUsedInFinancingActivities"}),
"cash_and_cash_equivalents":({"현금및현금성자산"},{"ifrs-full_CashAndCashEquivalents"}),
"accounts_receivable":({"매출채권","매출채권및기타채권","매출채권및기타유동채권"},set()),
"inventory":({"재고자산"},{"ifrs-full_Inventories"})}
REQUIRED={"revenue","operating_income","net_income","current_assets","total_assets","current_liabilities","total_liabilities","total_equity","operating_cash_flow"}
FIELDS=["year","report_code","report_name","period_order",*ACCOUNTS]

def compact(s): return "".join(s.split()).replace("(손실)","")
def dotenv():
    p=ROOT/".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1); os.environ.setdefault(k.strip(),v.strip().strip('"'))
def request(endpoint,params):
    with urlopen(f"{API}/{endpoint}?{urlencode(params)}",timeout=60) as r: return json.load(r)
def integer(v):
    return None if not v or v.strip()=="-" else int(v.replace(",",""))
def normalise(year,code,items):
    name,order=REPORTS[code]; row={"year":year,"report_code":code,"report_name":name,"period_order":order,**{f:None for f in ACCOUNTS}}
    for field,(labels,ids) in ACCOUNTS.items():
        labels={compact(x) for x in labels}
        candidates=[x for x in items if compact(x.get("account_nm","")) in labels or x.get("account_id") in ids]
        chosen=candidates[0] if candidates else None
        if chosen: row[field]=integer(chosen.get("thstrm_amount"))
    missing=sorted(f for f in REQUIRED if row[f] is None)
    if missing: raise RuntimeError(f"{year}년 {name}: 필수 계정 누락 ({', '.join(missing)})")
    return row
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--api-key"); ap.add_argument("--start-year",type=int,default=2010); ap.add_argument("--skip-report-archives",action="store_true"); args=ap.parse_args()
    dotenv(); key=args.api_key or os.environ.get("DART_API_KEY")
    if not key: raise SystemExit("DART_API_KEY가 없습니다.")
    raw=ROOT/"data"/"raw"; raw.mkdir(parents=True,exist_ok=True); rows=[]
    for year in range(args.start_year,date.today().year+1):
        for code in REPORTS:
            response=request("fnlttSinglAcntAll.json",{"crtfc_key":key,"corp_code":CORP_CODE,"bsns_year":str(year),"reprt_code":code,"fs_div":"CFS"})
            if response.get("status")!="000": continue
            (raw/f"yuhan_{year}_{code}.json").write_text(json.dumps(response,ensure_ascii=False,indent=2),encoding="utf-8")
            try: rows.append(normalise(year,code,response["list"]))
            except RuntimeError as e: print(f"경고: {e}; 해당 기간은 제외합니다.")
    if len(rows)<2: raise RuntimeError("분석할 완전한 연결 재무제표가 2개 기간보다 적습니다.")
    rows.sort(key=lambda x:(x["year"],x["period_order"]))
    with (ROOT/"data"/"financial_summary.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    filings=request("list.json",{"crtfc_key":key,"corp_code":CORP_CODE,"bgn_de":f"{args.start_year}0101","end_de":date.today().strftime("%Y%m%d"),"pblntf_ty":"A","page_count":"100"})
    annual=[x for x in filings.get("list",[]) if x.get("report_nm","").startswith("사업보고서")]
    reports=ROOT/"reports"; reports.mkdir(exist_ok=True)
    (reports/"opendart_disclosures.json").write_text(json.dumps({"company":"유한양행","corp_code":CORP_CODE,"filings":annual},ensure_ascii=False,indent=2),encoding="utf-8")
    if not args.skip_report_archives:
        target=reports/"source"; target.mkdir(parents=True,exist_ok=True)
        for filing in annual:
            receipt=filing["rcept_no"]; archive=target/f"{receipt}.zip"
            if archive.exists(): continue
            try:
                with urlopen(f"{API}/document.xml?{urlencode({'crtfc_key':key,'rcept_no':receipt})}",timeout=120) as r: payload=r.read()
                if payload[:2]==b"PK": archive.write_bytes(payload)
                else: print(f"경고: {receipt} 원문 ZIP 다운로드 실패; 계속합니다.")
            except Exception as e: print(f"경고: {receipt} 원문 다운로드 실패 ({e}); 계속합니다.")
    print(f"수집 완료: {len(rows)}개 기간, 사업보고서 {len(annual)}건")
if __name__=="__main__": main()
