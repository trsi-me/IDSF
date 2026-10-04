# IDSF

## 1 ما هو المشروع

IDSF تطبيق Flask لعرض حالة مراقبة شبكة محلية وتنبيهات. الاسم في `GET /api/system/info`: نظام كشف التسلل الذكي، والإصدار في ذلك الرد `1.0.0`.

الموجود في الكود:

- صفحة رئيسية وصفحة إعدادات بالعربي.
- مستمع حزم: التقاط عبر scapy عند تفعيل الخيار، أو حلقة محاكاة تولّد بيانات وصفية عند إيقاف الالتقاط الحقيقي أو عند فشله.
- كاشف ARP: إذا ظهر أكثر من عنوان MAC لعنوان IP واحد داخل نافذة زمنية، يُسجَّل تنبيه وتُزاد العدادات.
- كاشف RandomForest: يحمّل ملفاً محلياً أو يدرّب من CSV عينة، ثم يصدر تنبيهاً عندما يكون صنف التنبؤ 1.
- استجابة اختيارية بعد تنبيه ARP: تشغيل سكربت VPN محلي أو رفع علم HTTPS داخلي، حسب `response_mode`.

هذا وصف للسلوك الدفاعي المكتوب في الكاشفات. المشروع للتشغيل المحلي والتجربة.

## 2 لمن هذا المشروع

مشغّل على جهازه يفتح الواجهة ويبدأ المراقبة أو يوقفها من الأزرار المرتبطة بمسارات `/api/monitoring`. لا حسابات مستخدمين في الكود.

README السابق حدد Windows وPython 3.10.6 ومساراً `C:\Users\UPath\IDSF`. المسار الحالي للمستودع `D:\VSCode\Projects\IDSF`. إصدار بايثون غير مثبت بملف `runtime.txt`.

## 3 الميزات الفعلية

| الميزة | المكان |
| --- | --- |
| لوحة | `GET /` القالب `web/templates/index.html` |
| إعدادات | `GET /settings` |
| حالة الشبكة والعدادات | `GET /api/status` |
| آخر 50 تنبيهاً | `GET /api/alerts` |
| آخر 200 حركة | `GET /api/traffic` |
| عدادات فقط | `GET /api/stats` |
| تحديث وضع الاستجابة والمستمع | `POST /api/settings` |
| بدء المراقبة | `POST /api/monitoring/start` |
| إيقاف المراقبة | `POST /api/monitoring/stop` |
| حالة المراقبة | `GET /api/monitoring/status` |
| معلومات النظام | `GET /api/system/info` |
| فحص صحة | `GET /api/health` |
| رؤوس HTTPS عبر Talisman | عندما `response_mode` هو `https` أو `both` وعند توفر flask-talisman |
| سجل | `idsf.log` عبر `utils/logger.py` |
| اختبار كاشف ARP | `tests/test_arp_simulation.py` |

القيم الافتراضية في `config/settings.yaml`: `response_mode: none`، المستمع معطّل، الالتقاط الحقيقي معطّل، المضيف `0.0.0.0`، المنفذ `5000`.

عتبة ARP: `mac_change_threshold: 1` و`window_seconds: 60`. الكاشف يحسب عناوين MAC المختلفة في النافذة ويطلق التنبيه عندما `len(unique_macs) - 1 >= threshold`.

## 4 أمثلة واقعية

رد معلومات النظام يتضمن الاسم `IDSF` والإصدار `1.0.0` ووصفاً عربياً وقائمة ميزات نصية.

`POST /api/settings` يقبل `response_mode` إحدى القيم: `vpn`, `https`, `both`, `none`. ويقبل مفتاحي `enable_listener` و`use_real_capture` كقيم منطقية.

بدء المراقبة يضع `enable_listener` إلى true ويستدعي الدالة المسجّلة `start_listener`. النجاح يرجع رسالة أن المراقبة بدأت. الفشل يرجع `ok: false`.

اختبار `test_arp_spoof_detection` يمرر للكاشف وصفي حزمتين ARP بنفس IP وعنواني MAC مختلفين خلال النافذة، ويتوقع أن يُستدعى منبّه التنبيه. وضع الاستجابة في الاختبار `none` حتى لا يشغّل سكربت VPN.

## 5 رحلة الاستخدام

