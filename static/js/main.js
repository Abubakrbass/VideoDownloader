// Глобальные настройки и переводы
window.appSettings = { snow: true, sound: true, toasts: true, lang: 'ru', relax: false };
window.translations = {
    ru: {
        title: 'Скачать Видео', searchPlaceholder: 'Вставьте ссылку YouTube...', searchBtn: 'Найти', howTo: '<i class="bi bi-question-circle"></i> Как использовать?',
        settingsTitle: '<i class="bi bi-gear-fill"></i> Настройки', snow: '❄️ Снегопад', sound: '🔊 Звуки', toasts: '🔔 Уведомления', relax: '🌊 Релакс (Дождь)', clearCache: '<i class="bi bi-trash"></i> Очистить кэш',
        footerAbout: 'О нас', footerPrivacy: 'Конфиденциальность', footerTerms: 'Условия использования', footerFeedback: 'Обратная связь', footerCopyright: '&copy; 2025 Video Downloader',
        cookieText: '🍪 <b>Мы используем файлы cookie.</b><br>Они нужны для работы сайта (сохранение темы, вход в аккаунт) и улучшения вашего опыта.', cookieAccept: 'Принять', cookieReject: 'Отклонить все',
        howToContent: '<ol class="mb-0 ps-3"><li>Скопируйте ссылку на видео.</li><li>Вставьте её в поле (поиск начнется автоматически).</li><li>Выберите качество и скачайте.</li></ol><div class="mt-2 text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill"></i> Скачивание видео 18+ запрещено!</div><div class="mt-2"><i class="bi bi-info-circle-fill text-primary"></i> <b>Важно:</b> История скачиваний сохраняется только если вы вошли в аккаунт.</div>',
        lblDuration: 'Длительность:', lblQuality: 'Выберите качество:', btnReload: 'Скачать другое видео',
        historyModalTitle: '📂 Мои скачанные видео', notifModalTitle: '🔔 Уведомления',
        authLogin: 'Вход', authRegister: 'Регистрация',
        historyEmpty: 'История пуста', noNotifications: 'Нет уведомлений', loading: 'Загрузка...', errorLoad: 'Ошибка загрузки',
        clearHistoryConfirm: 'Вы уверены, что хотите очистить всю историю скачиваний?', deleteNotifConfirm: 'Удалить уведомление из истории?',
        btnDownload: 'Сохранить файл', btnShare: 'Поделиться', btnGetPremium: 'Купить Premium', btnPremiumActive: 'Premium Активен',
        qualityBest: 'Лучшее (MP4)', quality1080: '1080p (MP4)', quality720: '720p (MP4)', qualityAudio: 'Аудио (MP3)',
        statusDownloading: 'Скачивание...', statusProcessing: 'Обработка и склеивание...', statusFinished: 'Готово!', statusError: 'Ошибка при скачивании: ',
        searching: 'Поиск...', btnYes: 'Да', btnNo: 'Нет', resetSettingsConfirm: 'Сбросить все настройки и перезагрузить?',
        currency: '₽', priceMonth: '199', priceYear: '500',
        // Premium Cards
        planFree: 'FREE', planMonth: 'МЕСЯЦ', planYear: 'ГОД', planFreeDesc: 'Базовый', planMonthDesc: 'На 1 месяц', planYearDesc: 'На 1 год',
        btnCurrent: 'Текущий план', btnBuy: 'Купить', badgeBest: 'ВЫГОДНО',
        featAds: 'Реклама на сайте', featLimit: 'Лимит 5 видео в день', featSpeed: 'Ограниченная скорость', featNoPlaylist: 'Нет скачивания плейлистов', featNoQuality: 'Нет качества 1080p/4K',
        featNoAds: 'Отключение всей рекламы', featUnlimited: 'Безлимитное скачивание', featMaxSpeed: 'Максимальная скорость', featPlaylist: 'Скачивание плейлистов',
        featAll: 'Всё включено', featSave: 'Экономия до 80%', featSupport: 'Приоритетная поддержка',
        // New translations
        limitLabel: 'Лимит на сегодня:', slowSearch: 'Медленный поиск?', buyPremFast: 'Купите Premium для ускорения!',
        authRequiredTitle: 'Требуется вход', authRequiredText: 'Для покупки Premium необходимо войти или зарегистрироваться.'
    },
    en: {
        title: 'Download Video', searchPlaceholder: 'Paste YouTube link...', searchBtn: 'Search', howTo: '<i class="bi bi-question-circle"></i> How to use?',
        settingsTitle: '<i class="bi bi-gear-fill"></i> Settings', snow: '❄️ Snowfall', sound: '🔊 Sounds', toasts: '🔔 Notifications', relax: '🌊 Relax (Rain)', clearCache: '<i class="bi bi-trash"></i> Clear Cache',
        footerAbout: 'About us', footerPrivacy: 'Privacy', footerTerms: 'Terms of Use', footerFeedback: 'Feedback', footerCopyright: '&copy; 2025 Video Downloader',
        cookieText: '🍪 <b>We use cookies.</b><br>They are necessary for the site to work (saving theme, login) and improving your experience.', cookieAccept: 'Accept', cookieReject: 'Reject all',
        howToContent: '<ol class="mb-0 ps-3"><li>Copy the video link.</li><li>Paste it into the field (search starts automatically).</li><li>Select quality and download.</li></ol><div class="mt-2 text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill"></i> Downloading 18+ video is prohibited!</div><div class="mt-2"><i class="bi bi-info-circle-fill text-primary"></i> <b>Important:</b> Download history is saved only if you are logged in.</div>',
        lblDuration: 'Duration:', lblQuality: 'Select quality:', btnReload: 'Download another video',
        historyModalTitle: '📂 My downloads', notifModalTitle: '🔔 Notifications',
        authLogin: 'Login', authRegister: 'Register',
        historyEmpty: 'History is empty', noNotifications: 'No notifications', loading: 'Loading...', errorLoad: 'Error loading',
        clearHistoryConfirm: 'Are you sure you want to clear download history?', deleteNotifConfirm: 'Delete notification from history?',
        btnDownload: 'Save file', btnShare: 'Share', btnGetPremium: 'Get Premium', btnPremiumActive: 'Premium Active',
        qualityBest: 'Best (MP4)', quality1080: '1080p (MP4)', quality720: '720p (MP4)', qualityAudio: 'Audio (MP3)',
        statusDownloading: 'Downloading...', statusProcessing: 'Processing and merging...', statusFinished: 'Done!', statusError: 'Download error: ',
        searching: 'Searching...', btnYes: 'Yes', btnNo: 'No', resetSettingsConfirm: 'Reset all settings and reload?',
        currency: '$', priceMonth: '3', priceYear: '6',
        // Premium Cards
        planFree: 'FREE', planMonth: 'MONTH', planYear: 'YEAR', planFreeDesc: 'Basic', planMonthDesc: 'For 1 month', planYearDesc: 'For 1 year',
        btnCurrent: 'Current plan', btnBuy: 'Buy', badgeBest: 'BEST VALUE',
        featAds: 'Ads on site', featLimit: 'Limit 5 videos/day', featSpeed: 'Limited speed', featNoPlaylist: 'No playlist download', featNoQuality: 'No 1080p/4K',
        featNoAds: 'No ads', featUnlimited: 'Unlimited downloads', featMaxSpeed: 'Max speed', featPlaylist: 'Playlist download',
        featAll: 'All included', featSave: 'Save up to 80%', featSupport: 'Priority support',
        // New translations
        limitLabel: 'Limit for today:', slowSearch: 'Slow search?', buyPremFast: 'Buy Premium to speed up!',
        authRequiredTitle: 'Login required', authRequiredText: 'You need to login or register to buy Premium.'
    },
    kg: {
        title: 'Видео Жүктөө', searchPlaceholder: 'YouTube шилтемесин коюңуз...', searchBtn: 'Издөө', howTo: '<i class="bi bi-question-circle"></i> Кантип колдонуу керек?',
        settingsTitle: '<i class="bi bi-gear-fill"></i> Төндөөлөр', snow: '❄️ Кар жаашы', sound: '🔊 Үндөр', toasts: '🔔 Билдирүүлөр', relax: '🌊 Релакс (Жамгыр)', clearCache: '<i class="bi bi-trash"></i> Кэшти тазалоо',
        footerAbout: 'Биз жөнүндө', footerPrivacy: 'Купуялуулук', footerTerms: 'Колдонуу шарттары', footerFeedback: 'Байланыш', footerCopyright: '&copy; 2025 Video Downloader',
        cookieText: '🍪 <b>Биз cookie файлдарын колдонобуз.</b><br>Алар сайттын иштеши үчүн керек (теманы сактоо, аккаунтка кирүү).', cookieAccept: 'Кабыл алуу', cookieReject: 'Баарын четке кагуу',
        howToContent: '<ol class="mb-0 ps-3"><li>Видеонун шилтемесин көчүрүңүз.</li><li>Аны талаага коюңуз (издөө автоматтык түрдө башталат).</li><li>Сапатты тандап, жүктөп алыңыз.</li></ol><div class="mt-2 text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill"></i> 18+ видеолорду жүктөөгө тыюу салынат!</div>',
        lblDuration: 'Узактыгы:', lblQuality: 'Сапатты тандаңыз:', btnReload: 'Башка видео жүктөө',
        historyModalTitle: '📂 Менин жүктөдүүлөрүм', notifModalTitle: '🔔 Билдирүүлөр',
        authLogin: 'Кирүү', authRegister: 'Каттоо',
        historyEmpty: 'Тарых бош', noNotifications: 'Билдирүүлөр жок', loading: 'Жүктөлүүдө...', errorLoad: 'Жүктөө катасы',
        clearHistoryConfirm: 'Сиз жүктөө тарыхын тазалоону каалайсызбы?', deleteNotifConfirm: 'Билдирүүнү тарыхтан өчүрүү?',
        btnDownload: 'Файлды сактоо', btnShare: 'Бөлүшүү', btnGetPremium: 'Premium алуу', btnPremiumActive: 'Premium Активдүү',
        qualityBest: 'Мыкты (MP4)', quality1080: '1080p (MP4)', quality720: '720p (MP4)', qualityAudio: 'Аудио (MP3)',
        statusDownloading: 'Жүктөлүүдө...', statusProcessing: 'Иштеп чыгуу жана бириктирүү...', statusFinished: 'Даяр!', statusError: 'Жүктөө катасы: ',
        searching: 'Издөө...', btnYes: 'Ооба', btnNo: 'Жок', resetSettingsConfirm: 'Бардык жөндөөлөрдү тазалап, кайра жүктөйбүзбү?',
        currency: 'сом', priceMonth: '200', priceYear: '500',
        // Premium Cards
        planFree: 'АКЫСЫЗ', planMonth: 'АЙ', planYear: 'ЖЫЛ', planFreeDesc: 'Жөнөкөй', planMonthDesc: '1 айга', planYearDesc: '1 жылга',
        btnCurrent: 'Учурдагы план', btnBuy: 'Сатып алуу', badgeBest: 'ПАЙДАЛУУ',
        featAds: 'Сайттагы жарнама', featLimit: 'Күнүнө 5 видео чектөө', featSpeed: 'Чектелген ылдамдык', featNoPlaylist: 'Плейлисттерди жүктөө жок', featNoQuality: '1080p/4K сапаты жок',
        featNoAds: 'Жарнамасыз', featUnlimited: 'Чексиз жүктөөлөр', featMaxSpeed: 'Максималдуу ылдамдык', featPlaylist: 'Плейлисттерди толук жүктөө',
        featAll: 'Баары камтылган', featSave: '80% га чейин үнөмдөө', featSupport: 'Биринчи кезектеги колдоо',
        // New translations
        limitLabel: 'Бүгүнкү чек:', slowSearch: 'Жай издөөбү?', buyPremFast: 'Тезирээк кылуу үчүн Premium алыңыз!',
        authRequiredTitle: 'Кирүү керек', authRequiredText: 'Premium сатып алуу үчүн кириңиз же катталыңыз.'
    }
};

