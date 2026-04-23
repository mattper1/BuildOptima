import pytest
from models.part import Part

# Minimal seed: 2-3 parts per category, enough to exercise the algorithm.
def _make_parts(db):
    parts = [
        # CPU
        Part(category="cpu", name="Budget CPU", brand="AMD", price=130.0,
             specs={"cores": 4, "base_clock_ghz": 3.8, "tdp_watts": 65, "architecture": "Zen 3"}),
        Part(category="cpu", name="Mid CPU", brand="AMD", price=250.0,
             specs={"cores": 6, "base_clock_ghz": 4.7, "tdp_watts": 105, "architecture": "Zen 4"}),
        Part(category="cpu", name="High CPU", brand="Intel", price=420.0,
             specs={"cores": 8, "base_clock_ghz": 5.0, "tdp_watts": 125, "architecture": "Raptor Lake"}),
        # GPU
        Part(category="gpu", name="Budget GPU", brand="AMD", price=200.0,
             specs={"vram_gb": 8, "tdp_watts": 100, "benchmark_score": 50, "tier": "budget"}),
        Part(category="gpu", name="Mid GPU", brand="Nvidia", price=500.0,
             specs={"vram_gb": 12, "tdp_watts": 200, "benchmark_score": 75, "tier": "mid"}),
        Part(category="gpu", name="High GPU", brand="Nvidia", price=800.0,
             specs={"vram_gb": 16, "tdp_watts": 285, "benchmark_score": 90, "tier": "high"}),
        # RAM
        Part(category="ram", name="16GB DDR4", brand="Corsair", price=50.0,
             specs={"size_gb": 16, "speed_mhz": 3200}),
        Part(category="ram", name="32GB DDR5", brand="Corsair", price=100.0,
             specs={"size_gb": 32, "speed_mhz": 6000}),
        # Storage
        Part(category="storage", name="500GB SATA", brand="Samsung", price=45.0,
             specs={"size_gb": 500, "read_speed_mbs": 560, "type": "sata"}),
        Part(category="storage", name="1TB NVMe", brand="WD", price=85.0,
             specs={"size_gb": 1000, "read_speed_mbs": 7300, "type": "nvme"}),
        # Motherboard
        Part(category="motherboard", name="Budget MOBO", brand="MSI", price=90.0,
             specs={"socket": "AM5", "form_factor": "ATX", "chipset": "B650"}),
        Part(category="motherboard", name="Mid MOBO", brand="ASUS", price=190.0,
             specs={"socket": "AM5", "form_factor": "ATX", "chipset": "X670"}),
        # PSU
        Part(category="psu", name="550W Bronze", brand="EVGA", price=60.0,
             specs={"wattage": 550, "efficiency_rating": "bronze"}),
        Part(category="psu", name="750W Gold", brand="Corsair", price=100.0,
             specs={"wattage": 750, "efficiency_rating": "gold"}),
        # Case
        Part(category="case", name="Budget Case", brand="NZXT", price=60.0,
             specs={"form_factor": "ATX", "max_gpu_length_mm": 360}),
        Part(category="case", name="Mid Case", brand="Fractal", price=110.0,
             specs={"form_factor": "ATX", "max_gpu_length_mm": 430}),
        # Cooler
        Part(category="cooler", name="Budget Air", brand="CM", price=30.0,
             specs={"type": "air", "tdp_rating_watts": 150, "noise_db": 36, "is_quiet": False}),
        Part(category="cooler", name="Quiet AIO", brand="NZXT", price=90.0,
             specs={"type": "aio", "tdp_rating_watts": 250, "noise_db": 22, "is_quiet": True}),
    ]
    for p in parts:
        db.add(p)
    db.commit()


@pytest.fixture
def seeded(client, db):
    _make_parts(db)
    return client


def test_optimize_returns_200_with_all_categories(seeded):
    res = seeded.post("/optimize", json={"budget": 1200, "use_case": "gaming"})
    assert res.status_code == 200
    body = res.json()
    assert body["use_case"] == "gaming"
    cats = {c["category"] for c in body["components"]}
    assert cats == {"cpu", "gpu", "ram", "storage", "motherboard", "psu", "case", "cooler"}


def test_optimize_total_never_exceeds_budget(seeded):
    for budget in [700, 1000, 1500, 2000]:
        res = seeded.post("/optimize", json={"budget": budget, "use_case": "gaming"})
        assert res.status_code == 200
        assert res.json()["total_price"] <= budget


def test_optimize_owns_gpu_excludes_gpu_category(seeded):
    res = seeded.post(
        "/optimize", json={"budget": 1000, "use_case": "gaming", "owns_gpu": True}
    )
    assert res.status_code == 200
    cats = {c["category"] for c in res.json()["components"]}
    assert "gpu" not in cats


def test_optimize_prefer_quiet_selects_quiet_cooler(seeded):
    res = seeded.post(
        "/optimize",
        json={"budget": 1500, "use_case": "general", "prefer_quiet_cooling": True},
    )
    assert res.status_code == 200
    cooler = next(c for c in res.json()["components"] if c["category"] == "cooler")
    assert cooler["specs"]["is_quiet"] is True


def test_optimize_future_proofing_flag_accepted(seeded):
    res = seeded.post(
        "/optimize",
        json={"budget": 1500, "use_case": "workstation", "future_proofing": True},
    )
    assert res.status_code == 200
    assert res.json()["total_price"] <= 1500


def test_optimize_budget_below_300_returns_422(seeded):
    res = seeded.post("/optimize", json={"budget": 100, "use_case": "gaming"})
    assert res.status_code == 422


def test_optimize_invalid_use_case_returns_422(seeded):
    res = seeded.post("/optimize", json={"budget": 1000, "use_case": "mining"})
    assert res.status_code == 422


def test_optimize_all_components_have_reason(seeded):
    res = seeded.post("/optimize", json={"budget": 1000, "use_case": "content_creation"})
    assert res.status_code == 200
    for comp in res.json()["components"]:
        assert len(comp["reason"]) > 10
