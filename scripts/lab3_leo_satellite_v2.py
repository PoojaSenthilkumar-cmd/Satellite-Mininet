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
import time
 
 
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
    # Explicitly configure LEO delay+jitter
    h1.cmd('tc qdisc replace dev h1-eth0 root netem delay 20ms 10ms loss 1.5%')
    
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

    print('\n--- Throughput test (watch for handover jitter at ~10s) ---')
    # Clean up old iperf processes
    h1.cmd('pkill iperf3')
    h2.cmd('pkill iperf3')

    # Start server
    h2.cmd('iperf3 -s -D')
    time.sleep(1)
    
    # Start client in background
    h1.cmd('iperf3 -c 10.0.0.2 -t 30 -i 2 > /tmp/iperf.log &')
    
    # Wait 10 seconds
    time.sleep(10)
    print('\n[HANDOVER] LEO satellite beam switching — jitter spike!')
    h1.cmd('tc qdisc replace dev h1-eth0 root netem delay 80ms 60ms loss 1.5%')
    time.sleep(3)
    h1.cmd('tc qdisc replace dev h1-eth0 root netem delay 20ms 10ms loss 1.5%')
    
    print('[HANDOVER] Complete — back to normal LEO delay')
    # Wait for iperf3 to finish
    time.sleep(18)
    print('\n--- Throughput Results ---')
    print(h1.cmd('cat /tmp/iperf.log'))
 
    CLI(net)
    net.stop()
 
if __name__ == '__main__':
    setLogLevel('warning')
    leo_satellite_network()

