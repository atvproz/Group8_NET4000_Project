from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import OVSSwitch
from mininet.log import setLogLevel
from mininet.cli import CLI

class CustomTopo(Topo):
    def build(self):
        # Switches
        r1 = self.addSwitch('s1')
        r2 = self.addSwitch('s2')
        r3 = self.addSwitch('s3')
        r4 = self.addSwitch('s4')
        r5 = self.addSwitch('s5')
        
        # Hosts with IP configuration
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        
        # Single connection per host
        self.addLink(h1, r3)
        self.addLink(h2, r2)
        
        # Switch interconnections
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
    
    net = Mininet(
        topo=topo, 
        link=TCLink,
        controller=None,
        switch=OVSSwitch,
        autoSetMacs=True,
        autoStaticArp=True
    )
    
    print("\n*** Starting Network...")
    net.start()
    
    # Make switches act as learning switches
    print("\n*** Configuring switches as learning switches...")
    for switch in net.switches:
        switch.cmd('ovs-ofctl add-flow {} action=normal'.format(switch))
    
    # Don't call waitConnected() - it waits for a controller
    
    print("\n*** Testing connectivity...")
    net.pingAll()
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    main()