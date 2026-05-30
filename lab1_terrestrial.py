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
 
    print('\n' + '='*60)
    print('TERRESTRIAL NETWORK STARTED')
    print('h1 IP: 10.0.0.1    h2 IP: 10.0.0.2')
    print('Link: 100 Mbps, 5ms one-way delay, 0.1% loss')
    print('Expected RTT: ~10 ms (like a local broadband connection)')
    print('='*60)
 
    # Run automatic tests
    print('\n--- TEST 1: Basic connectivity (ping 10 packets) ---')
    h1.cmd('ping -c 10 10.0.0.2')
 
    print('\n--- TEST 2: RTT measurement (50 pings for statistics) ---')
    result = h1.cmd('ping -c 50 -i 0.2 10.0.0.2')
    print(result)
 
    # Open interactive CLI so you can run more commands manually
    print('\nEntering CLI. Type your own commands. Type exit to quit.')
    CLI(net)
 
    # Clean up
    net.stop()
 
if __name__ == '__main__':
    setLogLevel('warning')
    terrestrial_network()