// Глобальные переменные
let lastAuthData = { isAuth: false, username: '', avatarUrl: '', isPremium: false, isAdmin: false };
let authCheckPromise = null;
let currentTaskId = null;
let progressInterval = null;
let relaxCtx = null, relaxGain = null, relaxFilter = null;

// --- УТИЛИТЫ ---
const Utils = {
    getCsrfToken: () => document.querySelector('meta[name="csrf-token"]')?.getAttribute('content'),
    
    // Безопасный метод для создания элементов (защита от XSS)
    createElement: (tag, classes, text) => {
        const el = document.createElement(tag);
        if (classes) el.className = classes;
        if (text) el.textContent = text;
        return el;
    }
};

// --- ЗВУК РЕЛАКС ---
function toggleRelaxSound(enable) {
    if (enable) {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            if (!relaxCtx) relaxCtx = new AudioContext();
            if (relaxCtx.state === 'suspended') relaxCtx.resume().catch(() => {});
            if (!relaxGain) {
                const bufferSize = 2 * relaxCtx.sampleRate;
                const buffer = relaxCtx.createBuffer(1, bufferSize, relaxCtx.sampleRate);
                const output = buffer.getChannelData(0);
                let lastOut = 0;
                for (let i = 0; i < bufferSize; i++) {
                    const white = Math.random() * 2 - 1;
                    output[i] = (lastOut + (0.02 * white)) / 1.02;
                    lastOut = output[i];
                    output[i] *= 3.5;
                }
                const noise = relaxCtx.createBufferSource();
                noise.buffer = buffer;
                noise.loop = true;
                relaxGain = relaxCtx.createGain();
                relaxGain.gain.value = 0;
                relaxFilter = relaxCtx.createBiquadFilter();
                relaxFilter.type = 'lowpass';
                relaxFilter.frequency.value = 400;
                noise.connect(relaxFilter);
                relaxFilter.connect(relaxGain);
                relaxGain.connect(relaxCtx.destination);
                noise.start(0);
            }
            relaxGain.gain.setTargetAtTime(0.15, relaxCtx.currentTime, 0.5);
        } catch (e) { console.error(e); }
    } else {
        if (relaxGain && relaxCtx) {
            try {
                relaxGain.gain.setTargetAtTime(0, relaxCtx.currentTime, 0.5);
                setTimeout(() => { if (relaxCtx && relaxCtx.state === 'running') relaxCtx.suspend(); }, 500);
            } catch (e) {}
        }
    }
}

