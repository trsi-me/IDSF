import os
import threading
import time
from typing import Dict, Any

from flask import Flask
import yaml

from utils.logger import get_logger
from utils.https_forcer import configure_https_policy, get_ssl_context_if_enabled
from web.flask_blueprint import web_bp, state_registry
from detectors.packet_listener import PacketListener
from detectors.arp_detector import ArpDetector
from detectors.ml_detector import MlDetector


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'settings.yaml')


def load_settings() -> Dict[str, Any]:
    # تحميل ملف الإعدادات من YAML
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_app(settings: Dict[str, Any]) -> Flask:
    # تهيئة تطبيق Flask وتسجيل البلوبّرنت
    app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'web', 'templates'), static_folder=os.path.join(BASE_DIR, 'web', 'static'))

    # إعداد اللوغر العام
    logger = get_logger(os.path.join(BASE_DIR, 'idsf.log'))
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)

    # تخزين الإعدادات والحالة في سجل مشترك بسيط
    state_registry['settings'] = settings
    state_registry['alerts'] = []  # قائمة تنبيهات تعرض في الواجهة
    state_registry['traffic'] = []  # أحدث حركة حزم لعرضها طرفياً
    state_registry['status'] = {'network': 'Idle', 'counts': {'packets': 0, 'arp_alerts': 0, 'ml_alerts': 0}}
    state_registry['monitoring_active'] = False  # حالة المراقبة

    # فرض سياسات HTTPS إذا لزم (تأمين الرؤوس/الروابط داخل التطبيق)
    configure_https_policy(app, settings)

    # ربط المسارات عبر البلوبّرنت
    app.register_blueprint(web_bp)

    return app


def start_background_services(settings: Dict[str, Any], app_logger):
    # إنشاء كواشف ARP و ML مع مستمع الحزم (تشغيل في خيوط خلفية)
    response_mode = settings.get('response_mode', 'none')

    arp_detector = ArpDetector(settings=settings, on_attack=lambda alert: state_registry['alerts'].append(alert))
    ml_detector = MlDetector(base_dir=BASE_DIR, settings=settings, on_alert=lambda alert: state_registry['alerts'].append(alert))

    # متغيرات عامة للمستمع
    listener_thread = None
    current_listener = None

    def start_packet_listener():
        """بدء مستمع الحزم في خيط منفصل"""
        nonlocal listener_thread, current_listener
        
        if listener_thread and listener_thread.is_alive():
            return  # المستمع يعمل بالفعل
            
        def handle_packet(meta):
            # تحديث الحالة وعرض الحركة في الطرفية
            status = state_registry.get('status', {'network': 'Idle', 'counts': {'packets': 0, 'arp_alerts': 0, 'ml_alerts': 0}})
            status['network'] = 'Active'
            status['counts']['packets'] += 1
            state_registry['status'] = status
            
            # إضافة الحزمة مع تصنيفها
            packet_info = {
                **meta,
                'classification': classify_packet(meta),
                'timestamp': time.time()
            }
            state_registry['traffic'].append(packet_info)
            
            # احتفاظ بآخر 200 سطر فقط
            if len(state_registry['traffic']) > 200:
                del state_registry['traffic'][:-200]
            
            # تمريـر الحزمة للكواشف
            arp_detector.process_packet(meta)
            ml_detector.process_packet(meta)

        def classify_packet(meta):
            """تصنيف الحزمة حسب النوع والبروتوكول"""
            ptype = meta.get('type', 'UNKNOWN')
            src_ip = meta.get('src_ip', '')
            dst_ip = meta.get('dst_ip', '')
            
            if ptype == 'ARP':
                return f"ARP {meta.get('operation', '')} {src_ip} -> {dst_ip}"
            elif ptype == 'IP':
                protocol = meta.get('protocol', '')
                if protocol == 6:
                    return f"TCP {src_ip}:{meta.get('src_port', '?')} -> {dst_ip}:{meta.get('dst_port', '?')}"
                elif protocol == 17:
                    return f"UDP {src_ip}:{meta.get('src_port', '?')} -> {dst_ip}:{meta.get('dst_port', '?')}"
                else:
                    return f"IP {src_ip} -> {dst_ip} (Proto:{protocol})"
            elif ptype in ['TCP', 'UDP']:
                return f"{ptype} {src_ip}:{meta.get('src_port', '?')} -> {dst_ip}:{meta.get('dst_port', '?')}"
            else:
                return f"{ptype} {src_ip} -> {dst_ip}"

        enable_listener = settings.get('app', {}).get('enable_listener', False)
        use_real_capture = settings.get('app', {}).get('use_real_capture', False)
        
        if enable_listener:
            current_listener = PacketListener(on_packet=handle_packet, use_real_capture=use_real_capture)
            listener_thread = threading.Thread(target=current_listener.run, name='PacketListenerThread', daemon=True)
            listener_thread.start()
            app_logger.info('تم بدء مستمع الحزم في الخلفية.')
            return True
        return False

    def stop_packet_listener():
        """إيقاف مستمع الحزم"""
        nonlocal listener_thread, current_listener
        if current_listener:
            current_listener.stop()
            current_listener = None
        if listener_thread and listener_thread.is_alive():
            listener_thread.join(timeout=2)
        app_logger.info('تم إيقاف مستمع الحزم.')

    # إتاحة دوال بدء/إيقاف المستمع لبقية الموديولات عبر state_registry
    state_registry['start_listener'] = start_packet_listener
    state_registry['stop_listener'] = stop_packet_listener

    # بدء المستمع إذا كان مفعل في الإعدادات
    if settings.get('app', {}).get('enable_listener', False):
        start_packet_listener()
    else:
        app_logger.info('تم تعطيل مستمع الحزم عبر الإعدادات.')


if __name__ == '__main__':
    settings = load_settings()
    app = create_app(settings)
    start_background_services(settings, app.logger)

    # تشغيل التطبيق. إذا تم تفعيل HTTPS سيتم تزويد سياق TLS
    ssl_context = get_ssl_context_if_enabled(settings)
    host = settings.get('app', {}).get('host', '0.0.0.0')
    port = int(settings.get('app', {}).get('port', 5000))
    app.run(host=host, port=port, ssl_context=ssl_context)


