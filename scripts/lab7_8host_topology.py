#!/usr/bin/env python3
"""
8-Host Satellite Network Topology
===================================
Architecture:
  h1-h4  --  s1  --  r1  ~~WAN~~  r2  --  s2  --  h5-h8

  s1/s2 = LAN switches (clean links, no impairment)
  r1-r2 = routers (WAN link carries satellite/terrestrial parameters)

Subnets:
  Left LAN  (h1-h4, s1, r1-eth0): 10.0.1.0/24
  WAN link  (r1-eth1 <--> r2-eth0): 10.0.99.0/30
  Right LAN (h5-h8, s2, r2-eth1): 10.0.2.0/24

Usage:
  sudo python3 lab_8host_topology.py [profile]
  profiles: terrestrial | leo | geo | geo_worst
"""

from mininet.net import Mininet
from mininet.node import OVSController, Node
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
import sys, time


# ── Satellite / terrestrial profiles (same as Labs 1-4) ──────────────
PROFILES = {
    'terrestrial': {
        'delay': '5ms',   'jitter': '1ms',  'loss': 0.1,
        'bw_down': 100,   'bw_up': 100,
        'desc': 'Terrestrial broadband baseline'
    },
    'leo': {
        'delay': '20ms',  'jitter': '10ms', 'loss': 1.5,
        'bw_down': 100,   'bw_up': 50,
        'desc': 'LEO Satellite - Starlink-like (Paper 2)'
    },
    'geo': {
        'delay': '270ms', 'jitter': '30ms', 'loss': 2.0,
        'bw_down': 20,    'bw_up': 5,
        'desc': 'GEO Satellite (Paper 2: 270ms one-way, Paper 3: asymmetric)'
    },
    'geo_worst': {
        'delay': '300ms', 'jitter': '50ms', 'loss': 5.0,
        'bw_down': 10,    'bw_up': 2,
        'desc': 'GEO worst-case: rain fade + shadowing (Paper 3)'
    },
}


class LinuxRouter(Node):
    """A Linux node with IP forwarding enabled — acts as a router."""

    def config(self, **params):
        super().config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super().terminate()