1. تثبيت `requirements.txt`.
2. `python app.py` يحمّل YAML ويبني التطبيق ويجهّز الكاشفات.
3. لأن `enable_listener` افتراضياً false، السجل يكتب أن المستمع معطّل عبر الإعدادات.
4. المستخدم يفتح الصفحة على المنفذ 5000.
5. بدء المراقبة من الواجهة يستدعي مسار البدء.
6. إن بقي `use_real_capture` خاطئاً، المستمع يدخل `_run_simulation` ويولّد وصفاً كل فترة بين 1 و4 ثوانٍ.
7. كل وصف يمر على كاشف ARP وكاشف ML وتُحدَّث العدادات وقائمة الحركة بحد 200.
8. الإيقاف يستدعي `stop` على المستمع.

إن فُعّل الالتقاط الحقيقي وفشل scapy، المستمع يطبع رسالة الفشل ويعود إلى المحاكاة.

## 6 الوحدات البرمجية

| المسار | الدور |
| --- | --- |
| `app.py` | تحميل الإعداد، إنشاء Flask، خيوط المستمع |
| `web/flask_blueprint.py` | المسارات و`state_registry` |
| `web/templates` و`web/static` | الواجهة |
| `detectors/packet_listener.py` | scapy أو محاكاة |
| `detectors/arp_detector.py` | تعدد MAC لنفس IP |
| `detectors/ml_detector.py` | RandomForest |
| `utils/preprocessing.py` | خط معالجة CSV التدريب |
| `utils/https_forcer.py` | Talisman وشهادات PEM |
| `utils/vpn_manager.py` | تشغيل سكربت محلي حتى 3 محاولات |
| `utils/logger.py` | سجل |
| `config/settings.yaml` | الإعداد |
| `tests/test_arp_simulation.py` | اختبار الكاشف |

يوجد أيضاً `detectors/init.py` و`utils/init.py` إلى جانب `__init__.py`.

## 7 الكيانات

لا جداول قاعدة. الحالة في الذاكرة:

| الكيان | الشكل |
| --- | --- |
| status | `network` وعدادات `packets` و`arp_alerts` و`ml_alerts` |
| alerts | قائمة تنبيهات، الواجهة ترجع آخر 50 |
| traffic | قائمة حركة، آخر 200 في الذاكرة والواجهة |
| settings | قاموس YAML القابل للتحديث جزئياً من API |
| تنبيه ARP | نوع، IP، قائمة MAC، وقت، ثقة 0.9، قائمة إجراءات |
| تنبيه ML | نوع `ML Anomaly`، تفاصيل IP مصدر ووجهة، وقت |

## 8 الصلاحيات

غير موجود في الملفات الحالية على مسارات الويب. بدء المراقبة وإيقافها وتغيير الإعدادات بلا تسجيل دخول.

التقاط scapy الحقيقي قد يطلب صلاحية إدارية على النظام، كما ذكر README السابق.

## 9 الأتمتة

خيط خلفي `PacketListenerThread` عند تفعيل المستمع. الاستجابة بعد تنبيه ARP تستدعي `start_vpn` أو `enable_https_flag` حسب الوضع. لا cron.

المحاكاة حلقة `while` مع `time.sleep` عشوائي بين 1 و4 ثوانٍ إلى أن يُستدعى `stop`.

## 10 التكامل

- scapy عند توفر الاستيراد وتفعيل `use_real_capture`.
- flask-talisman اختيارياً. إن فشل الاستيراد يبقى `Talisman = None` ويكمل التشغيل.
- سكربت VPN: الاسم في الإعداد `vpn_client_windows.bat` بمهلة 60 ثانية. تشغيله حتى 3 محاولات مع انتظار متزايد. ملف bat بهذا الاسم: غير موجود في سرد ملفات المشروع الحالية. عند غيابه ترفع `start_vpn` خطأ ملف غير موجود ويُسجَّل في الكاشف.

## 11 المصطلحات

| المصطلح | المعنى هنا |
| --- | --- |
| response_mode | none أو vpn أو https أو both |
| use_real_capture | التقاط scapy بدل حلقة المحاكاة |
| state_registry | قاموس مشترك بين الخيط والواجهات |
| ML Anomaly | تنبيه عندما تنبؤ النموذج يساوي 1 |
| ARP Spoofing | تسمية التنبيه عند تعدد MAC لنفس IP داخل النافذة |

## 12 الأسئلة الشائعة

