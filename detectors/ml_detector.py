import os
import time
from typing import Callable, Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from utils.logger import get_logger
from utils.preprocessing import build_preprocessing_pipeline, clean_dataframe


class MlDetector:
    """كاشف بسيط يعتمد نموذج RandomForest تم تدريبه مسبقاً."""

    def __init__(self, base_dir: str, settings: Dict[str, Any], on_alert: Callable[[Dict[str, Any]], None]):
        self.base_dir = base_dir
        self.settings = settings
        self.on_alert = on_alert
        self.logger = get_logger()
        self.model_path = os.path.join(base_dir, 'models', 'rf_model.pkl')
        self.model = self._load_model()

    def _load_model(self):
        # تحميل النموذج من المسار المحلي، وإن لم يوجد يتم تدريب نموذج بسيط وحفظه
        if not os.path.exists(self.model_path):
            try:
                data_path = os.path.join(self.base_dir, 'data', 'sample_nslkdd.csv')
                df = pd.read_csv(data_path)
                df = clean_dataframe(df)
                pipeline, features = build_preprocessing_pipeline(df)
                X = df[features]
                y = df['label'].astype(int)
                Xp = pipeline.fit_transform(X)
                clf = RandomForestClassifier(n_estimators=64, random_state=42)
                clf.fit(Xp, y)
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                joblib.dump({'model': clf, 'pipeline': pipeline, 'features': features}, self.model_path)
                self.logger.info('تم تدريب نموذج RandomForest مع معالجة مسبقة وحفظه محلياً.')
            except Exception as ex:
                self.logger.error(f'فشل تدريب/حفظ النموذج: {ex}')
                return None
        try:
            return joblib.load(self.model_path)
        except Exception as ex:
            self.logger.error(f'فشل تحميل النموذج: {ex}')
            return None

    def process_packet(self, meta: Dict[str, Any]):
        # مثال تبسيطي: توليد ميزات ثابتة وإجراء تنبؤ إذا توفر النموذج
        if self.model is None:
            return

        # اشتقاق ميزات مبسّطة من الحزمة + تمريرها عبر pipeline إذا توفر
        src_ip = meta.get('src_ip', '0.0.0.0')
        dst_ip = meta.get('dst_ip', '0.0.0.0')
        ptype = meta.get('type', 'UNKNOWN')
        
        # ميزات أكثر واقعية بناءً على نوع الحزمة
        df = pd.DataFrame([{
            'f1': len(src_ip),
            'f2': len(dst_ip),
            'f3': int((time.time() * 1000) % 1000) / 1000.0,
            'f4': hash(ptype) % 100 / 100.0,  # تحويل نوع الحزمة إلى رقم
            'f5': meta.get('src_port', 0) / 65535.0 if 'src_port' in meta else 0.5,
        }])
        obj = self.model
        try:
            if isinstance(obj, dict) and 'pipeline' in obj and 'model' in obj:
                Xp = obj['pipeline'].transform(df)
                y_pred = obj['model'].predict(Xp)
            else:
                y_pred = obj.predict(df.values)
            if int(y_pred[0]) == 1:
                alert = {
                    'type': 'ML Anomaly',
                    'details': {'src_ip': src_ip, 'dst_ip': dst_ip},
                    'timestamp': time.time(),
                }
                self.logger.warning('تم رصد سلوك غير طبيعي عبر نموذج ML.')
                try:
                    from web.flask_blueprint import state_registry
                    status = state_registry.get('status', {'network': 'Idle', 'counts': {'packets': 0, 'arp_alerts': 0, 'ml_alerts': 0}})
                    status['counts']['ml_alerts'] += 1
                    state_registry['status'] = status
                except Exception:
                    pass
                self.on_alert(alert)
        except Exception as ex:
            self.logger.error(f'خطأ أثناء التنبؤ: {ex}')


