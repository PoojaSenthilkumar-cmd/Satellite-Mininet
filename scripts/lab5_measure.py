#!/usr/bin/env python3
"""
Lab 5: Automated metric measurement script
Measures RTT, jitter, packet loss, throughput for any profile
and saves results to a CSV file for comparison.
"""
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.log import setLogLevel
import time, re, csv, sys
 
PROFILES = {
    'terrestrial': {'delay':'5ms','jitter':'1ms','loss':0.1,'bw':100},
    'leo':  {'delay':'20ms','jitter':'10ms','loss':1.5,'bw':100},
    'geo':  {'delay':'270ms','jitter':'30ms','loss':2.0,'bw':20},
}
 
def parse_ping(output):
    """Extract RTT min/avg/max/mdev from ping output."""
    match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
    if match:
        return {
            'rtt_min': float(match.group(1)),
            'rtt_avg': float(match.group(2)),
            'rtt_max': float(match.group(3)),
            'jitter':  float(match.group(4))  # mdev = jitter
        }
    return {'rtt_min':0,'rtt_avg':0,'rtt_max':0,'jitter':0}
 
def parse_ping_loss(output):
    """Extract packet loss % from ping output."""
    match = re.search(r'([\d.]+)% packet loss', output)
    return float(match.group(1)) if match else 0.0
 
def parse_iperf(output):
    """Extract throughput in Mbps from iperf3 output."""
    match = re.search(r'([\d.]+)\s+Mbits/sec\s+receiver', output)
    return float(match.group(1)) if match else 0.0
 
def measure_profile(profile_name):
    p = PROFILES[profile_name]
    net = Mininet(controller=OVSController, link=TCLink)
    net.addController('c0')
    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')
    s1 = net.addSwitch('s1')
    net.addLink(h1, s1, bw=p['bw'], delay=p['delay'],
                loss=p['loss'], max_queue_size=500)
    net.addLink(h2, s1, bw=p['bw'], delay=p['delay'],
                loss=p['loss'], max_queue_size=500)
    net.start()
 
    print(f'\nMeasuring {profile_name} profile...')
 
    # Measure RTT and jitter (100 pings)
    ping_out = h1.cmd('ping -c 100 -i 0.1 10.0.0.2')
    rtt_data = parse_ping(ping_out)
    loss_pct = parse_ping_loss(ping_out)
 
    # Measure throughput (iperf3 for 20 seconds)
    h2.cmd('iperf3 -s -D')
    time.sleep(1)
    iperf_out = h1.cmd('iperf3 -c 10.0.0.2 -t 20')
    throughput = parse_iperf(iperf_out)
 
    results = {
        'profile':    profile_name,
        'delay_set':  p['delay'],
        'rtt_avg_ms': rtt_data['rtt_avg'],
        'jitter_ms':  rtt_data['jitter'],
        'loss_pct':   loss_pct,
        'throughput_mbps': throughput,
        'bw_set_mbps': p['bw']
    }
 
    print(f'  RTT avg:     {results["rtt_avg_ms"]:.1f} ms')
    print(f'  Jitter:      {results["jitter_ms"]:.1f} ms')
    print(f'  Packet loss: {results["loss_pct"]:.1f}%')
    print(f'  Throughput:  {results["throughput_mbps"]:.1f} Mbps')
 
    net.stop()
    return results
 
if __name__ == '__main__':
    setLogLevel('warning')
    all_results = []
    for profile in ['terrestrial', 'leo', 'geo']:
        r = measure_profile(profile)
        all_results.append(r)
        time.sleep(2)  # Wait between experiments
 
    # Save to CSV
    with open('satellite_comparison.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)
 
    print('\n\n=== FINAL COMPARISON TABLE ===')
    print(f'{"Profile":<16} {"RTT(ms)":>10} {"Jitter(ms)":>12} {"Loss%":>8} {"Throughput":>12}')
    print('-'*60)
    for r in all_results:
        print(f'{r["profile"]:<16} {r["rtt_avg_ms"]:>10.1f} {r["jitter_ms"]:>12.1f} {r["loss_pct"]:>8.1f} {r["throughput_mbps"]:>10.1f} Mbps')
    print('\nResults saved to satellite_comparison.csv')
