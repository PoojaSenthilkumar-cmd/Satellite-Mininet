#!/bin/bash
# ─────────────────────────────────────────────
# safe_start.sh — Run BEFORE every Mininet lab
# Cleans up any leftover virtual interfaces,
# OVS bridges, and processes from previous runs
# ─────────────────────────────────────────────

echo "=== Cleaning up Mininet leftovers ==="

# Remove all leftover Mininet network state
sudo mn -c 2>/dev/null

# Kill any orphaned iperf3 servers
sudo pkill -f iperf3 2>/dev/null

# Kill any orphaned Mininet processes
sudo pkill -f mininet 2>/dev/null

# Reset Open vSwitch (the virtual switch engine)
sudo service openvswitch-switch restart 2>/dev/null

echo "=== Cleanup done. Safe to start your lab. ==="
echo ""
echo "Active network interfaces (should be clean):"
ip link show | grep -E "^[0-9]+:" | awk '{print $2}'
