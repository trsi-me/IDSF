import time
from collections import defaultdict, deque
from typing import Dict, Any, Callable

from utils.logger import get_logger
from utils.vpn_manager import start_vpn
from utils.https_forcer import enable_https_flag


class ArpDetector:
    """كاشف بسيط لهجوم ARP spoofing بالاعتماد على تغيرات MAC لعنوان IP."""

    def __init__(self, settings: Dict[str, Any], on_attack: Callable[[Dict[str, Any]], None]):
        self.settings = settings
        self.on_attack = on_attack
        self.ip_to_macs: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
        self.logger = get_logger()
        self.threshold = int(settings.get('detection', {}).get('arp', {}).get('mac_change_threshold', 1))
        self.window_seconds = int(settings.get('detection', {}).get('arp', {}).get('window_seconds', 60))

    def process_packet(self, meta: Dict[str, Any]):
        # نعالج فقط حزم ARP
        if meta.get('type') != 'ARP':
            return

        ip = meta.get('src_ip')
        mac = meta.get('src_mac')
        now = time.time()

        macs_queue = self.ip_to_macs[ip]
        macs_queue.append((mac, now))

        # تنظيف العناصر القديمة خارج النافذة الزمنية
        while macs_queue and (now - macs_queue[0][1]) > self.window_seconds:
            macs_queue.popleft()

        unique_macs = {m for m, _ in macs_queue}
        if len(unique_macs) - 1 >= self.threshold:
            # حدث مشبوه
            alert = {
                'type': 'ARP Spoofing',
                'ip': ip,
                'suspected_macs': list(unique_macs),
                'timestamp': now,
                'confidence': 0.9,
                'actions': []
            }
            self.logger.warning(f"تم رصد هجوم ARP محتمل على {ip} بمؤشرات {unique_macs}")
            self._respond(alert)
            # زيادة عداد تنبيهات ARP إن وُجد
            try:
                from web.flask_blueprint import state_registry
                status = state_registry.get('status', {'network': 'Idle', 'counts': {'packets': 0, 'arp_alerts': 0, 'ml_alerts': 0}})
                status['counts']['arp_alerts'] += 1
                state_registry['status'] = status
            except Exception:
                pass
            self.on_attack(alert)

    def _respond(self, alert: Dict[str, Any]):
        mode = self.settings.get('response_mode', 'none')
        if mode in ('vpn', 'both'):
            try:
                start_vpn(self.settings)
                alert['actions'].append('vpn_started')
            except Exception as ex:
                self.logger.error(f"فشل بدء VPN: {ex}")
        if mode in ('https', 'both'):
            try:
                enable_https_flag()
                alert['actions'].append('https_enforced')
            except Exception as ex:
                self.logger.error(f"فشل فرض HTTPS: {ex}")