// --- НАСТРОЙКИ ---
window.loadSettings = function() {
    const saved = localStorage.getItem('appSettings');
    if (saved) {
        window.appSettings = { ...window.appSettings, ...JSON.parse(saved) };
    } else {
        const browserLang = navigator.language || navigator.userLanguage;
        if (browserLang.startsWith('ru')) window.appSettings.lang = 'ru';
        else if (browserLang.startsWith('ky') || browserLang.startsWith('kg')) window.appSettings.lang = 'kg';
        else window.appSettings.lang = 'en';
    }
    
    const setCheck = (id, val) => { const el = document.getElementById(id); if(el) el.checked = val; };
    const setVal = (id, val) => { const el = document.getElementById(id); if(el) el.value = val; };
    
    setCheck('settingSnow', window.appSettings.snow);
    setCheck('settingSound', window.appSettings.sound);
    setCheck('settingToasts', window.appSettings.toasts);
    setCheck('settingRelax', window.appSettings.relax);
    setVal('settingLang', window.appSettings.lang || 'ru');
    
    applySettings();
}

window.saveSettings = function() {
    const getCheck = (id) => { const el = document.getElementById(id); return el ? el.checked : false; };
    const getVal = (id) => { const el = document.getElementById(id); return el ? el.value : 'ru'; };

    window.appSettings.snow = getCheck('settingSnow');
    window.appSettings.sound = getCheck('settingSound');
    window.appSettings.toasts = getCheck('settingToasts');
    window.appSettings.relax = getCheck('settingRelax');
    window.appSettings.lang = getVal('settingLang');
    
    localStorage.setItem('appSettings', JSON.stringify(window.appSettings));
    applySettings();
}

