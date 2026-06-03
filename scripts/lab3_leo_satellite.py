#!/usr/bin/env python3
"""
Lab 3: LEO Satellite Network Simulation (Starlink-like)
Orbit altitude: 300-1500 km
Based on: Paper 2 (Azari et al.): Starlink 20-40ms, 50-150 Mbps
          Paper 2: Doppler shift 48 kHz → causes jitter
          Paper 3: LEO handovers increase jitter
"""
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
import time, threading
 
def simulate_leo_handover(net, h1, h2):
    """Simulate LEO satellite handover by briefly increasing delay."""
    # Paper 2: LEO satellites cause frequent handovers
    # during which jitter spikes (Paper 3 finding)
    print('\n[HANDOVER] LEO satellite beam switching — jitter spike!')

    # h1.cmd('tc qdisc change dev h1-eth0 root netem delay 80ms 60ms')
    #-- to rectify the 'Assertion Error' replace this line with the one below
    h1.cmd('tc qdisc replace dev h1-eth0 root netem delay 80ms 60ms &')
    
    time.sleep(3)  # Handover lasts ~3 seconds
    h1.cmd('tc qdisc change dev h1-eth0 root netem delay 20ms 10ms')
    print('[HANDOVER] Complete — back to normal LEO delay')
 
def leo_satellite_network():
    net = Mininet(controller=OVSController, link=TCLink)
    net.addController('c0')
 
    h1 = net.addHost('h1', ip='10.0.0.1')  # Ground station
    h2 = net.addHost('h2', ip='10.0.0.2')  # User terminal
    s1 = net.addSwitch('s1')
 
    # ===== LEO SATELLITE LINK PARAMETERS =====
    # Paper 2: Starlink latency 20-40ms, so 20ms one-way
    LEO_DELAY  = '20ms'   # Paper 2: Starlink one-way delay
    LEO_JITTER = '10ms'   # Paper 2/3: Doppler + handover jitter
    LEO_LOSS   = 1.5      # Less than GEO but still elevated
    LEO_BW     = 100      # Paper 2: Starlink 50-150 Mbps
 
    net.addLink(h1, s1, bw=LEO_BW, delay=LEO_DELAY,
                loss=LEO_LOSS, max_queue_size=1000)
    net.addLink(h2, s1, bw=LEO_BW, delay=LEO_DELAY,
                loss=LEO_LOSS, max_queue_size=1000)
 
    net.start()
 
    print('\n' + '='*65)
    print('LEO SATELLITE NETWORK STARTED (Starlink-like)')
    print(f'Delay:     {LEO_DELAY} one-way → RTT ~40ms')
    print(f'Jitter:    {LEO_JITTER} (Paper 2: Doppler shift effect)')
    print(f'Loss:      {LEO_LOSS}%')
    print(f'Bandwidth: {LEO_BW} Mbps (Paper 2: Starlink 50-150 Mbps)')
    print('RTT: ~40ms vs GEO ~540ms → 13x better!')
    print('But: much higher jitter than terrestrial (Paper 2/3)')
    print('='*65 + '\n')
 
    print('--- LEO RTT test ---')
    print(h1.cmd('ping -c 20 -i 0.2 10.0.0.2'))
 
    # Simulate a handover event after 10 seconds
    handover_thread = threading.Timer(10.0, simulate_leo_handover,
                                      args=[net, h1, h2])
    handover_thread.start()

    print('\n--- Throughput test (watch for handover jitter at ~10s) ---')
    h2.cmd('iperf3 -s -D')
    time.sleep(1)
    # print(h1.cmd('iperf3 -c 10.0.0.2 -t 30 -i 2'))
    #-- to rectify the 'Assertion Error' replace the above line with the one below
    h1.cmdPrint('iperf -c 10.0.0.2 -t 30 -i 2')    
 
    CLI(net)
    net.stop()
 
if __name__ == '__main__':
    setLogLevel('warning')
    leo_satellite_network()
