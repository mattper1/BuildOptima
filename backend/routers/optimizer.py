from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.part import Part
from schemas.optimizer import OptimizeRequest, OptimizeResponse

router = APIRouter(prefix="/optimize", tags=["optimizer"])

WEIGHTS: dict[str, dict[str, float]] = {
    "gaming": {
        "cpu": 0.18, "gpu": 0.38, "ram": 0.10, "storage": 0.08,
        "motherboard": 0.10, "psu": 0.07, "case": 0.05, "cooler": 0.04,
    },
    "content_creation": {
        "cpu": 0.28, "gpu": 0.20, "ram": 0.18, "storage": 0.12,
        "motherboard": 0.08, "psu": 0.06, "case": 0.04, "cooler": 0.04,
    },
    "workstation": {
        "cpu": 0.32, "gpu": 0.10, "ram": 0.18, "storage": 0.16,
        "motherboard": 0.08, "psu": 0.07, "case": 0.05, "cooler": 0.04,
    },
    "general": {
        "cpu": 0.22, "gpu": 0.18, "ram": 0.16, "storage": 0.12,
        "motherboard": 0.12, "psu": 0.08, "case": 0.06, "cooler": 0.06,
    },
}


def _perf_scores(parts_by_cat: dict) -> dict[int, float]:
    scores: dict[int, float] = {}
    for parts in parts_by_cat.values():
        if not parts:
            continue
        sorted_p = sorted(parts, key=lambda p: p.price)
        lo, hi = sorted_p[0].price, sorted_p[-1].price
        span = hi - lo
        for p in sorted_p:
            scores[p.id] = 1.0 if span == 0 else 0.1 + 0.9 * (p.price - lo) / span
    return scores


def _generate_reason(category: str, part: Part, use_case: str, weight: float) -> str:
    priority = (
        "Top-weighted" if weight >= 0.25
        else "Mid-priority" if weight >= 0.12
        else "Supporting"
    )
    uc = use_case.replace("_", " ")
    s = part.specs
    templates = {
        "cpu": (
            f"{priority} for {uc} — {s.get('cores')} cores at "
            f"{s.get('base_clock_ghz')}GHz ({s.get('architecture')}) handles "
            "demanding workloads with headroom."
        ),
        "gpu": (
            f"{priority} for {uc} — {s.get('vram_gb')}GB VRAM drives smooth "
            "visuals at high resolution."
        ),
        "ram": (
            f"{priority} for {uc} — {s.get('size_gb')}GB at "
            f"{s.get('speed_mhz')}MHz keeps multitasking fluid."
        ),
        "storage": (
            f"{priority} for {uc} — {s.get('size_gb')}GB "
            f"{str(s.get('type', 'nvme')).upper()} at "
            f"{s.get('read_speed_mbs')} MB/s read speed minimises load times."
        ),
        "motherboard": (
            f"Reliable {s.get('form_factor')} board with {s.get('socket')} socket "
            f"and {s.get('chipset')} chipset — solid foundation for this build."
        ),
        "psu": (
            f"{s.get('wattage')}W "
            f"{str(s.get('efficiency_rating', '80+')).upper()} PSU provides "
            "stable power with headroom for upgrades."
        ),
        "case": (
            f"{s.get('form_factor')} case with {s.get('max_gpu_length_mm')}mm "
            "GPU clearance — good airflow and cable management."
        ),
        "cooler": (
            f"{'Quiet ' if s.get('is_quiet') else ''}"
            f"{str(s.get('type', 'air')).upper()} cooler rated for "
            f"{s.get('tdp_rating_watts')}W TDP keeps the CPU cool"
            f"{' and silent' if s.get('is_quiet') else ''}."
        ),
    }
    return templates.get(category, f"Best value {category} for this build.")


