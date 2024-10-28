"""Chạy pipeline đầy đủ từ dòng lệnh.

Mặc định: sinh dữ liệu MÔ PHỎNG (seed 42) -> data/transactions_full.csv,
phân tích -> outputs/. Có thể phân tích file riêng:
    python run_analysis.py --input my_file.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from src.cleaning import load_file  # noqa: E402
from src.generate_data import generate_transactions  # noqa: E402
from src.report import run_full_analysis  # noqa: E402

BASE = Path(__file__).parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=None, help="CSV/Excel giao dịch (mặc định: sinh mô phỏng)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--churn-window", type=int, default=120)
    args = ap.parse_args()

    if args.input:
        raw = load_file(args.input)
        print(f"Đọc {len(raw)} dòng từ {args.input}")
    else:
        raw = generate_transactions(seed=args.seed)
        full = BASE / "data" / "transactions_full.csv"
        raw.to_csv(full, index=False)
        sample = raw.head(1000)
        sample.to_csv(BASE / "data" / "sample_transactions.csv", index=False)
        print(f"Dữ liệu MÔ PHỎNG: {len(raw)} dòng -> {full} (+ mẫu 1000 dòng)")

    result = run_full_analysis(raw, BASE / "outputs",
                               churn_window_days=args.churn_window)
    k = result["kpi"]
    print(f"KPI: doanh thu {k['revenue']:,.0f} đ | đơn {k['orders']} | "
          f"khách {k['customers']} | AOV {k['aov']:,.0f} đ | "
          f"repeat {k['repeat_rate_pct']:.1f}%")
    c = result["churn"]
    print("Churn metrics:", {n: {kk: round(vv, 3) for kk, vv in m.items()}
                             for n, m in c["metrics"].items()},
          "| best:", c["best_model"], f"| churn rate {c['churn_rate_pct']:.1f}%")
    print("Outputs ->", BASE / "outputs")


if __name__ == "__main__":
    main()