def build_8host_network(profile_name='geo'):
    p = PROFILES[profile_name]

    # TCLink is required for any link that needs bw/delay/loss parameters.
    # LAN links won't set those parameters, but TCLink is harmless there.
    net = Mininet(controller=OVSController, link=TCLink)
    net.addController('c0')

    # ── Routers ───────────────────────────────────────────────────────
    # ip= sets the loopback; actual interface IPs are set manually below
    r1 = net.addHost('r1', cls=LinuxRouter, ip=None)
    r2 = net.addHost('r2', cls=LinuxRouter, ip=None)

    # ── Switches (clean LAN segments) ────────────────────────────────
    s1 = net.addSwitch('s1')   # Left LAN
    s2 = net.addSwitch('s2')   # Right LAN

    # ── Left LAN hosts  (10.0.1.0/24) ───────────────────────────────
    h1 = net.addHost('h1', ip='10.0.1.1/24', defaultRoute='via 10.0.1.254')
    h2 = net.addHost('h2', ip='10.0.1.2/24', defaultRoute='via 10.0.1.254')
    h3 = net.addHost('h3', ip='10.0.1.3/24', defaultRoute='via 10.0.1.254')
    h4 = net.addHost('h4', ip='10.0.1.4/24', defaultRoute='via 10.0.1.254')

    # ── Right LAN hosts (10.0.2.0/24) ───────────────────────────────
    h5 = net.addHost('h5', ip='10.0.2.1/24', defaultRoute='via 10.0.2.254')
    h6 = net.addHost('h6', ip='10.0.2.2/24', defaultRoute='via 10.0.2.254')
    h7 = net.addHost('h7', ip='10.0.2.3/24', defaultRoute='via 10.0.2.254')
    h8 = net.addHost('h8', ip='10.0.2.4/24', defaultRoute='via 10.0.2.254')

    # ── Links ─────────────────────────────────────────────────────────

    # Left LAN: hosts → s1 (clean, no impairment)
    for h in [h1, h2, h3, h4]:
        net.addLink(h, s1)

    # s1 → r1 (LAN side, clean)
    net.addLink(s1, r1,
                intfName2='r1-eth0',
                params2={'ip': '10.0.1.254/24'})

    # *** WAN link r1 <--> r2: THIS is where satellite parameters go ***
    # Downlink direction (r1→r2): apply downstream BW/delay
    # Uplink direction   (r2→r1): apply upstream BW/delay
    # TCLink applies the parameters to BOTH directions symmetrically here;
    # for true asymmetry, we override one direction with tc after start().
    net.addLink(r1, r2,
                intfName1='r1-eth1',
                intfName2='r2-eth0',
                params1={'ip': '10.0.99.1/30'},
                params2={'ip': '10.0.99.2/30'},
                bw=p['bw_down'],          # WAN bandwidth
                delay=p['delay'],         # one-way propagation delay
                loss=p['loss'],           # packet loss %
                max_queue_size=200)

    # r2 → s2 (LAN side, clean)
    net.addLink(r2, s2,
                intfName1='r2-eth1',
                params1={'ip': '10.0.2.254/24'})

    # Right LAN: hosts → s2 (clean, no impairment)
    for h in [h5, h6, h7, h8]:
        net.addLink(h, s2)

    # ── Start network ─────────────────────────────────────────────────
    net.start()

    # ── Routing: add static routes so left↔right subnets can reach each other
    r1.cmd('ip route add 10.0.2.0/24 via 10.0.99.2')
    r2.cmd('ip route add 10.0.1.0/24 via 10.0.99.1')

    # ── Apply asymmetric uplink on the WAN link (r2→r1 direction) ────
    # The TCLink above already applied bw_down/delay/loss to the r1-eth1 interface.
    # Now apply the (usually lower) bw_up to r2-eth0 so uplink is constrained.
    r2.cmd(
        f'tc qdisc replace dev r2-eth0 root netem '
        f'delay {p["delay"]} {p["jitter"]} distribution normal '
        f'loss {p["loss"]} '
        f'rate {p["bw_up"]}mbit '
        f'limit 200'
    )

    # ── Print summary ─────────────────────────────────────────────────
    print('\n' + '='*70)
    print(f'8-HOST SATELLITE TOPOLOGY — Profile: {profile_name.upper()}')
    print(f'{p["desc"]}')
    print('='*70)
    print('LEFT  LAN  (10.0.1.0/24): h1=.1  h2=.2  h3=.3  h4=.4  gw=.254')
    print('RIGHT LAN  (10.0.2.0/24): h5=.1  h6=.2  h7=.3  h8=.4  gw=.254')
    print(f'WAN link   (10.0.99.0/30): r1=.1  r2=.2')
    print(f'  Delay  : {p["delay"]} one-way → RTT ~{int(p["delay"][:-2])*2} ms')
    print(f'  Jitter : {p["jitter"]}')
    print(f'  Loss   : {p["loss"]}%')
    print(f'  BW     : {p["bw_down"]} Mbps down / {p["bw_up"]} Mbps up')
    print('='*70)

    # ── Automatic tests ───────────────────────────────────────────────

    print('\n[1] Basic connectivity — ping from h1 (left) to h5 (right):')
    print(h1.cmd('ping -c 5 10.0.2.1'))

    print('\n[2] Cross-subnet RTT measurement (20 pings, h1 → h8):')
    print(h1.cmd('ping -c 20 -i 0.5 10.0.2.4'))

    print('\n[3] Throughput test — h1 → h5 (20 seconds):')
    h5.cmd('iperf3 -s -D')
    time.sleep(1)
    print(h1.cmd('iperf3 -c 10.0.2.1 -t 20'))

    print('\n[4] Concurrent multi-host test (h1+h2 → h5+h6 simultaneously):')
    h6.cmd('iperf3 -s -p 5202 -D')
    time.sleep(1)
    h2.cmd('iperf3 -c 10.0.2.2 -p 5202 -t 15 -i 5 &')
    print(h1.cmd('iperf3 -c 10.0.2.1 -t 15 -i 5'))

    print('\n[5] TCP retransmission check (Paper 3 finding):')
    print(h1.cmd('ss -tin | grep -i retrans | head -5'))

    # ── Useful CLI hints ──────────────────────────────────────────────
    print('\n' + '-'*70)
    print('USEFUL CLI COMMANDS:')
    print('  h1 ping -c 30 10.0.2.1        # RTT across WAN link')
    print('  h3 ping -c 30 10.0.2.3        # h3 → h7')
    print('  h5 iperf3 -s &')
    print('  h1 iperf3 -c 10.0.2.1 -t 30   # throughput h1→h5')
    print('  h1 iperf3 -c 10.0.2.1 -t 60 -i 5 -P 4  # 4 parallel streams')
    print('  h1 ss -tin                    # TCP socket stats')
    print('  r1 tc qdisc show dev r1-eth1  # see WAN link config on r1')
    print('  r2 tc qdisc show dev r2-eth0  # see WAN link config on r2')
    print('  pingall                       # test all-pairs connectivity')
    print('-'*70 + '\n')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('warning')
    profile = sys.argv[1] if len(sys.argv) > 1 else 'geo'
    if profile not in PROFILES:
        print(f'Unknown profile "{profile}". Choose: {list(PROFILES.keys())}')
        sys.exit(1)
    build_8host_network(profile)
