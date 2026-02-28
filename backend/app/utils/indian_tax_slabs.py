"""Indian Income Tax slab computation for FY 2025-26 (AY 2026-27).

Supports both New Regime and Old Regime.
"""

CESS_RATE = 0.04  # 4% Health & Education Cess
SECTION_87A_LIMIT_NEW = 1200000  # Rs 12 lakh — zero tax under new regime

NEW_REGIME_SLABS = [
    (400000, 0.00),
    (400000, 0.05),   # 4L - 8L
    (400000, 0.10),   # 8L - 12L
    (400000, 0.15),   # 12L - 16L
    (400000, 0.20),   # 16L - 20L
    (400000, 0.25),   # 20L - 24L
    (float("inf"), 0.30),  # 24L+
]

OLD_REGIME_SLABS = [
    (250000, 0.00),
    (250000, 0.05),   # 2.5L - 5L
    (500000, 0.20),   # 5L - 10L
    (float("inf"), 0.30),  # 10L+
]


def _slab_labels_new() -> list[str]:
    return ["0-4L", "4L-8L", "8L-12L", "12L-16L", "16L-20L", "20L-24L", "24L+"]


def _slab_labels_old() -> list[str]:
    return ["0-2.5L", "2.5L-5L", "5L-10L", "10L+"]


def compute_income_tax(taxable_income: float, regime: str = "new") -> dict:
    """Compute income tax with slab breakup.

    Returns:
        dict with estimated_tax, cess, total_tax_liability, slab_breakup
    """
    slabs = NEW_REGIME_SLABS if regime == "new" else OLD_REGIME_SLABS
    labels = _slab_labels_new() if regime == "new" else _slab_labels_old()

    if regime == "new" and taxable_income <= SECTION_87A_LIMIT_NEW:
        return {
            "estimated_tax": 0,
            "cess": 0,
            "total_tax_liability": 0,
            "slab_breakup": [
                {"range": label, "rate": rate * 100, "tax": 0}
                for label, (_, rate) in zip(labels, slabs)
            ],
            "note": "Section 87A rebate applied — zero tax for income up to Rs 12 lakh",
        }

    remaining = taxable_income
    total_tax = 0
    breakup = []

    for i, (slab_limit, rate) in enumerate(slabs):
        taxable_in_slab = min(remaining, slab_limit)
        tax_in_slab = taxable_in_slab * rate
        breakup.append({
            "range": labels[i],
            "rate": rate * 100,
            "tax": round(tax_in_slab, 2),
        })
        total_tax += tax_in_slab
        remaining -= taxable_in_slab
        if remaining <= 0:
            break

    cess = round(total_tax * CESS_RATE, 2)

    return {
        "estimated_tax": round(total_tax, 2),
        "cess": cess,
        "total_tax_liability": round(total_tax + cess, 2),
        "slab_breakup": breakup,
    }