function applySettings() {
    const pile = document.querySelector('.snow-pile');
    const container = document.getElementById('snow-container');
    if (window.appSettings.snow) {
        if (pile) pile.style.display = 'block';
    } else {
        if (pile) pile.style.display = 'none';
        if (container) container.innerHTML = '';
    }

    const t = window.translations[window.appSettings.lang];
    if (t) {
        const elementsToTranslate = {
            'mainTitle': 'title', 'urlInput': 'searchPlaceholder', 'searchBtn': 'searchBtn', 'howToLink': 'howTo',
            'settingsTitle': 'settingsTitle', 'lblSnow': 'snow', 'lblSound': 'sound', 'lblToasts': 'toasts', 'lblRelax': 'relax', 'btnClearCache': 'clearCache',
            'footerAbout': 'footerAbout', 'footerPrivacy': 'footerPrivacy', 'footerTerms': 'footerTerms', 'footerFeedback': 'footerFeedback', 'footerCopyright': 'footerCopyright',
            'cookieText': 'cookieText', 'cookieAccept': 'cookieAccept', 'cookieReject': 'cookieReject',
            'howToContent': 'howToContent', 'lblDuration': 'lblDuration', 'lblQuality': 'lblQuality', 'btnReload': 'btnReload',
            'historyModalTitle': 'historyModalTitle', 'notifModalTitle': 'notifModalTitle',
            'txtLimitLabel': 'limitLabel', 'txtSlowSearch': 'slowSearch', 'lnkBuyPremFast': 'buyPremFast'
        };
        for (const id in elementsToTranslate) {
            const el = document.getElementById(id);
            if (el) {
                const key = elementsToTranslate[id];
                if (id === 'urlInput') el.placeholder = t[key];
                else el.innerHTML = t[key];
            }
        }
        
        // Обновляем кнопки скачивания и поделиться
        if(document.getElementById('downloadBtn')) document.getElementById('downloadBtn').innerHTML = `<i class="bi bi-download"></i> ${t.btnDownload}`;
        if(document.getElementById('shareBtn')) document.getElementById('shareBtn').innerHTML = `<i class="bi bi-share"></i> ${t.btnShare}`;
        
        // Обновляем кнопку Premium в шапке
        const premBtn = document.getElementById('topBarPremiumBtn');
        if (premBtn) {
            premBtn.innerHTML = `<i class="bi bi-gem"></i> ${lastAuthData.isPremium ? t.btnPremiumActive : t.btnGetPremium}`;
        }

        // Обновление цен на странице Premium
        const priceMonth = document.getElementById('price-month');
        const priceYear = document.getElementById('price-year');
        if (priceMonth) priceMonth.innerText = t.priceMonth;
        if (priceYear) priceYear.innerText = t.priceYear;
        const currencySymbols = document.querySelectorAll('.currency-symbol');
        currencySymbols.forEach(el => el.innerText = t.currency);

        // Перевод карточек Premium
        const mapId = {
            't-planFree': 'planFree', 't-planMonth': 'planMonth', 't-planYear': 'planYear',
            't-planFreeDesc': 'planFreeDesc', 't-planMonthDesc': 'planMonthDesc', 't-planYearDesc': 'planYearDesc',
            't-btnCurrent': 'btnCurrent', 't-badgeBest': 'badgeBest',
            't-featAds': 'featAds', 't-featLimit': 'featLimit', 't-featSpeed': 'featSpeed', 't-featNoPlaylist': 'featNoPlaylist', 't-featNoQuality': 'featNoQuality',
            't-featNoAds': 'featNoAds', 't-featUnlimited': 'featUnlimited', 't-featMaxSpeed': 'featMaxSpeed', 't-featPlaylist': 'featPlaylist',
            't-featAll': 'featAll', 't-featSave': 'featSave', 't-featSupport': 'featSupport'
        };
        for (const [id, key] of Object.entries(mapId)) {
            const el = document.getElementById(id);
            if (el) el.innerText = t[key];
        }
        document.querySelectorAll('.t-btnBuy').forEach(btn => btn.innerText = t.btnBuy);
    }
    toggleRelaxSound(window.appSettings.relax);
    updateAuthUI(lastAuthData.isAuth, lastAuthData.username, lastAuthData.avatarUrl, lastAuthData.isPremium);
}

window.clearCache = function() {
    const t = window.translations[window.appSettings.lang] || window.translations['ru'];
    
    Swal.fire({
        title: t.settingsTitle,
        text: t.resetSettingsConfirm,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: t.btnYes,
        cancelButtonText: t.btnNo
    }).then((result) => {
        if (result.isConfirmed) {
            localStorage.clear();
            location.reload(true);
        }
    });
}

// --- АВТОРИЗАЦИЯ (переделано для возврата Promise и предотвращения дублирования запросов) ---
async function checkAuth() {
    if (authCheckPromise) {
        return authCheckPromise; // Если запрос уже выполняется, возвращаем существующий Promise
    }

    authCheckPromise = (async () => {
        try {
            const res = await fetch('/check_auth');
            const data = await res.json();
            lastAuthData = { isAuth: data.authenticated, username: data.username, avatarUrl: data.avatar_url, isPremium: data.is_premium, isAdmin: data.is_admin };
            updateAuthUI(data.authenticated, data.username, data.avatar_url, data.is_premium, data.is_admin);
            return data;
        } catch(e) {
            console.error("Ошибка проверки авторизации:", e);
            lastAuthData = { isAuth: false, username: '', avatarUrl: '', isPremium: false, isAdmin: false }; // Сброс при ошибке
            return { authenticated: false };
        } finally {
            authCheckPromise = null; // Сбрасываем Promise после его выполнения/отклонения
        }
    })();
    return authCheckPromise;
}
window.checkAuth = checkAuth;

function updateAuthUI(isAuth, username, avatarUrl, isPremium, isAdmin) {
    const t = window.translations[window.appSettings.lang] || window.translations['ru'];
    const container = document.getElementById('authSection');
    if (!container) return;

    // Обновляем текст кнопки Premium в шапке
    const premBtn = document.getElementById('topBarPremiumBtn');
    if (premBtn) {
        premBtn.innerHTML = `<i class="bi bi-gem"></i> ${isPremium ? t.btnPremiumActive : t.btnGetPremium}`;
    }

    if (isAuth) {
        const imgUrl = avatarUrl || 'https://via.placeholder.com/40';
        const avatarHtml = `<a href="/profile"><img src="${imgUrl}" alt="Avatar" class="rounded-circle border border-2 border-light avatar-online" style="width: 40px; height: 40px; object-fit: cover;"></a>`;
        const adminBadge = isAdmin ? '<div class="badge bg-info text-dark mt-1 shadow-sm" style="font-size: 0.6rem; padding: 2px 6px; line-height: 1;"><i class="bi bi-shield-lock"></i> ADMIN</div>' : '';
        // Показываем "PREMIUM" только если это платный премиум, а не админ
        const premiumBadge = (isPremium && !isAdmin) ? '<div class="badge bg-warning text-dark mt-1 shadow-sm" style="font-size: 0.6rem; padding: 2px 6px; line-height: 1;"><i class="bi bi-gem"></i> PREMIUM</div>' : '';
        
        container.innerHTML = `
            <div class="d-flex gap-2 me-3 align-items-center border-end pe-3 border-secondary">
                <button class="btn btn-sm btn-dark rounded-circle position-relative shadow-sm" style="width: 32px; height: 32px; padding: 0;" onclick="loadNotificationHistory()" title="Уведомления">
                    <i class="bi bi-bell-fill"></i>
                    <span id="notifBadge" class="position-absolute top-0 start-100 translate-middle p-1 bg-danger border border-light rounded-circle" style="display: none;"></span>
                </button>
                <button class="btn btn-sm btn-dark rounded-circle shadow-sm" style="width: 32px; height: 32px; padding: 0;" onclick="loadHistory()" title="История скачиваний"><i class="bi bi-folder2-open"></i></button>
                <button class="btn btn-sm btn-danger rounded-circle shadow-sm" style="width: 32px; height: 32px; padding: 0;" onclick="logout()" title="Выход"><i class="bi bi-box-arrow-right"></i></button>
            </div>
            <div class="d-flex flex-column align-items-center justify-content-center me-3" style="line-height: 1.1; height: 40px;">
                <a href="/profile" class="fw-bold text-decoration-none text-white small" style="text-shadow: 0 0 5px rgba(0,0,0,0.5);">${username}</a>
                ${adminBadge || premiumBadge}
            </div>
            ${avatarHtml}
        `;
    } else {
        container.innerHTML = `
            <a href="/login_page" class="btn btn-sm btn-outline-primary">${t.authLogin}</a>
            <a href="/register_page" class="btn btn-sm btn-primary">${t.authRegister}</a>
        `;
    }
}