| السؤال | الجواب |
| --- | --- |
| هل المراقبة تعمل تلقائياً؟ | الإعداد الافتراضي يعطّل المستمع حتى يُطلب البدء أو يُغيَّر YAML |
| ماذا أرى بدون Npcap أو صلاحيات؟ | المحاكاة إن كان الالتقاط الحقيقي مغلقاً أو فشل |
| هل تُحفظ التنبيهات بعد الإغلاق؟ | القوائم في الذاكرة. الملف الدائم المذكور هو `idsf.log` |
| هل HTTPS يشتغل دائماً؟ | فقط مع الوضع المناسب وملفات PEM تبدأ بمؤشر شهادة ومفتاح صالحين، وإلا HTTP |
| ما إصدار الواجهة البرمجي؟ | `1.0.0` في `/api/system/info` |

## 13 البنية المعمارية

```
المتصفح
   |
   v
Flask :5000  blueprint web
   |
   v
state_registry (ذاكرة)
   ^
   |
خيط PacketListener
   |-- محاكاة أو scapy
   |
   +--> ArpDetector --> تنبيه --> اختياري: سكربت VPN أو علم HTTPS
   +--> MlDetector   --> تنبيه إن كان الصنف 1
   |
   v
idsf.log
```

## 14 التقنيات

| الحزمة | الإصدار في `requirements.txt` |
| --- | --- |
| Flask | 2.2.5 |
| scikit-learn | 1.2.2 |
| pandas | 1.5.3 |
| numpy | 1.23.5 |
| joblib | 1.2.0 |
| pyshark | 0.4.6 |
| scapy | 2.4.5 |
| PyYAML | 6.0 |
| gunicorn | 20.1.0 |
| cryptography | 40.0.2 |
| flask-talisman | 1.0.0 |

استيراد pyshark داخل ملفات الكاشف والمستمع: غير موجود. gunicorn مدرج. Procfile: غير موجود في الملفات الحالية.

الواجهة: قوالب Flask، CSS في `web/static/css/style.css`، JS في `web/static/js/main.js`. README السابق يذكر خط IBM Plex Sans Arabic وأيقونات Font Awesome محلياً.

## 15 شجرة الملفات

```
IDSF/
├── app.py
├── idsf.log
├── requirements.txt
├── README.md
├── config/settings.yaml
├── detectors/
│   ├── arp_detector.py
│   ├── ml_detector.py
│   ├── packet_listener.py
│   ├── __init__.py
│   └── init.py
├── utils/
│   ├── https_forcer.py
│   ├── logger.py
│   ├── preprocessing.py
│   ├── vpn_manager.py
│   ├── __init__.py
│   └── init.py
├── web/
│   ├── flask_blueprint.py
│   ├── templates/index.html
│   ├── templates/settings.html
│   └── static/css و js
├── tests/test_arp_simulation.py
├── certs/     مجلد الشهادات المشار إليه في الإعداد
├── data/      CSV التدريب المشار إليه
└── models/    ملف rf_model.pkl عند أول تدريب ناجح
```

وجود ملفات داخل `certs` و`data` و`models` يعتمد على ما نُسخ مع المجلد. الإعداد يشير إلى `certs/server.crt` و`certs/server.key` و`data/sample_nslkdd.csv` و`models/rf_model.pkl`.

## 16 الواجهة الأمامية

صفحتان: الرئيسية والإعدادات. الجافاسكربت يطلب مسارات الحالة والتنبيهات والحركة والمراقبة. README السابق يصف واجهة داكنة عربية.

## 17 الخادم الخلفي

`create_app` يضبط مجلد القوالب والملفات الثابتة تحت `web/`، ويربط المُسجّل، ويملأ السجل المشترك، ويستدعي `configure_https_policy`، ويسجّل الـ blueprint.

`start_background_services` ينشئ الكاشفين ويمسك دوال البدء والإيقاف.

التشغيل: `app.run(host, port, ssl_context=...)`.

## 18 تدفق الطلب

```
POST /api/monitoring/start
  -> enable_listener = true
  -> start_packet_listener
       -> PacketListener.run
            -> scapy أو _run_simulation
            -> handle_packet
                 -> تصنيف نصي للعرض
                 -> arp_detector.process_packet
                 -> ml_detector.process_packet
```

تصنيف العرض النصي في `classify_packet` يصف النوع والبروتوكول والمنافذ للواجهة فقط.

## 19 قاعدة البيانات

غير موجود في الملفات الحالية.

## 20 نقاط النهاية

| الطريقة | المسار |
| --- | --- |
| GET | `/` |
| GET | `/settings` |
| GET | `/api/status` |
| GET | `/api/alerts` |
| GET | `/api/traffic` |
| GET | `/api/stats` |
| POST | `/api/settings` |
| POST | `/api/monitoring/start` |
| POST | `/api/monitoring/stop` |
| GET | `/api/monitoring/status` |
| GET | `/api/system/info` |
| GET | `/api/health` |

