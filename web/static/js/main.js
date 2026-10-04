window.IDSF = (function () {
    // وظائف مساعدة بسيطة لواجهة المستخدم بدون أطر عمل
    async function fetchJson(url, opts) {
        const res = await fetch(url, Object.assign({ headers: { 'Content-Type': 'application/json' } }, opts));
        return await res.json();
    }

    async function refreshStatus() {
        try {
            const data = await fetchJson('/api/status');
            const el = document.getElementById('network-status');
            el.textContent = data.network === 'Active' ? 'نشط' : 'خامل';
            const c = (data.counts || {});
            const g = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v ?? 0; };
            g('count-packets', c.packets);
            g('count-arp', c.arp_alerts);
            g('count-ml', c.ml_alerts);

            // تحديث إحصائيات الهيدر
            g('header-packets', c.packets);
            g('header-alerts', (c.arp_alerts || 0) + (c.ml_alerts || 0));
        } catch (e) { /* تجاهل الأخطاء لعرض الواجهة */ }
    }

    function renderAlerts(list) {
        const ul = document.getElementById('alerts-list');
        ul.innerHTML = '';
        list.forEach((a) => {
            const li = document.createElement('li');
            const when = new Date(a.timestamp * 1000).toLocaleString('ar');
            li.innerHTML = `<strong>${a.type}</strong> - <span class="muted">${when}</span>`;
            if ((a.type || '').toLowerCase().includes('arp')) {
                li.classList.add('badge-danger');
            }
            ul.appendChild(li);
        });
    }

    async function refreshAlerts() {
        try {
            const data = await fetchJson('/api/alerts');
            renderAlerts(data || []);
        } catch (e) { /* تجاهل */ }
    }

    async function refreshTraffic() {
        try {
            const data = await fetchJson('/api/traffic');
            const term = document.getElementById('net-terminal');
            if (!term) return;

            const lines = (data || []).map(p => {
                const t = new Date((p.timestamp || Date.now() / 1000) * 1000).toLocaleTimeString('ar');
                const classification = p.classification || `${p.type || 'PKT'} ${p.src_ip || ''} -> ${p.dst_ip || ''}`;
                return `[${t}] ${classification}`;
            });

            if (lines.length === 0) {
                term.textContent = 'لا توجد حركة شبكية - اضغط "بدء المراقبة" لرؤية الحزم الحية';
            } else {
                term.textContent = lines.join('\n');
            }
            term.scrollTop = term.scrollHeight;
        } catch (e) { /* تجاهل */ }
    }

    function bindSettings() {
        const btn = document.getElementById('save-settings');
        if (!btn) return;
        btn.addEventListener('click', async function () {
            const sel = document.querySelector('input[name="response_mode"]:checked');
            const mode = sel ? sel.value : 'none';
            const enableListener = document.getElementById('enable-listener')?.checked || false;
            const realCapture = document.getElementById('real-capture')?.checked || false;

            const payload = {
                response_mode: mode,
                enable_listener: enableListener,
                use_real_capture: realCapture
            };

            await fetchJson('/api/settings', { method: 'POST', body: JSON.stringify(payload) });
            await refreshAlerts();
        });
    }

    function bindMonitoringControls() {
        const startBtn = document.getElementById('start-monitoring');
        const stopBtn = document.getElementById('stop-monitoring');

        if (!startBtn || !stopBtn) return;

        startBtn.addEventListener('click', async function () {
            try {
                const result = await fetchJson('/api/monitoring/start', { method: 'POST' });
                if (result.ok) {
                    startBtn.style.display = 'none';
                    stopBtn.style.display = 'inline-block';
                    document.getElementById('network-status').textContent = 'نشط - مراقبة';
                    alert('تم بدء المراقبة! الحركة الشبكية تظهر الآن في الطرفية');
                } else {
                    alert('فشل في بدء المراقبة: ' + (result.message || 'خطأ غير معروف'));
                }
            } catch (e) {
                alert('فشل في بدء المراقبة: ' + (e.message || 'خطأ غير معروف'));
            }
        });

        stopBtn.addEventListener('click', async function () {
            try {
                const result = await fetchJson('/api/monitoring/stop', { method: 'POST' });
                if (result.ok) {
                    stopBtn.style.display = 'none';
                    startBtn.style.display = 'inline-block';
                    document.getElementById('network-status').textContent = 'متوقف';
                    alert('تم إيقاف المراقبة');
                } else {
                    alert('فشل في إيقاف المراقبة: ' + (result.message || 'خطأ غير معروف'));
                }
            } catch (e) {
                alert('فشل في إيقاف المراقبة: ' + (e.message || 'خطأ غير معروف'));
            }
        });
    }

    async function checkMonitoringStatus() {
        try {
            const data = await fetchJson('/api/monitoring/status');
            const startBtn = document.getElementById('start-monitoring');
            const stopBtn = document.getElementById('stop-monitoring');

            if (data.active) {
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
            } else {
                stopBtn.style.display = 'none';
                startBtn.style.display = 'inline-block';
            }
        } catch (e) {
            // تجاهل الأخطاء
        }
    }

    async function init() {
        bindSettings();
        bindMonitoringControls();
        await checkMonitoringStatus();
        await refreshStatus();
        await refreshAlerts();
        setInterval(refreshStatus, 3000);
        setInterval(refreshAlerts, 5000);
        setInterval(refreshTraffic, 1000);  // تحديث أسرع للطرفية
        setInterval(checkMonitoringStatus, 3000);
    }

    return { init };
})();


