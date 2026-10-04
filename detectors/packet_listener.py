import time
import random
from typing import Callable, Dict, Any

# محاولة استيراد scapy للالتقاط الحقيقي، مع fallback للمحاكاة
try:
    from scapy.all import sniff, ARP, IP, Ether
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class PacketListener:
    """مستمع حزم يدعم الالتقاط الحقيقي عبر scapy أو المحاكاة كبديل آمن."""

    def __init__(self, on_packet: Callable[[Dict[str, Any]], None], use_real_capture: bool = False):
        self.on_packet = on_packet
        self._running = True
        self.use_real_capture = use_real_capture and SCAPY_AVAILABLE

    def _scapy_callback(self, packet):
        """معالج حزم scapy - يستخرج معلومات ARP/IP الأساسية."""
        try:
            meta = {'timestamp': time.time()}
            
            if packet.haslayer(ARP):
                arp = packet[ARP]
                meta.update({
                    'type': 'ARP',
                    'src_ip': arp.psrc,
                    'dst_ip': arp.pdst,
                    'src_mac': arp.hwsrc,
                    'dst_mac': arp.hwdst,
                })
            elif packet.haslayer(IP):
                ip = packet[IP]
                meta.update({
                    'type': 'IP',
                    'src_ip': ip.src,
                    'dst_ip': ip.dst,
                    'protocol': ip.proto,
                })
                if packet.haslayer(Ether):
                    meta['src_mac'] = packet[Ether].src
                    meta['dst_mac'] = packet[Ether].dst
            
            if len(meta) > 1:  # إذا تم استخراج معلومات مفيدة
                self.on_packet(meta)
        except Exception:
            pass  # تجاهل الأخطاء في معالجة الحزم

    def run(self):
        if self.use_real_capture:
            try:
                # الالتقاط الحقيقي - قد يتطلب صلاحيات إدارية
                sniff(prn=self._scapy_callback, stop_filter=lambda x: not self._running)
            except Exception as e:
                print(f"فشل الالتقاط الحقيقي: {e}. العودة للمحاكاة.")
                self._run_simulation()
        else:
            self._run_simulation()

    def _run_simulation(self):
        """محاكاة وصول حزم متنوعة لأغراض الاختبار."""
        packet_types = ['ARP', 'IP', 'TCP', 'UDP']
        ips = ['192.168.1.10', '192.168.1.20', '192.168.1.30', '10.0.0.5']
        macs = ['AA:BB:CC:DD:EE:01', 'AA:BB:CC:DD:EE:02', 'AA:BB:CC:DD:EE:03']
        
        while self._running:
            ptype = random.choice(packet_types)
            meta = {
                'type': ptype,
                'src_ip': random.choice(ips),
                'dst_ip': random.choice(ips),
                'src_mac': random.choice(macs),
                'timestamp': time.time(),
            }
            
            # إضافة تفاصيل إضافية حسب نوع الحزمة
            if ptype == 'ARP':
                meta['operation'] = random.choice(['request', 'reply'])
            elif ptype in ['TCP', 'UDP']:
                meta['src_port'] = random.randint(1024, 65535)
                meta['dst_port'] = random.choice([80, 443, 22, 53, 25])
            
            self.on_packet(meta)
            time.sleep(random.uniform(1, 4))  # فترات عشوائية أكثر واقعية

    def stop(self):
        self._running = False


