import logging
import os
from typing import Optional


_LOGGER: Optional[logging.Logger] = None


def get_logger(log_path: Optional[str] = None) -> logging.Logger:
    """إنشاء لوجر موحد للتطبيق.

    إذا تم تمرير مسار ملف، سيتم إنشاء FileHandler. وإلا، نعيد اللوجر الحالي.
    """
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger('IDSF')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_path:
        try:
            base_dir = os.path.dirname(log_path)
            if base_dir and not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)
            fh = logging.FileHandler(log_path, encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            # نتجاهل أخطاء ملف السجل للحفاظ على التشغيل
            pass

    _LOGGER = logger
    return logger