## 21 المصادقة

غير موجود في الملفات الحالية.

## 22 الأمان

السلوك الدفاعي الموجود:

- كشف تغيّر MAC المرتبط بـ IP داخل نافذة زمنية قابلة للضبط، مع تنبيه وسجل.
- نموذج تصنيف يرفع تنبيهاً عند الصنف الإيجابي بعد تحميل أو تدريب محلي.
- فرض رؤوس عبر Talisman عندما يُختار وضع HTTPS ويتوفر المكتبة.
- تشغيل TLS فقط إذا بدأ ملف الشهادة بمؤشر PEM ومؤشر المفتاح موجود، وإلا يبقى HTTP مع تحذير في السجل.
- إيقاف المستمع عند طلب الإيقاف.
- المحاكاة مسار بديل عندما لا يُطلب التقاط حقيقي.

حدود ظاهرة في الكود:

- مسارات التحكم مفتوحة بلا دخول.
- المضيف الافتراضي `0.0.0.0`.
- ميزات التنبؤ في `process_packet` مبنية من طول عنوان IP وطول الوجهة وجزء من الوقت وتجزئة نوع الحزمة ومنفذ مصدر مُطبَّع. هذا مختلف عن أعمدة CSV التدريب التي يمررها `build_preprocessing_pipeline` عند إنشاء النموذج. فشل التحويل يُسجَّل كخطأ تنبؤ.
- `vpn_manager` يشغّل ملفاً محلياً عبر `subprocess` مع `shell=True` لملفات bat.
- pyshark في المتطلبات بلا استخدام في المستمع.

## 23 الإعدادات

ملف `config/settings.yaml`:

| المفتاح | القيمة الحالية |
| --- | --- |
| response_mode | none |
| vpn.script | vpn_client_windows.bat |
| vpn.timeout | 60 |
| https.cert | certs/server.crt |
| https.key | certs/server.key |
| detection.arp.mac_change_threshold | 1 |
| detection.arp.window_seconds | 60 |
| detection.ml.model_path | models/rf_model.pkl |
| detection.ml.data_path | data/sample_nslkdd.csv |
| app.host | 0.0.0.0 |
| app.port | 5000 |
| app.enable_listener | false |
| app.use_real_capture | false |

`POST /api/settings` يحدّث الوضع وأعلام المستمع في الذاكرة. حفظ YAML من هذا المسار: غير موجود في الملفات الحالية.

## 24 التكاملات الخارجية

scapy للالتقاط. Talisman للرؤوس. سكربت VPN محلي إن وُجد الملف. لا خدمة سحابية في الكود.

## 25 المهام والجدولة

خيط المستمع فقط. لا جدولة زمنية.

## 26 الملفات المهمة

`config/settings.yaml` و`idsf.log` وشهادات `certs` إن وُجدت و`models/rf_model.pkl` بعد التدريب و`data/sample_nslkdd.csv` للتدريب الأول.

## 27 السجلات

`utils/logger.py` يكتب إلى `idsf.log` في جذر المشروع. الملف موجود في الجذر. رسائل الكاشف: تحذير عند تنبيه ARP، وخطأ عند فشل VPN أو HTTPS أو التنبؤ.

## 28 التثبيت

```
cd D:\VSCode\Projects\IDSF
pip install -r requirements.txt
python app.py
```

ثم افتح عنوان المضيف والمنفذ من YAML. الافتراضي المنفذ 5000.

README السابق ذكر المسار `C:\Users\UPath\IDSF`. استخدم مسار المجلد الذي يحتوي `app.py` على جهازك.

## 29 دليل التطوير

- المسارات في `web/flask_blueprint.py`.
- لا تضف خطوات هجوم إلى الواجهة. الكاشف يستهلك قاموس `meta` فيه `type` و`src_ip` و`src_mac`.
- اختبار الكاشف الحالي يمرر قاموسين متتاليين ويتأكد من استدعاء التنبيه.
- تدريب ML يحدث داخل `_load_model` إذا غاب ملف joblib.

## 30 النشر

gunicorn في المتطلبات. أمر التشغيل المكتوب في README السابق والكود هو `python app.py`. ربط منصة سحابية: غير موجود في الملفات الحالية.

## 31 النسخ الاحتياطي