window.logout = async function() {
    await fetch('/logout');
    lastAuthData = { isAuth: false, username: '', avatarUrl: '', isPremium: false };
    updateAuthUI(false);
    location.reload();
}

// --- ИСТОРИЯ И УВЕДОМЛЕНИЯ ---
window.loadHistory = async function() {
    const el = document.getElementById('historyModal');
    if(!el) return;
    const modal = bootstrap.Modal.getOrCreateInstance(el);
    modal.show();
    
    const t = window.translations[window.appSettings.lang] || window.translations['ru'];
    const list = document.getElementById('historyList');
    if(list) list.innerHTML = `<div class="text-center p-3">${t.loading}</div>`;
    
    try {
        const res = await fetch('/my_history');
        if (res.status === 401) return showToast('Сначала войдите в аккаунт', true);
        const data = await res.json();
        if(list) {
            if (data.length === 0) {
                list.innerHTML = `<div class="text-center p-3 text-muted">${t.historyEmpty}</div>`;
                return;
            }
            list.innerHTML = '';
            data.forEach(item => {
                const div = document.createElement('a');
                div.className = 'list-group-item list-group-item-action';
                div.innerHTML = `
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1 text-truncate" style="max-width: 70%;">${item.title}</h6>
                        <small class="text-muted">${new Date(item.date).toLocaleDateString()}</small>
                    </div>
                    <small class="text-muted text-truncate d-block">${item.url}</small>
                `;
                div.onclick = () => {
                    const urlInput = document.getElementById('urlInput');
                    if (urlInput && typeof getInfo === 'function') {
                        urlInput.value = item.url;
                        modal.hide();
                        getInfo();
                    }
                };
                list.appendChild(div);
            });
        }
    } catch (e) {
        if(list) list.innerHTML = `<div class="text-danger p-3">${t.errorLoad}</div>`;
    }
}

window.clearHistory = async function() {
    const t = window.translations[window.appSettings.lang] || window.translations['ru'];
    
    Swal.fire({
        title: t.historyModalTitle,
        text: t.clearHistoryConfirm,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: t.btnYes,
        cancelButtonText: t.btnNo
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                const res = await fetch('/clear_history', { 
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': Utils.getCsrfToken()
                    }
                });
                const data = await res.json();
                if (data.success) loadHistory();
                else Swal.fire('Ошибка', 'Не удалось очистить историю', 'error');
            } catch (e) { Swal.fire('Ошибка', 'Ошибка сети', 'error'); }
        }
    });
}

window.loadNotificationHistory = async function() {
    const el = document.getElementById('notificationHistoryModal');
    if(!el) return;
    const modal = bootstrap.Modal.getOrCreateInstance(el);
    modal.show();
    
    const t = window.translations[window.appSettings.lang] || window.translations['ru'];
    const list = document.getElementById('notificationList');
    if(list) list.innerHTML = `<div class="text-center p-3">${t.loading}</div>`;
    
    fetch('/mark_notifications_read', { 
        method: 'POST',
        headers: {
            'X-CSRFToken': Utils.getCsrfToken()
        }
    });
    const badge = document.getElementById('notifBadge');
    if (badge) badge.style.display = 'none';
    
    try {
        const res = await fetch('/notification_history');
        const data = await res.json();
        if(list) {
            if (data.length === 0) {
                list.innerHTML = `<div class="text-center p-3 text-muted">${t.noNotifications}</div>`;
                return;
            }
            list.innerHTML = '';
            data.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'list-group-item';

                const headerDiv = document.createElement('div');
                headerDiv.className = 'd-flex w-100 justify-content-between align-items-center';

                const dateSmall = document.createElement('small');
                dateSmall.className = 'text-muted';
                const date = new Date(item.date + 'Z').toLocaleString();
                dateSmall.textContent = date;

                const deleteButton = document.createElement('button');
                deleteButton.className = 'btn btn-sm btn-link text-danger p-0';
                deleteButton.innerHTML = '<i class="bi bi-x-lg"></i>';
                deleteButton.onclick = () => deleteNotification(item.id, deleteButton);

                const messageP = document.createElement('p');
                messageP.className = 'mb-1 pe-3';
                messageP.textContent = item.message;

                headerDiv.appendChild(dateSmall);
                headerDiv.appendChild(deleteButton);
                itemDiv.appendChild(headerDiv);
                itemDiv.appendChild(messageP);
                list.appendChild(itemDiv);
            });
        }
    } catch (e) {
        if(list) list.innerHTML = `<div class="text-danger p-3">${t.errorLoad}</div>`;
    }
}

window.deleteNotification = async function(id, btn) {
    const t = window.translations[window.appSettings.lang] || window.translations['ru'];
    
    Swal.fire({
        title: t.notifModalTitle,
        text: t.deleteNotifConfirm,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: t.btnYes,
        cancelButtonText: t.btnNo
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                await fetch('/hide_notification', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Utils.getCsrfToken()
                    },
                    body: JSON.stringify({ id })
                });
                const item = btn.closest('.list-group-item');
                item.remove();
                const list = document.getElementById('notificationList');
                if (list && list.children.length === 0) {
                    list.innerHTML = `<div class="text-center p-3 text-muted">${t.noNotifications}</div>`;
                }
            } catch (e) { Swal.fire('Ошибка', 'Не удалось удалить', 'error'); }
        }
    });
}

