"""Market Basket Analysis — tự cài bằng pandas (không cần mlxtend).

Với mỗi cặp sản phẩm (A, B) xuất hiện cùng nhau trong ít nhất `min_pair_count`
hóa đơn:
  support(A,B)    = số hóa đơn chứa cả A và B / tổng số hóa đơn
  confidence(A->B)= support(A,B) / support(A)
  lift(A,B)       = confidence(A->B) / support(B)
lift > 1 nghĩa là A và B đi cùng nhau nhiều hơn ngẫu nhiên.
"""
from __future__ import annotations

from itertools import combinations

import pandas as pd


def basket_pairs(df: pd.DataFrame, min_pair_count: int = 10,
                 top_n: int = 30) -> pd.DataFrame:
    baskets = (df.groupby("invoice_id")["product_name"]
                 .agg(lambda s: sorted(set(s))))
    total = len(baskets)
    if total == 0:
        return pd.DataFrame()
    item_count: dict[str, int] = {}
    pair_count: dict[tuple[str, str], int] = {}
    for items in baskets:
        for it in items:
            item_count[it] = item_count.get(it, 0) + 1
        for a, b in combinations(items, 2):
            pair_count[(a, b)] = pair_count.get((a, b), 0) + 1

    rows = []
    for (a, b), cnt in pair_count.items():
        if cnt < min_pair_count:
            continue
        sup = cnt / total
        conf_ab = cnt / item_count[a]
        conf_ba = cnt / item_count[b]
        lift = conf_ab / (item_count[b] / total)
        rows.append({
            "product_a": a, "product_b": b, "pair_invoices": cnt,
            "support": round(sup, 4),
            "confidence_a_to_b": round(conf_ab, 4),
            "confidence_b_to_a": round(conf_ba, 4),
            "lift": round(lift, 3),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("lift", ascending=False).head(top_n).reset_index(drop=True)