انسخ `idsf.log` و`models/rf_model.pkl` و`config/settings.yaml`. التنبيهات الحية تختفي بإعادة التشغيل.

## 32 استكشاف الأخطاء

| العرض | المصدر |
| --- | --- |
| المستمع لا يعمل عند الإقلاع | `enable_listener: false` |
| رجوع للمحاكاة | فشل scapy أو `use_real_capture` false |
| فشل VPN | السكربت غير موجود أو رمز خروج غير صفر أو انتهاء المهلة |
| تشغيل بلا SSL | الشهادة غير موجودة أو ليست PEM |
| خطأ أثناء التنبؤ في السجل | شكل الميزات لا يطابق خط المعالجة المحفوظ |
| فشل بدء المراقبة | `start_listener` أعاد False لأن المستمع ما زال غير مفعّل داخل الإعداد لحظة البناء، أو الاستثناء ابتُلع |

## 33 الاعتماديات

انظر القسم 14.

## 34 القيود

- الحالة في الذاكرة.
- المحاكاة تستخدم عناوين وأرقام منافذ ثابتة في قوائم داخل `_run_simulation` لأغراض العرض المحلي.
- نموذج ML عند التنبؤ الحي لا يستخدم نفس أعمدة ملف العينة حرفياً.
- سكربت VPN المشار إليه غير موجود في سرد الملفات الحالي.
- لا مصادقة.
- مسار README السابق `C:\Users\UPath\IDSF` يختلف عن مسار المجلد الحالي.

## 35 الحالة الحالية

تطبيق Flask مع كاشفين وسجل وواجهة من صفحتين وإعداد YAML يبقي المستمع متوقفاً حتى الطلب. إصدار واجهة المعلومات `1.0.0`.

## 36 القرارات

| القرار | الأثر |
| --- | --- |
| محاكاة بديلة | الواجهة تعمل بلا التقاط |
| عتبة MAC | حساسية التنبيه من YAML |
| Talisman اختياري | غياب المكتبة لا يوقف الإقلاع |
| تجاهل PEM غير الصالح | البقاء على HTTP |
| pytest للاختبار الموجود | أمر README السابق `python -m pytest -q` |

## 37 الاختبار

ملف `tests/test_arp_simulation.py` دالة `test_arp_spoof_detection`. تشغّل بـ pytest بعد تثبيت المتطلبات. الاختبار يتحقق من إطلاق التنبيه فقط، مع `response_mode: none`.

## 38 متطلبات التشغيل

بايثون. README السابق يحدد 3.10.6 على Windows. pip. للالتقاط الحقيقي: scapy وصلاحيات تسمح بالالتقاط. للشهادات: ملفات PEM في `certs` عند اختيار HTTPS.

## 39 سجل التغييرات

رقم الإصدار الظاهر في الكود: `1.0.0` داخل `system_info`. سجل تغييرات بين إصدارات: غير موجود في الملفات الحالية.

## System Overview

واجهة عربية، حالة في الذاكرة، مستمع حزم حقيقي أو محاكى، تنبيه عند تعدد MAC لنفس IP، وتنبيه نموذج عند الصنف 1، مع سجل ملف.

## Quick Reference

| البند | القيمة |
| --- | --- |
| التشغيل | `python app.py` |
| المنفذ | 5000 |
| الإعداد | `config/settings.yaml` |
| السجل | `idsf.log` |
| الإصدار | 1.0.0 |
| الاختبار | `python -m pytest -q` |

## Quick Start

```
cd D:\VSCode\Projects\IDSF
pip install -r requirements.txt
python app.py
```

افتح الصفحة، ثم ابدأ المراقبة من الواجهة. الإعداد الافتراضي يستخدم المحاكاة.

## For Non-Technical Users

الصفحة تعرض حركة وعدادات. زر البدء يشغّل المراقبة. في الوضع الافتراضي الحركة المعروضة مولَّدة داخل البرنامج للتجربة. إذا تكرر عنوان جهاز مختلف لنفس عنوان الشبكة داخل دقيقة، يظهر تنبيه. يمكنك إيقاف المراقبة من الزر المقابل.

## For Developers

أبقِ وصف السلوك عند مستوى الكاشف: مدخلات `meta`، نافذة زمنية، تنبيه، عداد، سجل. تحديث الإعداد من `POST /api/settings` يغيّر الذاكرة فقط. نموذج ML يحتاج محاذاة أعمدة التنبؤ مع خط `preprocessing` إذا أردت تنبؤاً يمر بلا استثناء تحويل.
