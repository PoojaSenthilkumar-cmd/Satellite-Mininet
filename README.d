# Satellite Network Simulation with Mininet

Simulating satellite vs terrestrial network conditions based on 4 IEEE research papers.

## Papers Referenced
- P1: Cai et al. (2023) — Satellite Traffic Prediction, LSTM + GAN
- P2: Azari et al. (2022) — NTN Evolution 5G to 6G Survey
- P3: Wang et al. (2020) — Satellite-Terrestrial Convergence Survey
- P4: Wang et al. (2025) — SAGS Integration Architecture

## Labs
| File | What it does |
|------|-------------|
| lab1_terrestrial.py | Terrestrial baseline (RTT ~10ms) |
| lab2_geo_satellite.py | GEO satellite conditions (RTT ~540ms) |
| lab3_leo_satellite.py | LEO satellite + handover simulation |
| lab4_full_satellite.py | All profiles combined |
| lab5_measure.py | Automated measurements → CSV output |

## How to run
```bash
./safe_start.sh           # Always run first
sudo python3 scripts/lab1_terrestrial.py
```

## Requirements
- Ubuntu 20.04 / 22.04
- Mininet: `sudo apt-get install mininet`
- Tools: `sudo apt-get install iperf3 iproute2`
