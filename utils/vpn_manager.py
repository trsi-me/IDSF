import os
import subprocess
import time
from typing import Dict, Any

from .logger import get_logger


def start_vpn(settings: Dict[str, Any]) -> None:
    """تشغيل سكربت VPN المحلي من داخل المشروع مع محاولات إعادة.

    لا يتم تثبيت أي برامج خارجية. يعتمد فقط على السكربت المحلي.
    """
    logger = get_logger()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    script_name = settings.get('vpn', {}).get('script', 'vpn_client_windows.bat')
    timeout = int(settings.get('vpn', {}).get('timeout', 60))
    script_path = os.path.join(base_dir, script_name)

    if not os.path.exists(script_path):
        raise FileNotFoundError(f'السكربت غير موجود: {script_path}')

    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            logger.info(f'تشغيل سكربت VPN ({script_name}) المحاولة {attempt}/{attempts}')
            if script_path.lower().endswith('.ps1'):
                # تشغيل PowerShell سكربت
                proc = subprocess.run([
                    'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script_path
                ], cwd=base_dir, timeout=timeout, capture_output=True, text=True)
            else:
                # تشغيل batch سكربت
                proc = subprocess.run([
                    script_path
                ], cwd=base_dir, timeout=timeout, capture_output=True, text=True, shell=True)

            logger.info(f'خروج VPN code={proc.returncode} stdout={proc.stdout} stderr={proc.stderr}')
            if proc.returncode == 0:
                return
        except subprocess.TimeoutExpired:
            logger.error('انتهت المهلة أثناء محاولة تشغيل VPN')
        except Exception as ex:
            logger.error(f'فشل تشغيل VPN: {ex}')

        # تأخير متزايد بين المحاولات
        time.sleep(2 * attempt)

    raise RuntimeError('تعذر بدء اتصال VPN بعد عدة محاولات')