// --- TOASTS & COOKIES ---
window.showToast = function(message, isError = false) {
    if (!window.appSettings.toasts && !isError) return;
    const toastEl = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastBody');
    if(toastEl && toastBody) {
        toastEl.className = isError ? 'toast align-items-center text-bg-danger border-0' : 'toast align-items-center text-bg-primary border-0';
        toastBody.innerText = message;
        const toast = bootstrap.Toast.getOrCreateInstance(toastEl);
        toast.show();
    }
}

window.acceptCookies = function() {
    localStorage.setItem('cookieConsent', 'accepted');
    const banner = document.getElementById('cookie-banner');
    if(banner) banner.style.display = 'none';
}
window.rejectCookies = function() {
    localStorage.setItem('cookieConsent', 'rejected');
    const banner = document.getElementById('cookie-banner');
    if(banner) banner.style.display = 'none';
}

// --- SNOW ---
const snowContainer = document.getElementById('snow-container');
function createSnowflake(isInit = false) {
    if (!window.appSettings.snow || !snowContainer) return;
    const snowflake = document.createElement('div');
    snowflake.classList.add('snowflake');
    snowflake.style.left = Math.random() * 100 + 'vw';
    snowflake.style.opacity = Math.random() * 0.6 + 0.4;
    const size = Math.random() * 6 + 3 + 'px';
    snowflake.style.width = size;
    snowflake.style.height = size;
    const duration = Math.random() * 5 + 5 + 's';
    snowflake.style.animationDuration = duration;
    if (isInit) snowflake.style.top = Math.random() * 100 + 'vh';
    snowContainer.appendChild(snowflake);
    setTimeout(() => snowflake.remove(), parseFloat(duration) * 1000);
}

// --- WEBSOCKETS ---
try {
    const socket = io();
    socket.on('connect', () => {
        checkUnreadStatus();
    });
    socket.on('new_notification', (data) => {
        showToast('📢 ' + data.message);
        const badge = document.getElementById('notifBadge');
        if (badge) badge.style.display = 'block';
    });
} catch(e) { console.log('Socket.io not available'); }

async function checkUnreadStatus() {
    try {
        const res = await fetch('/check_notifications?last_id=0');
        const data = await res.json();
        const badge = document.getElementById('notifBadge');
        if (badge) {
            if (data.unread_count > 0) badge.style.display = 'block';
            else badge.style.display = 'none';
        }
    } catch (e) {}
}

// --- ФУНКЦИИ ГЛАВНОЙ СТРАНИЦЫ ---
window.validateUrl = function() {
    const url = document.getElementById('urlInput').value.trim();
    const btn = document.getElementById('searchBtn');
    // Проверка: ссылка должна начинаться с http:// или https:// и содержать точку
    const isValid = /^https?:\/\/.+\..+/.test(url);
    btn.disabled = !isValid;
    return isValid;
}

