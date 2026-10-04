import time
from typing import Dict, Any
from flask import Blueprint, jsonify, render_template, request


web_bp = Blueprint('web', __name__)

# مسجل حالة بسيط للوصول من بقية أجزاء التطبيق
state_registry: Dict[str, Any] = {}


@web_bp.route('/')
def index():
    return render_template('index.html')


@web_bp.route('/settings')
def settings_page():
    return render_template('settings.html')


@web_bp.get('/api/status')
def api_status():
    status = state_registry.get('status', {'network': 'Idle', 'counts': {'packets': 0, 'arp_alerts': 0, 'ml_alerts': 0}})
    return jsonify(status)


@web_bp.get('/api/alerts')
def api_alerts():
    alerts = state_registry.get('alerts', [])[-50:]
    return jsonify(alerts)


@web_bp.get('/api/traffic')
def api_traffic():
    # إعادة أحدث الحزم لمحاكاة طرفية الشبكة
    traffic = state_registry.get('traffic', [])[-200:]
    return jsonify(traffic)


@web_bp.get('/api/stats')
def api_stats():
    status = state_registry.get('status', {'network': 'Idle', 'counts': {'packets': 0, 'arp_alerts': 0, 'ml_alerts': 0}})
    return jsonify(status.get('counts', {}))


@web_bp.post('/api/settings')
def api_settings():
    body = request.get_json(silent=True) or {}
    settings = state_registry.get('settings', {})
    
    # تحديث وضع الاستجابة
    mode = body.get('response_mode')
    if mode in ('vpn', 'https', 'both', 'none'):
        settings['response_mode'] = mode
    
    # تحديث إعدادات المستمع
    if 'enable_listener' in body:
        settings.setdefault('app', {})['enable_listener'] = bool(body['enable_listener'])
    if 'use_real_capture' in body:
        settings.setdefault('app', {})['use_real_capture'] = bool(body['use_real_capture'])
    
    state_registry['settings'] = settings
    return jsonify({'ok': True, 'settings': settings})


@web_bp.post('/api/monitoring/start')
def start_monitoring():
    """بدء مراقبة الشبكة الفعلية"""
    settings = state_registry.get('settings', {})
    settings.setdefault('app', {})['enable_listener'] = True
    state_registry['settings'] = settings
    state_registry['monitoring_active'] = True

    # بدء المستمع الفعلي عبر الدالة المخزنة في السجل
    starter = state_registry.get('start_listener')
    success = False
    if callable(starter):
        try:
            success = bool(starter())
        except Exception:
            success = False

    if success:
        return jsonify({'ok': True, 'message': 'تم بدء مراقبة الشبكة - الحركة تظهر الآن في الطرفية'})
    else:
        return jsonify({'ok': False, 'message': 'فشل في بدء مراقبة الشبكة'})


@web_bp.post('/api/monitoring/stop')
def stop_monitoring():
    """إيقاف مراقبة الشبكة"""
    settings = state_registry.get('settings', {})
    settings.setdefault('app', {})['enable_listener'] = False
    state_registry['settings'] = settings
    state_registry['monitoring_active'] = False

    # إيقاف المستمع الفعلي عبر الدالة المخزنة
    stopper = state_registry.get('stop_listener')
    if callable(stopper):
        try:
            stopper()
        except Exception:
            pass

    return jsonify({'ok': True, 'message': 'تم إيقاف مراقبة الشبكة'})


@web_bp.get('/api/monitoring/status')
def monitoring_status():
    """حالة المراقبة الحالية"""
    active = state_registry.get('monitoring_active', False)
    settings = state_registry.get('settings', {})
    return jsonify({
        'active': active,
        'listener_enabled': settings.get('app', {}).get('enable_listener', False),
        'real_capture': settings.get('app', {}).get('use_real_capture', False)
    })


@web_bp.get('/api/system/info')
def system_info():
    """معلومات النظام"""
    return jsonify({
        'name': 'IDSF',
        'version': '1.0.0',
        'description': 'نظام كشف التسلل الذكي - مراقبة الشبكة بالذكاء الاصطناعي',
        'features': [
            'كشف هجمات ARP Spoofing',
            'تحليل حركة الشبكة بالذكاء الاصطناعي',
            'مراقبة مباشرة مثل Wireshark',
            'استجابة تلقائية للتهديدات'
        ]
    })


@web_bp.get('/api/health')
def health_check():
    """فحص صحة النظام"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'uptime': 'running'
    })


