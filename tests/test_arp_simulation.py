import time

from detectors.arp_detector import ArpDetector


def test_arp_spoof_detection():
    # إعدادات بسيطة لاختبار تغير MAC مرة واحدة خلال نافذة 60 ثانية
    settings = {
        'response_mode': 'none',
        'detection': { 'arp': { 'mac_change_threshold': 1, 'window_seconds': 60 } }
    }
    detected = {'hit': False}

    def on_attack(alert):
        detected['hit'] = True

    det = ArpDetector(settings, on_attack)

    # حزمة أولى من MAC1
    det.process_packet({'type': 'ARP', 'src_ip': '192.168.1.20', 'src_mac': 'AA:AA:AA:AA:AA:01', 'timestamp': time.time()})
    # حزمة ثانية من MAC2 لنفس الـ IP ضمن النافذة
    det.process_packet({'type': 'ARP', 'src_ip': '192.168.1.20', 'src_mac': 'AA:AA:AA:AA:AA:02', 'timestamp': time.time()})

    assert detected['hit'] is True