// --- МЕНЕДЖЕР ЗАГРУЗОК (Refactored) ---
const VideoDownloader = {
    currentTaskId: null,
    progressInterval: null,

    async getInfo() {
        const url = document.getElementById('urlInput').value;
        if (!url) return showToast('Введите ссылку!', true);

        this.resetUI(true); // Скрыть старые результаты

        const btn = document.getElementById('searchBtn');
        const t = window.translations[window.appSettings.lang] || window.translations['ru'];
        const originalText = t.searchBtn;
        
        btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${t.searching}`;
        btn.disabled = true;
        
        // Показываем сообщение о Premium при поиске
        const searchMsg = document.getElementById('searchMessage');
        if (searchMsg && !lastAuthData.isPremium) {
            searchMsg.style.display = 'block';
        }

        try {
            const formData = new FormData();
            formData.append('url', url);

            const response = await fetch('/get_info', { 
                method: 'POST', 
                body: formData,
                headers: { 'X-CSRFToken': Utils.getCsrfToken() }
            });
            const data = await response.json();

            if (response.ok) {
                // Если не премиум, показываем рекламу
                if (!lastAuthData.isPremium) {
                    this.showAdOverlay(() => this.renderInfo(data, url, t));
                } else {
                    this.renderInfo(data, url, t);
                }
            } else {
                showToast('Ошибка: ' + data.error, true);
            }
        } catch (e) {
            showToast('Ошибка соединения: ' + e, true);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
            if (searchMsg) setTimeout(() => { searchMsg.style.display = 'none'; }, 5000); // Скрыть через 5 сек
        }
    },

    // Логика показа рекламы
    showAdOverlay(callback) {
        const overlay = document.getElementById('adOverlay');
        const timerEl = document.getElementById('adTimer');
        
        if (!overlay) return callback();

        let timeLeft = 5;
        timerEl.innerText = timeLeft;
        
        overlay.classList.remove('d-none');
        
        this.adInterval = setInterval(() => {
            timeLeft--;
            timerEl.innerText = timeLeft;
            if (timeLeft <= 0) {
                clearInterval(this.adInterval);
                overlay.classList.add('d-none');
                callback();
            }
        }, 1000);
        
        this.closeAd = () => {
            clearInterval(this.adInterval);
            overlay.classList.add('d-none');
            callback();
        };
    },

    renderInfo(data, url, t) {
        document.getElementById('thumb').src = data.thumbnail;
        document.getElementById('videoTitle').innerText = data.title;
        document.getElementById('duration').innerText = data.duration;
        
        const container = document.getElementById('buttonsContainer');
        container.innerHTML = '';
        
        const labels = { 'best': t.qualityBest, '1080': t.quality1080, '720': t.quality720, 'audio': t.qualityAudio };
        ['best', '1080', '720', 'audio'].forEach(key => {
            if (data.sizes[key]) {
                const button = document.createElement('button');
                button.className = 'btn btn-outline-primary quality-btn';
                button.innerHTML = `${labels[key] || key}<br><small style="opacity:0.7">${data.sizes[key]}</small>`;
                button.onclick = () => this.startDownload(url, key);
                container.appendChild(button);
            }
        });

        if (data.is_playlist && data.entries) {
            this.renderPlaylist(data.entries);
        }

        document.getElementById('videoInfo').style.display = 'block';
    },

    renderPlaylist(entries) {
        const plContainer = document.getElementById('playlistContainer');
        plContainer.innerHTML = '';
        
        const card = Utils.createElement('div', 'card bg-dark border-secondary shadow-sm');
        const header = Utils.createElement('div', 'card-header border-secondary text-center text-white-50 small fw-bold text-uppercase py-2', 'Содержимое плейлиста');
        header.style.background = 'rgba(255,255,255,0.05)';
        
        const list = Utils.createElement('div', 'list-group list-group-flush');
        list.style.maxHeight = '400px';
        list.style.overflowY = 'auto';

        entries.forEach((entry, index) => {
            const item = Utils.createElement('div', 'list-group-item bg-transparent text-light border-secondary d-flex flex-column flex-sm-row justify-content-sm-center align-items-sm-center gap-2 py-3');
            
            const infoDiv = Utils.createElement('div', 'd-flex align-items-center text-truncate me-2');
            infoDiv.style.flex = '1';
            
            const badge = Utils.createElement('span', 'badge bg-secondary bg-opacity-25 text-secondary me-3 rounded-pill', index + 1);
            badge.style.minWidth = '25px';
            
            const title = Utils.createElement('span', 'text-truncate small fw-medium', entry.title);
            title.title = entry.title; // Tooltip

            infoDiv.append(badge, title);

            const btnGroup = Utils.createElement('div', 'd-flex gap-2 shrink-0 justify-content-end');
            const singleUrl = `https://www.youtube.com/watch?v=${entry.id}`;
            
            const btnMp4 = Utils.createElement('button', 'btn btn-sm btn-outline-info');
            btnMp4.innerHTML = '<i class="bi bi-camera-video"></i> MP4';
            btnMp4.onclick = () => this.startDownload(singleUrl, 'best');

            const btnMp3 = Utils.createElement('button', 'btn btn-sm btn-outline-success');
            btnMp3.innerHTML = '<i class="bi bi-music-note-beamed"></i> MP3';
            btnMp3.onclick = () => this.startDownload(singleUrl, 'audio');

            btnGroup.append(btnMp4, btnMp3);
            item.append(infoDiv, btnGroup);
            list.appendChild(item);
        });

        card.append(header, list);
        plContainer.appendChild(card);
        plContainer.style.display = 'block';
    },

    async startDownload(url, quality) {
        document.getElementById('buttonsContainer').style.pointerEvents = 'none';
        document.getElementById('buttonsContainer').style.opacity = '0.5';
        document.getElementById('progress-section').style.display = 'block';
        
        const formData = new FormData();
        formData.append('url', url);
        formData.append('quality', quality);

        try {
            const response = await fetch('/start_download', { 
                method: 'POST', 
                body: formData,
                headers: { 'X-CSRFToken': Utils.getCsrfToken() }
            });

            // Проверяем, что сервер вернул JSON, а не HTML ошибку
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") === -1) {
                throw new Error(`Сервер вернул ошибку (${response.status}). Возможно, ведутся тех. работы.`);
            }

            const data = await response.json();

            if (response.ok) {
                this.currentTaskId = data.task_id;
                this.trackProgress();
                setTimeout(() => this.updateLimitUI(), 1000); // Обновляем лимит сразу после старта
            } else {
                showToast('Ошибка старта: ' + data.error, true);
                this.resetUI();
            }
        } catch (e) {
            showToast('Ошибка: ' + e, true);
            this.resetUI();
        }
    },

    trackProgress() {
        const t = window.translations[window.appSettings.lang] || window.translations['ru'];
        if (this.progressInterval) clearInterval(this.progressInterval);
        
        this.progressInterval = setInterval(async () => {
            try {
                const res = await fetch(`/progress/${this.currentTaskId}`);
                const data = await res.json();
                const bar = document.getElementById('progressBar');
                const statusText = document.getElementById('statusText');
                const percentText = document.getElementById('percentText');

                if (data.status === 'downloading') {
                    bar.style.width = data.progress + '%';
                    bar.className = 'progress-bar progress-bar-striped progress-bar-animated';
                    statusText.innerText = (data.message && /\d/.test(data.message)) ? `${t.statusDownloading} (${data.message})` : t.statusDownloading;
                    percentText.innerText = Math.round(parseFloat(data.progress)) + '%';
                } else if (data.status === 'processing') {
                    bar.style.width = '100%';
                    bar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
                    statusText.innerText = t.statusProcessing;
                    percentText.innerText = '100%';
                } else if (data.status === 'finished') {
                    clearInterval(this.progressInterval);
                    bar.className = 'progress-bar bg-success';
                    statusText.innerText = t.statusFinished;
                    document.getElementById('downloadBtn').href = `/get_file/${this.currentTaskId}`;
                    if (navigator.share) document.getElementById('shareBtn').style.display = 'block';
                    document.getElementById('progress-section').style.display = 'none';
                    document.getElementById('download-section').style.display = 'block';
                    VideoDownloader.updateLimitUI(); // Обновляем лимит
                } else if (data.status === 'error') {
                    clearInterval(this.progressInterval);
                    showToast(t.statusError + data.error, true);
                    this.resetUI();
                }
            } catch (e) { console.error(e); }
        }, 1000);
    },

    resetUI(full = false) {
        document.getElementById('buttonsContainer').style.pointerEvents = 'auto';
        document.getElementById('buttonsContainer').style.opacity = '1';
        document.getElementById('progress-section').style.display = 'none';
        if (full) {
            document.getElementById('videoInfo').style.display = 'none';
            document.getElementById('download-section').style.display = 'none';
            document.getElementById('playlistContainer').style.display = 'none';
        }
    },
    
    async updateLimitUI() {
        try {
            const res = await fetch('/get_limit_status');
            const data = await res.json();
            const badge = document.getElementById('limitBadge');
            const count = document.getElementById('limitCount');
            
            if (count) count.innerText = `${data.count}/${data.limit}`; // Текст "Лимит..." обновляется через applySettings
            if (badge && data.reached) {
                badge.classList.remove('bg-secondary');
                badge.classList.add('bg-danger');
                
                // Блокируем поиск
                const searchBtn = document.getElementById('searchBtn');
                const urlInput = document.getElementById('urlInput');
                if(searchBtn) searchBtn.disabled = true;
                if(urlInput) urlInput.disabled = true;
                
                // Показываем модальное окно
                const limitModalEl = document.getElementById('limitModal');
                if(limitModalEl && !limitModalEl.classList.contains('show')) {
                    new bootstrap.Modal(limitModalEl).show();
                }
            }
        } catch(e) {}
    }
};

