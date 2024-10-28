"""Sinh dữ liệu giao dịch bán lẻ MÔ PHỎNG (không phải dữ liệu thật).

Quy luật được cài sẵn để các phân tích có "đất" kiểm chứng:
- Mùa vụ: tháng 1 (Tết), 11, 12 cao; tháng 6-7 thấp.
- Xu hướng tăng trưởng nhẹ theo thời gian.
- 3 nhóm khách: VIP (ít, mua nhiều/thường xuyên), Thường, Thỉnh thoảng.
- Một nhóm khách "rời bỏ": ngừng mua hẳn sau một mốc ngẫu nhiên trong 2023-2024.
- Cặp sản phẩm bán kèm: khi giỏ có sản phẩm "neo" thì sản phẩm "kèm" xuất hiện
  với xác suất cao hơn hẳn ngẫu nhiên (để market basket tìm ra lift > 1).
- ~0,4% dòng lỗi được chèn cố ý (trùng dòng, số lượng <= 0, thiếu khách,
  đơn giá <= 0) để bước làm sạch có số liệu loại bỏ thật.

Cùng seed -> cùng dữ liệu (tái lập hoàn toàn bằng numpy RandomState).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CATEGORIES = {
    "Điện tử": [
        ("Tivi 43 inch", 6_900_000), ("Laptop văn phòng", 14_500_000),
        ("Tai nghe Bluetooth", 790_000), ("Loa Soundbar", 2_490_000),
        ("Điện thoại tầm trung", 5_490_000), ("Máy tính bảng", 4_290_000),
        ("Cáp HDMI 2m", 149_000), ("Chuột không dây", 349_000),
        ("Bàn phím cơ", 1_190_000), ("Ổ cứng SSD 512GB", 1_390_000),
    ],
    "Gia dụng": [
        ("Nồi chiên không dầu", 1_890_000), ("Máy xay sinh tố", 890_000),
        ("Nồi cơm điện", 1_290_000), ("Quạt điều hòa", 2_690_000),
        ("Máy lọc nước", 4_590_000), ("Ấm siêu tốc", 390_000),
        ("Bộ nồi inox 3 chiếc", 990_000), ("Chảo chống dính", 459_000),
    ],
    "Thời trang": [
        ("Áo sơ mi nam", 499_000), ("Váy đầm nữ", 690_000),
        ("Giày sneaker", 1_290_000), ("Túi xách nữ", 890_000),
        ("Áo khoác gió", 790_000), ("Quần jean", 590_000),
    ],
    "Mỹ phẩm": [
        ("Kem chống nắng", 329_000), ("Sữa rửa mặt", 189_000),
        ("Serum dưỡng da", 459_000), ("Son môi", 259_000),
        ("Dầu gội 650ml", 179_000), ("Mặt nạ giấy (hộp 10)", 149_000),
    ],
    "Thực phẩm": [
        ("Cà phê hạt 1kg", 289_000), ("Trà ô long 500g", 159_000),
        ("Hạt điều rang 500g", 219_000), ("Mật ong 500ml", 189_000),
        ("Gạo ST25 5kg", 139_000), ("Dầu ô liu 500ml", 169_000),
    ],
    "Thể thao": [
        ("Thảm yoga", 349_000), ("Tạ tay 5kg (cặp)", 459_000),
        ("Xe đạp thể thao", 5_900_000), ("Giày chạy bộ", 1_490_000),
        ("Balo leo núi", 690_000), ("Vợt cầu lông", 549_000),
    ],
}

# (sản phẩm neo, sản phẩm kèm, xác suất kèm khi có neo)
COMPANION_PAIRS = [
    ("Tivi 43 inch", "Loa Soundbar", 0.45),
    ("Tivi 43 inch", "Cáp HDMI 2m", 0.55),
    ("Laptop văn phòng", "Chuột không dây", 0.50),
    ("Laptop văn phòng", "Balo leo núi", 0.30),
    ("Nồi chiên không dầu", "Bộ nồi inox 3 chiếc", 0.28),
    ("Điện thoại tầm trung", "Tai nghe Bluetooth", 0.42),
]

BRANCHES = {  # chi nhánh -> khu vực
    "Chi nhánh Quận 1": "TP.HCM",
    "Chi nhánh Thủ Đức": "TP.HCM",
    "Chi nhánh Hà Nội": "Hà Nội",
    "Chi nhánh Đà Nẵng": "Đà Nẵng",
    "Chi nhánh Cần Thơ": "Cần Thơ",
}
MONTH_FACTOR = {1: 1.30, 2: 0.95, 3: 0.95, 4: 0.92, 5: 0.95, 6: 0.85,
                7: 0.85, 8: 0.95, 9: 1.05, 10: 1.10, 11: 1.30, 12: 1.45}

PRODUCTS = []  # (product_id, name, category, unit_price, unit_cost, popularity)
_pid = 0
for _cat, _items in CATEGORIES.items():
    for _name, _price in _items:
        _pid += 1
        PRODUCTS.append({
            "product_id": f"SP{_pid:03d}", "product_name": _name, "category": _cat,
            "unit_price": _price, "unit_cost": int(_price * 0.68),
        })
PRODUCT_BY_NAME = {p["product_name"]: p for p in PRODUCTS}
# Độ phổ biến: vài sản phẩm bán chạy hẳn (phân phối lệch)
_POP = np.array([1.0] * len(PRODUCTS))
for _i, _p in enumerate(PRODUCTS):
    if _p["unit_price"] < 400_000:
        _POP[_i] = 2.2
    elif _p["unit_price"] > 5_000_000:
        _POP[_i] = 0.45
_POP = _POP / _POP.sum()


def _make_customers(rng: np.random.RandomState, n: int = 1200) -> pd.DataFrame:
    kinds = rng.choice(["vip", "regular", "occasional", "churned", "one_time"],
                       size=n, p=[0.05, 0.50, 0.20, 0.10, 0.15])
    rows = []
    churn_start = pd.Timestamp("2023-06-01")
    churn_end = pd.Timestamp("2024-03-01")
    span_days = (pd.Timestamp("2024-12-31") - pd.Timestamp("2022-01-01")).days
    for i in range(n):
        kind = kinds[i]
        stop = None
        single_day = None
        if kind == "churned":
            stop = churn_start + pd.Timedelta(
                days=int(rng.randint(0, (churn_end - churn_start).days)))
        if kind == "one_time":
            single_day = pd.Timestamp("2022-01-01") + pd.Timedelta(
                days=int(rng.randint(0, span_days)))
        rows.append({"customer_id": f"KH{i + 1:04d}", "kind": kind,
                     "stop_date": stop, "single_day": single_day})
    return pd.DataFrame(rows)


def generate_transactions(seed: int = 42,
                          start: str = "2022-01-01",
                          end: str = "2024-12-31") -> pd.DataFrame:
    """Trả về DataFrame dòng giao dịch (mỗi dòng = 1 dòng hóa đơn)."""
    rng = np.random.RandomState(seed)
    customers = _make_customers(rng)
    # Tốc độ mua (số đơn kỳ vọng / tháng) theo nhóm
    rate = {"vip": 2.6, "regular": 0.85, "occasional": 0.28, "churned": 0.9}
    branch_names = list(BRANCHES)
    days = pd.date_range(start, end, freq="D")
    records = []
    inv_no = 0
    # Xác suất khách có đơn trong 1 ngày ~ rate/30, có trọng số mùa vụ xử lý ở tầng ngày
    daily_p = {c.customer_id: rate.get(c.kind, 0.0) / 30.0
               for c in customers.itertuples()}
    cust_ids = customers["customer_id"].to_numpy()
    cust_kind = dict(zip(customers.customer_id, customers.kind))
    cust_stop = {r.customer_id: r.stop_date for r in customers.itertuples()}
    one_time_day = {r.customer_id: r.single_day for r in customers.itertuples()
                    if r.kind == "one_time"}

    def emit_invoice(cid, day):
        nonlocal inv_no
        inv_no += 1
        invoice_id = f"HD{inv_no:06d}"
        branch = branch_names[rng.randint(len(branch_names))]
        channel = "Online" if rng.rand() < 0.38 else "Offline"
        promo = rng.rand() < 0.22
        discount = float(rng.choice([0.05, 0.10, 0.15])) if promo else 0.0
        n_items = int(rng.choice([1, 2, 3, 4], p=[0.45, 0.32, 0.16, 0.07]))
        chosen = rng.choice(len(PRODUCTS), size=n_items, replace=False, p=_POP)
        names = [PRODUCTS[i]["product_name"] for i in chosen]
        extra = []
        for anchor, comp, prob in COMPANION_PAIRS:
            if anchor in names and comp not in names and rng.rand() < prob:
                extra.append(comp)
        for name in names + extra:
            p = PRODUCT_BY_NAME[name]
            qty = int(rng.choice([1, 1, 1, 2, 3],
                                  p=[0.62, 0.15, 0.08, 0.10, 0.05]))
            if cust_kind[cid] == "vip":
                qty += int(rng.randint(0, 2))
            records.append({
                "invoice_id": invoice_id, "invoice_date": day,
                "customer_id": cid, "product_id": p["product_id"],
                "product_name": name, "category": p["category"],
                "quantity": qty, "unit_price": p["unit_price"],
                "unit_cost": p["unit_cost"], "discount_pct": discount,
                "branch": branch, "region": BRANCHES[branch],
                "channel": channel,
            })

    for day in days:
        factor = MONTH_FACTOR[day.month]
        trend = 1.0 + 0.12 * ((day - days[0]).days / max(len(days), 1))  # tăng trưởng nhẹ
        for cid in cust_ids:
            if cid in one_time_day:
                if one_time_day[cid] == day:
                    emit_invoice(cid, day)
                continue
            stop = cust_stop[cid]
            if stop is not None and day > stop:
                continue
            if rng.rand() < daily_p[cid] * factor * trend:
                emit_invoice(cid, day)
    df = pd.DataFrame(records)
    df = _inject_dirty_rows(df, rng)
    return df


def _inject_dirty_rows(df: pd.DataFrame, rng: np.random.RandomState) -> pd.DataFrame:
    """Chèn ~0,4% dòng lỗi cố ý để bước làm sạch có việc thật."""
    n_dirty = max(10, int(len(df) * 0.004))
    bad = df.sample(n=n_dirty, random_state=int(rng.randint(1 << 30))).copy()
    kinds = ["dup", "bad_qty", "no_customer", "bad_price"]
    out = [df]
    for i, (_, row) in enumerate(bad.iterrows()):
        r = row.copy()
        kind = kinds[i % len(kinds)]
        if kind == "dup":
            pass  # giữ nguyên -> dòng trùng
        elif kind == "bad_qty":
            r["quantity"] = 0 if i % 2 == 0 else -2
        elif kind == "no_customer":
            r["customer_id"] = None
        elif kind == "bad_price":
            r["unit_price"] = 0
        out.append(pd.DataFrame([r]))
    return pd.concat(out, ignore_index=True).sample(
        frac=1.0, random_state=7).reset_index(drop=True)


if __name__ == "__main__":
    d = generate_transactions()
    print(len(d), d["invoice_date"].min(), d["invoice_date"].max())
