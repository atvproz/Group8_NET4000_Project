from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from mininet.log import setLogLevel
from mininet.cli import CLI
import time

class CustomTopo(Topo):
    def build(self):
        r1 = self.addSwitch('s1', protocols='OpenFlow13')
        r2 = self.addSwitch('s2', protocols='OpenFlow13')
        r3 = self.addSwitch('s3', protocols='OpenFlow13')
        r4 = self.addSwitch('s4', protocols='OpenFlow13')
        r5 = self.addSwitch('s5', protocols='OpenFlow13')
        
        h1 = self.addHost('h1', ip='10.0.0.1/24', defaultRoute='via 10.0.0.254')
        h2 = self.addHost('h2', ip='10.0.0.2/24', defaultRoute='via 10.0.0.254')
        
        self.addLink(h1, r3)
        self.addLink(h2, r2)
        self.addLink(r1, r2)
        self.addLink(r1, r3)
        self.addLink(r1, r4)
        self.addLink(r1, r5)
        self.addLink(r2, r3)
        self.addLink(r2, r5)
        self.addLink(r3, r4)
        self.addLink(r4, r5)

def main():
    setLogLevel('info')
    topo = CustomTopo()
    c0 = RemoteController('c0', ip='127.0.0.1', port=6633)
    net = Mininet(
        topo=topo,
        link=TCLink,
        controller=c0,
        switch=OVSSwitch,
        autoSetMacs=True,
        autoStaticArp=False
    )
    
    print("\n Starting Network...")
    net.start()
    
    # Enable STP at the switch level, not controller level
    print("\n Enabling Spanning Tree Protocol on switches...")
    for switch in net.switches:
        switch.cmd('ovs-vsctl set Bridge', switch.name, 'stp_enable=true')
    
    print("\n Waiting for STP to converge (30 seconds)...")
    time.sleep(30)
    
    print("\n Testing connectivity...")
    net.pingAll()
    
    CLI(net)
    net.stop()
    
if __name__ == '__main__':
    main()