// Экспорт функций для HTML обработчиков
window.getInfo = () => VideoDownloader.getInfo();
window.startDownload = (u, q) => VideoDownloader.startDownload(u, q);

// --- Функция "Поделиться" ---
window.shareFile = async function() {
    const downloadBtn = document.getElementById('downloadBtn');
    const shareBtn = document.getElementById('shareBtn');
    const originalText = shareBtn.innerText;
    
    // Получаем ссылку (или с сервера, или уже локальный blob)
    let url = downloadBtn.href;
    
    try {
        shareBtn.disabled = true;
        shareBtn.innerText = 'Загрузка...';

        let blob;
        let filename = 'video_download';

        // Если ссылка ведет на сервер, скачиваем файл в память
        if (url.includes('/get_file/')) {
            const res = await fetch(url);
            if (!res.ok) throw new Error('Файл недоступен (возможно, уже скачан)');
            blob = await res.blob();
            
            // Пытаемся узнать имя файла из заголовков
            const disposition = res.headers.get('Content-Disposition');
            if (disposition && disposition.match(/filename="?([^"]+)"?/)) {
                filename = disposition.match(/filename="?([^"]+)"?/)[1];
            }

            // Обновляем кнопку "Сохранить", чтобы она брала файл из памяти (так как на сервере он удалится)
            const blobUrl = URL.createObjectURL(blob);
            downloadBtn.href = blobUrl;
            downloadBtn.download = filename; 
        } else {
            // Если уже blob, просто берем его
            blob = await fetch(url).then(r => r.blob());
            filename = downloadBtn.download || 'video_download.mp4';
        }

        const file = new File([blob], filename, { type: blob.type });

        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({ files: [file], title: 'Видео', text: 'Скачано с Video Downloader' });
        } else {
            throw new Error('Ваш браузер не поддерживает отправку этого файла.');
        }
    } catch (e) {
        showToast('Ошибка: ' + e.message, true);
    } finally {
        shareBtn.disabled = false;
        shareBtn.innerText = originalText;
    }
}

// Функция сброса интерфейса (вместо перезагрузки)
window.resetApp = function() {
    document.getElementById('urlInput').value = '';
    VideoDownloader.resetUI(true);
    document.getElementById('searchBtn').disabled = false;
    document.getElementById('searchBtn').innerHTML = window.translations[window.appSettings.lang].searchBtn;
}

// Функция покупки Premium
window.buyPremium = function(plan) {
    // Проверка авторизации перед покупкой
    if (!lastAuthData.isAuth) {
        const t = window.translations[window.appSettings.lang] || window.translations['ru'];
        Swal.fire({
            title: t.authRequiredTitle,
            text: t.authRequiredText,
            icon: 'info',
            showCancelButton: true,
            confirmButtonText: t.authLogin,
            cancelButtonText: t.authRegister
        }).then((result) => {
            if (result.isConfirmed) window.location.href = '/login_page';
            else if (result.dismiss === Swal.DismissReason.cancel) window.location.href = '/register_page';
        });
        return;
    }

    const lang = window.appSettings.lang;
    let currency = 'RUB';
    if (lang === 'kg') currency = 'KGS';
    if (lang === 'en') currency = 'USD';
    
    // Перенаправление на оплату
    window.location.href = `/buy_premium?plan=${plan}&currency=${currency}`;
}

document.addEventListener('DOMContentLoaded', () => {
    // --- ИНИЦИАЛИЗАЦИЯ ---
    loadSettings();
    checkAuth();
    if (!localStorage.getItem('cookieConsent') && window.location.pathname === '/') { // Показывать баннер куки только на главной странице
        const banner = document.getElementById('cookie-banner');
        if(banner) banner.style.display = 'block';
    }
    for (let i = 0; i < 50; i++) createSnowflake(true);
    setInterval(() => createSnowflake(false), 50);
    document.addEventListener('mousemove', (e) => {
        if(snowContainer) {
            const x = (e.clientX / window.innerWidth - 0.5) * 20;
            const y = (e.clientY / window.innerHeight - 0.5) * 20;
            snowContainer.style.transform = `translate(${x}px, ${y}px)`;
        }
    });
    
    // Скролл эффект для верхней панели
    window.addEventListener('scroll', () => {
        const topBar = document.querySelector('.top-bar');
        if (topBar) {
            if (window.scrollY > 10) {
                topBar.classList.add('scrolled');
                topBar.style.background = 'rgba(30, 30, 30, 0.9)';
                topBar.style.top = '10px';
            } else {
                topBar.classList.remove('scrolled');
                topBar.style.background = 'rgba(30, 30, 30, 0.6)';
                topBar.style.top = '25px';
            }
        }
    });
});

// Логика заставки и редиректа (вынесена отдельно для надежности)
async function initApp() {
    const splash = document.getElementById('splash-screen');
    if(!splash) return;

    // 1. Проверяем авторизацию, чтобы обновить кнопки входа/профиля
    await checkAuth();

    // 2. Если авторизован - управляем заставкой
    let isReload = false;
    try {
        const navEntry = performance.getEntriesByType("navigation")[0];
        isReload = navEntry && navEntry.type === 'reload';
    } catch(e) {}

    if (!isReload && document.referrer && document.referrer.startsWith(window.location.origin)) {
        splash.style.display = 'none';
    } else {
        setTimeout(() => {
            splash.classList.add('hidden');
            setTimeout(() => { splash.style.display = 'none'; }, 500);
        }, 1500);
    }
}

// Запускаем initApp когда страница полностью загружена (или сразу, если уже загружена)
if (document.readyState === 'complete') {
    initApp();
} else {
    window.addEventListener('load', initApp);
}
