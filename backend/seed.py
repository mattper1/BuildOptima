"""
Run from backend/ with the venv active:
    python seed.py
Requires DATABASE_URL in .env or environment.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import models  # noqa: F401 — registers all models with Base
from db.database import Base, engine, SessionLocal
from models.part import Part

PARTS = [
    # ── CPU (8) ──────────────────────────────────────────────────────────────
    {"category": "cpu", "name": "AMD Ryzen 5 5600", "brand": "AMD", "price": 129.0,
     "specs": {"cores": 6, "base_clock_ghz": 3.5, "tdp_watts": 65, "architecture": "Zen 3"}},
    {"category": "cpu", "name": "AMD Ryzen 5 7600X", "brand": "AMD", "price": 229.0,
     "specs": {"cores": 6, "base_clock_ghz": 4.7, "tdp_watts": 105, "architecture": "Zen 4"}},
    {"category": "cpu", "name": "Intel Core i5-13600K", "brand": "Intel", "price": 269.0,
     "specs": {"cores": 14, "base_clock_ghz": 3.5, "tdp_watts": 125, "architecture": "Raptor Lake"}},
    {"category": "cpu", "name": "AMD Ryzen 7 7700X", "brand": "AMD", "price": 299.0,
     "specs": {"cores": 8, "base_clock_ghz": 4.5, "tdp_watts": 105, "architecture": "Zen 4"}},
    {"category": "cpu", "name": "Intel Core i7-13700K", "brand": "Intel", "price": 379.0,
     "specs": {"cores": 16, "base_clock_ghz": 3.4, "tdp_watts": 125, "architecture": "Raptor Lake"}},
    {"category": "cpu", "name": "AMD Ryzen 9 7900X", "brand": "AMD", "price": 429.0,
     "specs": {"cores": 12, "base_clock_ghz": 4.7, "tdp_watts": 170, "architecture": "Zen 4"}},
    {"category": "cpu", "name": "Intel Core i9-13900K", "brand": "Intel", "price": 549.0,
     "specs": {"cores": 24, "base_clock_ghz": 3.0, "tdp_watts": 125, "architecture": "Raptor Lake"}},
    {"category": "cpu", "name": "AMD Ryzen 9 7950X", "brand": "AMD", "price": 699.0,
     "specs": {"cores": 16, "base_clock_ghz": 4.5, "tdp_watts": 170, "architecture": "Zen 4"}},

    # ── GPU (8) ──────────────────────────────────────────────────────────────
    {"category": "gpu", "name": "AMD Radeon RX 6600", "brand": "AMD", "price": 199.0,
     "specs": {"vram_gb": 8, "tdp_watts": 132, "benchmark_score": 45, "tier": "budget"}},
    {"category": "gpu", "name": "NVIDIA GeForce RTX 3060", "brand": "NVIDIA", "price": 249.0,
     "specs": {"vram_gb": 12, "tdp_watts": 170, "benchmark_score": 55, "tier": "budget"}},
    {"category": "gpu", "name": "AMD Radeon RX 6700 XT", "brand": "AMD", "price": 299.0,
     "specs": {"vram_gb": 12, "tdp_watts": 230, "benchmark_score": 63, "tier": "mid"}},
    {"category": "gpu", "name": "NVIDIA GeForce RTX 4060", "brand": "NVIDIA", "price": 299.0,
     "specs": {"vram_gb": 8, "tdp_watts": 115, "benchmark_score": 65, "tier": "mid"}},
    {"category": "gpu", "name": "NVIDIA RTX 4070 SUPER", "brand": "NVIDIA", "price": 599.0,
     "specs": {"vram_gb": 12, "tdp_watts": 220, "benchmark_score": 82, "tier": "high"}},
    {"category": "gpu", "name": "AMD Radeon RX 7900 XT", "brand": "AMD", "price": 749.0,
     "specs": {"vram_gb": 20, "tdp_watts": 315, "benchmark_score": 88, "tier": "high"}},
    {"category": "gpu", "name": "NVIDIA RTX 4080 SUPER", "brand": "NVIDIA", "price": 999.0,
     "specs": {"vram_gb": 16, "tdp_watts": 320, "benchmark_score": 93, "tier": "flagship"}},
    {"category": "gpu", "name": "NVIDIA RTX 4090", "brand": "NVIDIA", "price": 1599.0,
     "specs": {"vram_gb": 24, "tdp_watts": 450, "benchmark_score": 100, "tier": "flagship"}},

    # ── RAM (6) ──────────────────────────────────────────────────────────────
    {"category": "ram", "name": "16GB Corsair Vengeance DDR4 3200", "brand": "Corsair", "price": 44.0,
     "specs": {"size_gb": 16, "speed_mhz": 3200}},
    {"category": "ram", "name": "32GB G.Skill Ripjaws DDR4 3600", "brand": "G.Skill", "price": 72.0,
     "specs": {"size_gb": 32, "speed_mhz": 3600}},
    {"category": "ram", "name": "32GB Corsair Vengeance DDR5 5200", "brand": "Corsair", "price": 89.0,
     "specs": {"size_gb": 32, "speed_mhz": 5200}},
    {"category": "ram", "name": "32GB G.Skill Trident Z5 DDR5 6000", "brand": "G.Skill", "price": 109.0,
     "specs": {"size_gb": 32, "speed_mhz": 6000}},
    {"category": "ram", "name": "64GB Corsair Dominator DDR5 5600", "brand": "Corsair", "price": 169.0,
     "specs": {"size_gb": 64, "speed_mhz": 5600}},
    {"category": "ram", "name": "64GB G.Skill Trident Z5 DDR5 6400", "brand": "G.Skill", "price": 219.0,
     "specs": {"size_gb": 64, "speed_mhz": 6400}},

    # ── Storage (6) ──────────────────────────────────────────────────────────
    {"category": "storage", "name": "500GB Samsung 870 EVO SATA", "brand": "Samsung", "price": 49.0,
     "specs": {"size_gb": 500, "read_speed_mbs": 560, "type": "sata"}},
    {"category": "storage", "name": "1TB Crucial MX500 SATA", "brand": "Crucial", "price": 69.0,
     "specs": {"size_gb": 1000, "read_speed_mbs": 560, "type": "sata"}},
    {"category": "storage", "name": "1TB Samsung 980 NVMe Gen3", "brand": "Samsung", "price": 79.0,
     "specs": {"size_gb": 1000, "read_speed_mbs": 3500, "type": "nvme"}},
    {"category": "storage", "name": "1TB WD Black SN850X NVMe Gen4", "brand": "WD", "price": 89.0,
     "specs": {"size_gb": 1000, "read_speed_mbs": 7300, "type": "nvme"}},
    {"category": "storage", "name": "2TB Samsung 990 Pro NVMe Gen4", "brand": "Samsung", "price": 149.0,
     "specs": {"size_gb": 2000, "read_speed_mbs": 7450, "type": "nvme"}},
    {"category": "storage", "name": "2TB WD Black SN850X NVMe Gen4", "brand": "WD", "price": 179.0,
     "specs": {"size_gb": 2000, "read_speed_mbs": 7300, "type": "nvme"}},

    # ── Motherboard (6) ──────────────────────────────────────────────────────
    {"category": "motherboard", "name": "MSI B450 Tomahawk Max II", "brand": "MSI", "price": 89.0,
     "specs": {"socket": "AM4", "form_factor": "ATX", "chipset": "B450"}},
    {"category": "motherboard", "name": "ASUS Prime B650M-A WiFi", "brand": "ASUS", "price": 139.0,
     "specs": {"socket": "AM5", "form_factor": "Micro-ATX", "chipset": "B650"}},
    {"category": "motherboard", "name": "MSI B650 Tomahawk WiFi", "brand": "MSI", "price": 189.0,
     "specs": {"socket": "AM5", "form_factor": "ATX", "chipset": "B650"}},
    {"category": "motherboard", "name": "ASUS ROG Strix B650-A Gaming", "brand": "ASUS", "price": 239.0,
     "specs": {"socket": "AM5", "form_factor": "ATX", "chipset": "B650"}},
    {"category": "motherboard", "name": "MSI MEG X670E ACE", "brand": "MSI", "price": 349.0,
     "specs": {"socket": "AM5", "form_factor": "ATX", "chipset": "X670E"}},
    {"category": "motherboard", "name": "ASUS ROG Crosshair X670E Hero", "brand": "ASUS", "price": 499.0,
     "specs": {"socket": "AM5", "form_factor": "ATX", "chipset": "X670E"}},

    # ── PSU (6) ──────────────────────────────────────────────────────────────
    {"category": "psu", "name": "EVGA 550W B5 80+ Bronze", "brand": "EVGA", "price": 59.0,
     "specs": {"wattage": 550, "efficiency_rating": "bronze"}},
    {"category": "psu", "name": "Corsair CV650 80+ Bronze", "brand": "Corsair", "price": 69.0,
     "specs": {"wattage": 650, "efficiency_rating": "bronze"}},
    {"category": "psu", "name": "Corsair RM750x 80+ Gold", "brand": "Corsair", "price": 99.0,
     "specs": {"wattage": 750, "efficiency_rating": "gold"}},
    {"category": "psu", "name": "Seasonic Focus GX-850 80+ Gold", "brand": "Seasonic", "price": 129.0,
     "specs": {"wattage": 850, "efficiency_rating": "gold"}},
    {"category": "psu", "name": "Corsair RM1000x 80+ Gold", "brand": "Corsair", "price": 169.0,
     "specs": {"wattage": 1000, "efficiency_rating": "gold"}},
    {"category": "psu", "name": "Seasonic Prime TX-1000 80+ Titanium", "brand": "Seasonic", "price": 239.0,
     "specs": {"wattage": 1000, "efficiency_rating": "platinum"}},

    # ── Case (6) ─────────────────────────────────────────────────────────────
    {"category": "case", "name": "Fractal Design Core 1000", "brand": "Fractal", "price": 49.0,
     "specs": {"form_factor": "Micro-ATX", "max_gpu_length_mm": 310}},
    {"category": "case", "name": "NZXT H5 Flow", "brand": "NZXT", "price": 79.0,
     "specs": {"form_factor": "ATX", "max_gpu_length_mm": 365}},
    {"category": "case", "name": "Fractal Design Meshify C", "brand": "Fractal", "price": 89.0,
     "specs": {"form_factor": "ATX", "max_gpu_length_mm": 315}},
    {"category": "case", "name": "Lian Li Lancool 216", "brand": "Lian Li", "price": 109.0,
     "specs": {"form_factor": "ATX", "max_gpu_length_mm": 400}},
    {"category": "case", "name": "Fractal Design North", "brand": "Fractal", "price": 139.0,
     "specs": {"form_factor": "ATX", "max_gpu_length_mm": 355}},
    {"category": "case", "name": "Lian Li O11 Dynamic EVO XL", "brand": "Lian Li", "price": 179.0,
     "specs": {"form_factor": "Full Tower", "max_gpu_length_mm": 446}},

    # ── Cooler (6) ───────────────────────────────────────────────────────────
    {"category": "cooler", "name": "Cooler Master Hyper 212", "brand": "Cooler Master", "price": 29.0,
     "specs": {"type": "air", "tdp_rating_watts": 150, "noise_db": 36, "is_quiet": False}},
    {"category": "cooler", "name": "Thermalright Peerless Assassin 120", "brand": "Thermalright", "price": 39.0,
     "specs": {"type": "air", "tdp_rating_watts": 250, "noise_db": 26, "is_quiet": True}},
    {"category": "cooler", "name": "be quiet! Dark Rock 4", "brand": "be quiet!", "price": 69.0,
     "specs": {"type": "air", "tdp_rating_watts": 200, "noise_db": 24, "is_quiet": True}},
    {"category": "cooler", "name": "NZXT Kraken 240 AIO", "brand": "NZXT", "price": 89.0,
     "specs": {"type": "aio", "tdp_rating_watts": 250, "noise_db": 33, "is_quiet": False}},
    {"category": "cooler", "name": "Corsair iCUE H150i Elite 360 AIO", "brand": "Corsair", "price": 159.0,
     "specs": {"type": "aio", "tdp_rating_watts": 350, "noise_db": 28, "is_quiet": True}},
    {"category": "cooler", "name": "NZXT Kraken 360 Elite AIO", "brand": "NZXT", "price": 229.0,
     "specs": {"type": "aio", "tdp_rating_watts": 400, "noise_db": 21, "is_quiet": True}},
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Part).count() > 0:
            print("Parts table already seeded — skipping.")
            return
        for row in PARTS:
            db.add(Part(**row))
        db.commit()
        print(f"Seeded {len(PARTS)} parts successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
