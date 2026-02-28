from datetime import date
from fastapi import APIRouter, Query

from app.dependencies import TenantId, DB
from app.schemas.tax import GSTSummaryResponse, ITEstimateResponse, ITSlabBreakup
from app.services.tax_service import compute_gst_summary, compute_income_tax_estimate

router = APIRouter()


@router.get("/gst/summary", response_model=list[GSTSummaryResponse])
async def get_gst_summary(
    period_type: str = Query("monthly", pattern="^(monthly|quarterly)$"),
    year: int = Query(2025),
    tenant_id: TenantId = None,
    db: DB = None,
):
    """Get GST summaries for a financial year. Recomputes if stale."""
    summaries = []

    if period_type == "monthly":
        for month in range(4, 16):
            actual_month = month if month <= 12 else month - 12
            actual_year = year if month <= 12 else year + 1
            start = date(actual_year, actual_month, 1)
            if actual_month == 12:
                end = date(actual_year + 1, 1, 1)
            else:
                end = date(actual_year, actual_month + 1, 1)
            from datetime import timedelta
            end = end - timedelta(days=1)

            summary = await compute_gst_summary(db, tenant_id, start, end, "monthly")
            summaries.append(summary)
    else:
        quarters = [
            (date(year, 4, 1), date(year, 6, 30)),
            (date(year, 7, 1), date(year, 9, 30)),
            (date(year, 10, 1), date(year, 12, 31)),
            (date(year + 1, 1, 1), date(year + 1, 3, 31)),
        ]
        for start, end in quarters:
            summary = await compute_gst_summary(db, tenant_id, start, end, "quarterly")
            summaries.append(summary)

    return [
        GSTSummaryResponse(
            id=str(s.id), period_start=s.period_start, period_end=s.period_end,
            period_type=s.period_type,
            output_cgst=float(s.output_cgst), output_sgst=float(s.output_sgst),
            output_igst=float(s.output_igst), output_cess=float(s.output_cess),
            input_cgst=float(s.input_cgst), input_sgst=float(s.input_sgst),
            input_igst=float(s.input_igst), input_cess=float(s.input_cess),
            net_liability=float(s.net_liability), is_stale=s.is_stale,
            computed_at=s.computed_at,
        )
        for s in summaries
    ]


@router.get("/income/estimate", response_model=ITEstimateResponse)
async def get_income_tax_estimate(
    fy: str = Query("2025-26", pattern=r"^\d{4}-\d{2}$"),
    tenant_id: TenantId = None,
    db: DB = None,
):
    estimate = await compute_income_tax_estimate(db, tenant_id, fy)

    return ITEstimateResponse(
        id=str(estimate.id), fy=estimate.fy,
        total_revenue=float(estimate.total_revenue),
        total_expenses=float(estimate.total_expenses),
        gross_profit=float(estimate.gross_profit),
        tax_regime=estimate.tax_regime,
        taxable_income=float(estimate.taxable_income),
        estimated_tax=float(estimate.estimated_tax),
        cess=float(estimate.cess),
        total_tax_liability=float(estimate.total_tax_liability),
        slab_breakup=[ITSlabBreakup(**s) for s in (estimate.slab_breakup or [])],
        assumptions=estimate.assumptions or {},
        is_stale=estimate.is_stale,
        computed_at=estimate.computed_at,
    )
