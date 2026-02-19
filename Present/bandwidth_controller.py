from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
import random

class BandwidthController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(BandwidthController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.link_bandwidths = {}
        self.datapaths = {}
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        self.datapaths[datapath.id] = datapath

        # Request port descriptions to get port info
        req = parser.OFPPortDescStatsRequest(datapath, 0)
        datapath.send_msg(req)

        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def port_desc_stats_reply_handler(self, ev):
        """Handle port description stats reply"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        
        bandwidth_options = [10, 50, 100, 200, 500, 1000]  # Mbps
        
        self.logger.info("=== Bandwidth Assignment for Switch %s ===", datapath.id)
        
        for port in ev.msg.body:
            if port.port_no < ofproto.OFPP_MAX:
                bw = random.choice(bandwidth_options)
                self.link_bandwidths[(datapath.id, port.port_no)] = bw
                self.logger.info("Switch %s Port %s (%s): %s Mbps", 
                               datapath.id, port.port_no, port.name.decode('utf-8'), bw)
                
                # Set bandwidth using meter
                self._set_port_bandwidth(datapath, port.port_no, bw)
        
        self.logger.info("=" * 50)

    def _set_port_bandwidth(self, datapath, port_no, bandwidth_mbps):
        """Set bandwidth limit on a port using meters"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Convert Mbps to kbps for meter
        rate = bandwidth_mbps * 1000
        
        # Create meter for bandwidth limiting
        meter_id = port_no
        bands = [parser.OFPMeterBandDrop(rate=rate, burst_size=0)]
        
        mod = parser.OFPMeterMod(
            datapath=datapath,
            command=ofproto.OFPMC_ADD,
            flags=ofproto.OFPMF_KBPS,
            meter_id=meter_id,
            bands=bands
        )
        datapath.send_msg(mod)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, meter_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if meter_id:
            inst.insert(0, parser.OFPInstructionMeter(meter_id))

        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # Learn MAC address
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow with meter if not flooding
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            
            # Get meter ID for this output port
            meter_id = out_port
            
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id, meter_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions, meter_id=meter_id)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)