#!/usr/bin/env python3
"""
Lab 2: GEO Satellite Network Simulation
Orbit altitude: ~36,000 km
Based on: Paper 2 (Azari et al. 2022) - GEO RTT 270ms
          Paper 3 (Wang et al. 2020) - TCP retransmission problem
"""
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
 
def geo_satellite_network():
    net = Mininet(controller=OVSController, link=TCLink)
    net.addController('c0')
 
    # Ground station (h1) and remote user (h2)
    h1 = net.addHost('h1', ip='10.0.0.1')  # Ground station / gateway
    h2 = net.addHost('h2', ip='10.0.0.2')  # End user via satellite
    s1 = net.addSwitch('s1')
 
    # ===== GEO SATELLITE LINK PARAMETERS =====
    # From Paper 2: GEO propagation delay = ~270ms one-way
    # So we use 270ms on EACH side → RTT = 270+270 = 540ms
    #
    # From Paper 3: satellite channels have higher loss
    # and limited bandwidth compared to terrestrial
    #
    # From Paper 4: experimental NTN end-to-end delay is 80-160ms
    # (LEO/UAV based) - GEO would be much higher
    GEO_DELAY    = '270ms'   # Paper 2: one-way propagation delay
    GEO_JITTER   = '30ms'    # Paper 2: GEO has some timing variance
    GEO_LOSS     = 2.0       # Paper 4: NTN ~7-13% loss at high bitrate; 2% at low
    GEO_BW       = 20        # Mbps: typical GEO downlink
    GEO_UPLINK   = 5         # Mbps: satellite uplink is more constrained (Paper 3)
 
    # Downlink (satellite to user) — higher bandwidth
    net.addLink(h1, s1, bw=GEO_BW, delay=GEO_DELAY,
                loss=GEO_LOSS, max_queue_size=200)
    # Uplink (user to satellite) — lower bandwidth, Paper 3 finding
    net.addLink(h2, s1, bw=GEO_UPLINK, delay=GEO_DELAY,
                loss=GEO_LOSS, max_queue_size=200)
 
    net.start()
 
    print('\n' + '='*65)
    print('GEO SATELLITE NETWORK STARTED')
    print(f'Delay:     {GEO_DELAY} each way → RTT ~540ms (Paper 2)')
    print(f'Jitter:    {GEO_JITTER} (Paper 2: GEO timing variance)')
    print(f'Loss:      {GEO_LOSS}% (Paper 3-4: atmospheric + shadowing)')
    print(f'Bandwidth: {GEO_BW}/{GEO_UPLINK} Mbps down/up (Paper 3: asymmetric)')
    print('Expected RTT: ~540ms vs terrestrial ~10ms = 54x higher!')
    print('='*65 + '\n')
 
    # Automatic comparison tests
    print('--- Connectivity test ---')
    print(h1.cmd('ping -c 5 10.0.0.2'))
 
    print('\n--- RTT measurement (20 pings) ---')
    print('Notice the ~540ms RTT vs ~10ms terrestrial!')
    print(h1.cmd('ping -c 20 -i 0.5 10.0.0.2'))
 
    print('\n--- Throughput test (15 seconds) ---')
    h2.cmd('iperf3 -s -D')  # Start server in background
    import time
    time.sleep(1)
    print('Notice how throughput is LIMITED by the delay (TCP window issue):')
    #print(h1.cmd('iperf3 -c 10.0.0.2 -t 15'))
 
    print('\n--- TCP retransmission check (Paper 3 finding) ---')
    print('Run: h1 ss -tin   to see retrans counter climbing')

    ## -- checking cli window
    # print("Entering CLI...")
    # print("Hosts:", net.hosts)
    # print("Switches:", net.switches)
    # print("Links:", net.links)
    ## --

    print("About to enter CLI")
    print("TEST1 =", repr(h1.cmd('echo hello')))
    print("TEST2 =", repr(h2.cmd('echo bye')))
    print("TEST3 =", net.hosts)
    
    CLI(net)
    
    print("Returned from CLI")
    net.stop()
 
if __name__ == '__main__':
    setLogLevel('warning')
    geo_satellite_network()