def run_optimizer(
    parts_by_cat: dict,
    budget: int,
    use_case: str,
    future_proofing: bool,
    owns_gpu: bool,
    prefer_quiet_cooling: bool,
) -> dict:
    weights = dict(WEIGHTS[use_case])
    active = list(weights.keys())

    # owns_gpu: remove GPU, redistribute its weight proportionally
    if owns_gpu and "gpu" in active:
        gpu_w = weights.pop("gpu")
        active.remove("gpu")
        remaining_w = sum(weights.values())
        for cat in active:
            weights[cat] += gpu_w * (weights[cat] / remaining_w)

    perf = _perf_scores({cat: parts_by_cat.get(cat, []) for cat in active})

    # future_proofing: boost perf scores of top-quartile parts
    if future_proofing:
        for cat in active:
            cat_parts = parts_by_cat.get(cat, [])
            if not cat_parts:
                continue
            prices = sorted(p.price for p in cat_parts)
            p75 = prices[int(len(prices) * 0.75)]
            for p in cat_parts:
                if p.price >= p75:
                    perf[p.id] = perf.get(p.id, 0.5) * 1.3

    target = {cat: budget * w for cat, w in weights.items()}
    selected: dict[str, Part] = {}

    for cat in active:
        parts = parts_by_cat.get(cat, [])
        if not parts:
            continue
        if cat == "cooler" and prefer_quiet_cooling:
            quiet = [p for p in parts if p.specs.get("is_quiet")]
            pool = quiet if quiet else parts
        else:
            pool = parts
        affordable = [p for p in pool if p.price <= target[cat]]
        selected[cat] = (
            max(affordable, key=lambda p: perf.get(p.id, 0))
            if affordable
            else min(pool, key=lambda p: p.price)
        )

    # Budget correction: if cheapest parts exceed budget, downgrade costliest
    total = sum(p.price for p in selected.values())
    for _ in range(50):
        if total <= budget:
            break
        worst = max(active, key=lambda c: selected[c].price if c in selected else 0)
        pool = parts_by_cat.get(worst, [])
        cheaper = sorted(
            [p for p in pool if p.price < selected[worst].price],
            key=lambda p: p.price,
            reverse=True,
        )
        if not cheaper:
            break
        total -= selected[worst].price - cheaper[0].price
        selected[worst] = cheaper[0]

    # Greedy upgrade pass: spend leftover budget on best incremental upgrades
    remaining = budget - sum(p.price for p in selected.values())
    improved = True
    while improved:
        improved = False
        best: tuple | None = None
        best_cost = float("inf")
        for cat in active:
            if cat not in selected:
                continue
            if cat == "cooler" and prefer_quiet_cooling:
                quiet = [p for p in parts_by_cat.get(cat, []) if p.specs.get("is_quiet")]
                pool = quiet if quiet else parts_by_cat.get(cat, [])
            else:
                pool = parts_by_cat.get(cat, [])
            upgrades = [
                p for p in pool
                if p.price > selected[cat].price
                and (p.price - selected[cat].price) <= remaining
            ]
            if upgrades:
                upgrade = min(upgrades, key=lambda p: p.price - selected[cat].price)
                cost = upgrade.price - selected[cat].price
                if cost < best_cost:
                    best_cost = cost
                    best = (cat, upgrade)
        if best:
            cat, new_part = best
            remaining -= new_part.price - selected[cat].price
            selected[cat] = new_part
            improved = True

    components = [
        {
            "category": cat,
            "name": part.name,
            "brand": part.brand,
            "price": part.price,
            "reason": _generate_reason(cat, part, use_case, weights[cat]),
            "specs": part.specs,
        }
        for cat, part in selected.items()
    ]

    return {
        "use_case": use_case,
        "budget": budget,
        "total_price": round(sum(p.price for p in selected.values()), 2),
        "components": components,
    }


@router.post("", response_model=OptimizeResponse)
def optimize(body: OptimizeRequest, db: Session = Depends(get_db)):
    all_parts = db.query(Part).all()
    by_cat: dict[str, list[Part]] = {}
    for p in all_parts:
        by_cat.setdefault(p.category, []).append(p)

    return run_optimizer(
        parts_by_cat=by_cat,
        budget=body.budget,
        use_case=body.use_case,
        future_proofing=body.future_proofing,
        owns_gpu=body.owns_gpu,
        prefer_quiet_cooling=body.prefer_quiet_cooling,
    )
