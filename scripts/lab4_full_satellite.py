#!/usr/bin/env python3
"""
Lab 4: Complete satellite channel simulation
Combines findings from all 4 papers into one experiment.
Includes GEO mode and LEO mode selectable at runtime.
"""
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
import sys, time
 
# ─── Satellite profiles based on paper findings ──────────────────────
PROFILES = {
    'terrestrial': {
        'delay': '5ms', 'jitter': '1ms', 'loss': 0.1,
        'bw_down': 100, 'bw_up': 100,
        'description': 'Terrestrial broadband (baseline)'
    },
    'leo': {
        'delay': '20ms', 'jitter': '10ms', 'loss': 1.5,
        'bw_down': 100, 'bw_up': 50,
        'description': 'LEO Satellite - Starlink-like (Paper 2: 20-40ms RTT)'
    },
    'geo': {
        'delay': '270ms', 'jitter': '30ms', 'loss': 2.0,
        'bw_down': 20, 'bw_up': 5,
        'description': 'GEO Satellite (Paper 2: 270ms one-way, Paper 3: asymmetric)'
    },
    'geo_worst': {
        'delay': '300ms', 'jitter': '50ms', 'loss': 5.0,
        'bw_down': 10, 'bw_up': 2,
        'description': 'GEO worst case: rain fade + shadowing (Paper 3: Shadowed-Rician)'
    }
}
 
def full_satellite_sim(profile_name='geo'):
    p = PROFILES[profile_name]
    net = Mininet(controller=OVSController, link=TCLink)
    net.addController('c0')
 
    h1 = net.addHost('h1', ip='10.0.0.1')  # Gateway / ground station
    h2 = net.addHost('h2', ip='10.0.0.2')  # End user
    h3 = net.addHost('h3', ip='10.0.0.3')  # Second user (to test congestion)
    s1 = net.addSwitch('s1')
 
    # Downlink: more bandwidth (satellite to user)
    net.addLink(h1, s1, bw=p['bw_down'], delay=p['delay'],
                loss=p['loss'], max_queue_size=100)
    # Uplink h2: constrained (user to satellite) — Paper 3 finding
    net.addLink(h2, s1, bw=p['bw_up'], delay=p['delay'],
                loss=p['loss'], max_queue_size=100)
    # Second user
    net.addLink(h3, s1, bw=p['bw_up'], delay=p['delay'],
                loss=p['loss'], max_queue_size=100)
 
    net.start()
 
    print('\n' + '='*70)
    print(f'SATELLITE SIMULATION: {profile_name.upper()}')
    print(f'Profile: {p["description"]}')
    print(f'Delay (one-way): {p["delay"]}  → RTT ~{int(p["delay"][:-2])*2}ms')
    print(f'Jitter:          {p["jitter"]}')
    print(f'Packet loss:     {p["loss"]}%')
    print(f'Bandwidth:       {p["bw_down"]} Mbps down / {p["bw_up"]} Mbps up')
    print('='*70)
 
    print('\n[1] Running comprehensive tests...')
 
    # Test 1: RTT
    print('\n--- RTT (50 pings) ---')
    print(h1.cmd('ping -c 50 -i 0.2 10.0.0.2'))
 
    # Test 2: Throughput
    print('\n--- Throughput test ---')
    h2.cmd('iperf3 -s -D')
    time.sleep(1)
    print(h1.cmd('iperf3 -c 10.0.0.2 -t 20 -i 5'))
 
    # Test 3: Multi-user congestion
    print('\n--- Multi-user test (h1 and h3 both sending) ---')
    h2.cmd('iperf3 -s -p 5202 -D')
    time.sleep(1)
    h3.cmd('iperf3 -c 10.0.0.2 -p 5202 -t 15 -i 5 &')
    print(h1.cmd('iperf3 -c 10.0.0.2 -t 15 -i 5'))
 
    # Test 4: TCP retransmission check
    print('\n--- TCP retransmission check (Paper 3 finding) ---')
    print('Retransmission statistics:')
    print(h1.cmd('ss -tin | grep retrans | head -5'))
 
    print('\nEntering CLI for manual testing.')
    print('Try: h1 ping -c 100 10.0.0.2')
    print('     h2 iperf3 -s &')
    print('     h1 iperf3 -c 10.0.0.2 -t 30')
    CLI(net)
    net.stop()
 
if __name__ == '__main__':
    setLogLevel('warning')
    # Change 'geo' to 'leo', 'terrestrial', or 'geo_worst'
    profile = sys.argv[1] if len(sys.argv) > 1 else 'geo'
    full_satellite_sim(profile)
    
    
# Run with GEO profile (default)
#sudo python3 lab4_full_satellite.py geo
 
# Run with LEO profile
#sudo python3 lab4_full_satellite.py leo
 
# Run worst-case GEO (rain fade scenario from Paper 3)
#sudo python3 lab4_full_satellite.py geo_worst
 
# Run terrestrial for comparison
#sudo python3 lab4_full_satellite.py terrestrial
