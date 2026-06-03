#!/usr/bin/env python3
"""
Lab 1: Terrestrial network baseline
Creates: 2 hosts connected by a switch with realistic terrestrial link parameters
Based on: Paper 3 (Wang et al.) terrestrial channel characteristics
"""
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
from time import sleep
import re

def parse_ping(output):
    """Extract RTT statistics (min/avg/max/mdev) from ping output."""
    match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
    if match:
        return {
            'rtt_min': float(match.group(1)),
            'rtt_avg': float(match.group(2)),
            'rtt_max': float(match.group(3)),
            'jitter': float(match.group(4))
        }
    return {'rtt_min': 0, 'rtt_avg': 0, 'rtt_max': 0, 'jitter': 0}

def parse_ping_loss(output):
    """Extract packet loss percentage from ping output."""
    match = re.search(r'([\d.]+)% packet loss', output)
    return float(match.group(1)) if match else 0.0

def parse_iperf3(output):
    """Extract throughput in Mbps from iperf3 output."""
    # Look for the final result line with receiver throughput
    match = re.search(r'(\d+(?:\.\d+)?)\s+Mbits/sec\s+receiver', output)
    if match:
        return float(match.group(1))
    return 0.0

def terrestrial_network():
    # Create network object — TCLink lets us set link parameters
    net = Mininet(controller=OVSController, link=TCLink)
 
    # Add a controller (the 'brain' managing the switch)
    net.addController('c0')
 
    # Add two hosts (virtual computers)
    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')
 
    # Add a switch (connects the two hosts)
    s1 = net.addSwitch('s1')
 
    # Connect hosts to switch with TERRESTRIAL link parameters:
    # bw=100  → 100 Mbps bandwidth (typical broadband)
    # delay='5ms' → 5 ms one-way delay (RTT will be ~10ms)
    # loss=0.1 → 0.1% packet loss (realistic terrestrial)
    # jitter='1ms' → 1 ms jitter (stable terrestrial)
    net.addLink(h1, s1, bw=100, delay='5ms', loss=0.1,
                max_queue_size=1000)
    net.addLink(h2, s1, bw=100, delay='5ms', loss=0.1,
                max_queue_size=1000)
 
    # Start the network
    net.start()

    #small pause to avoid start up spikes
    sleep(2)
 
    print('\n' + '-'*60)
    print('TERRESTRIAL NETWORK STARTED')
    print('h1 IP: 10.0.0.1    h2 IP: 10.0.0.2')
    print('Link: 100 Mbps, 5ms one-way delay, 0.1% loss')
    print('Expected RTT: ~20 ms')
    print('-'*60)
 
    # Run automatic tests
    print('\n--- TEST 1: Basic connectivity (ping 10 packets) ---')
    demoResult = h1.cmd('ping -c 10 10.0.0.2')
    print(demoResult)
 
    print('\n--- TEST 2: RTT measurement (50 pings for statistics) ---')
    ping_result = h1.cmd('ping -c 50 -i 0.2 10.0.0.2')
    print(ping_result)
    
    # Parse and display ping statistics
    ping_stats = parse_ping(ping_result)
    packet_loss = parse_ping_loss(ping_result)
    print('\n--- PING STATISTICS SUMMARY ---')
    print(f'RTT Min:     {ping_stats["rtt_min"]:.2f} ms')
    print(f'RTT Average: {ping_stats["rtt_avg"]:.2f} ms')
    print(f'RTT Max:     {ping_stats["rtt_max"]:.2f} ms')
    print(f'Jitter:      {ping_stats["jitter"]:.2f} ms')
    print(f'Packet Loss: {packet_loss:.2f}%')
    
    # TEST 3: Throughput measurement using iperf3
    print('\n--- TEST 3: Throughput measurement (iperf3 for 20 seconds) ---')
    print('Starting iperf3 server on h2...')
    h2.cmd('iperf3 -s -D')  # Start server in background (-D = daemon)
    sleep(1)  # Wait for server to start
    
    print('Running throughput test from h1 to h2...')
    iperf_result = h1.cmd('iperf3 -c 10.0.0.2 -t 20 -i 5')
    print(iperf_result)
    
    # Parse and display throughput
    throughput = parse_iperf3(iperf_result)
    print('\n--- THROUGHPUT SUMMARY ---')
    print(f'Measured Throughput: {throughput:.2f} Mbps')
    print(f'Expected Maximum:    100 Mbps')
    print(f'Utilization:         {(throughput/100)*100:.1f}%')
 
    # Open interactive CLI so you can run more commands manually
    print('\n' + '='*60)
    print('Entering CLI. Type your own commands. Type exit to quit.')
    print('='*60)
    CLI(net)
 
    # Clean up
    net.stop()
 
if __name__ == '__main__':
    setLogLevel('warning')
    terrestrial_network() 
