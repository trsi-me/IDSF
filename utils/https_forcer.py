import os
from typing import Optional, Dict, Any

from flask import Flask
try:
    from flask_talisman import Talisman
except Exception:
    # في حال غياب المكتبة، نسند قيمة None ونتعامل برفق
    Talisman = None  # type: ignore

from .logger import get_logger

_HTTPS_ENFORCED = False


def configure_https_policy(app: Flask, settings: Dict[str, Any]) -> None:
    """تفعيل سياسات HTTPS على مستوى الرؤوس وإعادة التوجيه عند الطلب."""
    global _HTTPS_ENFORCED
    mode = settings.get('response_mode', 'none')
    if mode in ('https', 'both'):
        if Talisman is not None:
            # تفعيل Talisman لفرض HTTPS عبر الرؤوس
            Talisman(app, content_security_policy=None)
        _HTTPS_ENFORCED = True


def enable_https_flag():
    """تمكين العلم الداخلي لفرض HTTPS (لاعادة توجيه/تشغيل SSL عند البدء)."""
    global _HTTPS_ENFORCED
    _HTTPS_ENFORCED = True


def get_ssl_context_if_enabled(settings: Dict[str, Any]) -> Optional[tuple]:
    """إرجاع سياق SSL إذا كان مفعلًا وفق الإعدادات وبشرط صلاحية ملفات PEM.

    إذا كانت الشهادات غير صالحة (أو عناصر نائبة)، يتم تجاهل SSL وتشغيل HTTP.
    """
    if not _HTTPS_ENFORCED and settings.get('response_mode', 'none') not in ('https', 'both'):
        return None
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    cert_rel = settings.get('https', {}).get('cert', 'certs/server.crt')
    key_rel = settings.get('https', {}).get('key', 'certs/server.key')
    cert_path = os.path.join(base_dir, cert_rel)
    key_path = os.path.join(base_dir, key_rel)

    try:
        if not (os.path.exists(cert_path) and os.path.exists(key_path)):
            get_logger().warning('شهادات HTTPS غير متوفرة. سيتم التشغيل بدون SSL.')
            return None
        with open(cert_path, 'r', encoding='utf-8', errors='ignore') as fc:
            cert_head = fc.read(128)
        with open(key_path, 'r', encoding='utf-8', errors='ignore') as fk:
            key_head = fk.read(128)
        # تحقق بدائي لصلاحية PEM
        if 'BEGIN CERTIFICATE' not in cert_head or 'BEGIN' not in key_head:
            get_logger().warning('ملفات الشهادة تبدو غير صالحة (ليست PEM). التشغيل بدون SSL.')
            return None
        return cert_path, key_path
    except Exception as ex:
        get_logger().warning(f'تعذر استخدام شهادات HTTPS: {ex}. سيتم التشغيل بدون SSL.')
        return None


