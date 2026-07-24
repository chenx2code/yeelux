const deviceGroups = document.querySelectorAll('.device-group');

let isUpdating = false;

// i18n Translations
const translations = {
    en: {
        connecting: "Connecting...",
        on: "ON",
        off: "OFF",
        disconnected: "Disconnected / Offline",
        focus_mode: "Focus Mode",
        sleep_timer: "Sleep Timer",
        inactive: "Inactive",
        start: "Start",
        cancel: "Cancel",
        work_mins: "Work (mins)",
        rest_mins: "Rest (mins)",
        timer_mins: "Timer (mins)",
        turns_off_in: "Turns off in {time}",
        working: "Working",
        resting: "Resting",
        rest_light: "Rest Light",
        dim: "Dim",
        turn_off: "Off",
        rest_brightness: "Brightness",
        rest_color_temp: "Color Temp"
    },
    zh: {
        connecting: "正在连接...",
        on: "已开启",
        off: "已关闭",
        disconnected: "未连接或离线",
        focus_mode: "专注模式",
        sleep_timer: "睡眠定时",
        inactive: "未开启",
        start: "开启",
        cancel: "取消",
        work_mins: "工作 (分钟)",
        rest_mins: "休息 (分钟)",
        timer_mins: "关闭倒计时 (分钟)",
        turns_off_in: "将在 {time} 后关闭",
        working: "工作中",
        resting: "休息中",
        rest_light: "休息灯光",
        dim: "调暗",
        turn_off: "关灯",
        rest_brightness: "亮度",
        rest_color_temp: "色温"
    }
};

let currentLang = localStorage.getItem('yeelight_lang') || 'zh';

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('yeelight_lang', lang);
    
    // Update static HTML elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });

    // Update Segmented Control UI
    document.querySelectorAll('.lang-option').forEach(el => {
        if (el.getAttribute('data-lang') === lang) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    // Re-fetch to update dynamic states
    fetchAllStatus();
    fetchAutomations();
}

// Bind language toggle button
const langOptions = document.querySelectorAll('.lang-option');
langOptions.forEach(option => {
    option.addEventListener('click', (e) => {
        const selectedLang = e.target.getAttribute('data-lang');
        setLanguage(selectedLang);
    });
});

// Initial Translation Setup
document.addEventListener('DOMContentLoaded', () => {
    setLanguage(currentLang);
});

// --- Sidebar TOC Logic ---
const tocItems = document.querySelectorAll('.toc-item');
const dashboardCards = document.querySelectorAll('.apple-card');

// Smooth scrolling on click
tocItems.forEach(item => {
    item.addEventListener('click', () => {
        const targetId = item.getAttribute('data-target');
        const targetCard = document.getElementById(targetId);
        if (targetCard) {
            const yOffset = -80; // Margin from top
            const y = targetCard.getBoundingClientRect().top + window.scrollY + yOffset;
            window.scrollTo({top: y, behavior: 'smooth'});
        }
    });
});

// Intersection Observer for highlighting active node in TOC
const observerOptions = {
    root: null,
    rootMargin: '-40% 0px -60% 0px', // triggers when card is roughly in middle/top half
    threshold: 0
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const activeId = entry.target.id;
            tocItems.forEach(item => {
                if (item.getAttribute('data-target') === activeId) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
        }
    });
}, observerOptions);

dashboardCards.forEach(card => observer.observe(card));
// -----------------------

// Poll all statuses
async function fetchAllStatus() {
    if (isUpdating) return;
    try {
        const res = await fetch('/api/status/all');
        const data = await res.json();
        
        deviceGroups.forEach(group => {
            const deviceId = group.dataset.deviceId;
            if (data[deviceId]) {
                updateUI(group, data[deviceId]);
            } else {
                setOffline(group);
            }
        });
    } catch (e) {
        deviceGroups.forEach(group => setOffline(group));
    }
}

function updateUI(group, data) {
    const toggleBtn = group.querySelector('.toggle-btn');
    const iconContainer = group.querySelector('.light-icon');
    const statusBadge = group.querySelector('.connection-status');
    const brightnessSlider = group.querySelector('.brightness-slider');
    const brightnessVal = group.querySelector('.brightness-val');
    const ctSlider = group.querySelector('.ct-slider');
    const ctVal = group.querySelector('.ct-val');

    if (!data.success) {
        setOffline(group);
        return;
    }
    
    toggleBtn.checked = data.is_on;
    
    if (data.is_on) {
        iconContainer.classList.add('active');
        statusBadge.textContent = translations[currentLang].on;
    } else {
        iconContainer.classList.remove('active');
        statusBadge.textContent = translations[currentLang].off;
    }

    if (!group.dataset.isUpdating) {
        brightnessSlider.value = data.brightness;
        brightnessVal.textContent = data.brightness + '%';
        ctSlider.value = data.color_temp;
        ctVal.textContent = data.color_temp + 'K';
    }
}

function setOffline(group) {
    group.querySelector('.connection-status').textContent = translations[currentLang].disconnected;
    group.querySelector('.light-icon').classList.remove('active');
    group.querySelector('.toggle-btn').checked = false;
}

function debounceSlider(group, element, valElement, suffix, apiEndpoint) {
    let timeout;
    element.addEventListener('input', (e) => {
        valElement.textContent = e.target.value + suffix;
        group.dataset.isUpdating = "true";
        isUpdating = true;
    });
    
    element.addEventListener('change', (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(async () => {
            try {
                await fetch(apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ value: e.target.value })
                });
            } catch(e) {
                console.error(e);
            }
            setTimeout(() => { 
                group.dataset.isUpdating = "";
                isUpdating = false; 
            }, 500);
        }, 100);
    });
}

// Bind events to each device
deviceGroups.forEach(group => {
    const deviceId = group.dataset.deviceId;
    const toggleBtn = group.querySelector('.toggle-btn');
    const iconContainer = group.querySelector('.light-icon');
    const statusBadge = group.querySelector('.connection-status');
    
    toggleBtn.addEventListener('change', async () => {
        if (toggleBtn.checked) {
            iconContainer.classList.add('active');
            statusBadge.textContent = translations[currentLang].on;
        } else {
            iconContainer.classList.remove('active');
            statusBadge.textContent = translations[currentLang].off;
        }
        
        try {
            const res = await fetch(`/api/toggle/${deviceId}`, { method: 'POST' });
            const data = await res.json();
            updateUI(group, data);
        } catch (e) {
            setOffline(group);
        }
    });

    const brightnessSlider = group.querySelector('.brightness-slider');
    const brightnessVal = group.querySelector('.brightness-val');
    const ctSlider = group.querySelector('.ct-slider');
    const ctVal = group.querySelector('.ct-val');

    debounceSlider(group, brightnessSlider, brightnessVal, '%', `/api/brightness/${deviceId}`);
    debounceSlider(group, ctSlider, ctVal, 'K', `/api/colortemp/${deviceId}`);
    
    // Timer Bindings
    const timerToggleBtn = group.querySelector('.timer-toggle-btn');
    const timerInput = group.querySelector('.timer-input');
    const timerStatus = group.querySelector('.timer-status');
    timerToggleBtn.addEventListener('click', () => {
        const isStarting = !timerToggleBtn.classList.contains('stop-btn');
        let mins = parseInt(timerInput.value) || 15;
        
        // Optimistic UI update for snappiness
        if (isStarting) {
            timerToggleBtn.textContent = translations[currentLang].cancel;
            timerToggleBtn.classList.add('stop-btn');
            timerStatus.textContent = translations[currentLang].turns_off_in.replace('{time}', formatTime(mins * 60));
            timerStatus.style.color = 'var(--accent-color)';
            timerInput.disabled = true;
        } else {
            timerToggleBtn.textContent = translations[currentLang].start;
            timerToggleBtn.classList.remove('stop-btn');
            timerStatus.textContent = translations[currentLang].inactive;
            timerStatus.style.color = 'var(--text-secondary)';
            timerInput.disabled = false;
        }

        const body = { action: isStarting ? 'start' : 'stop' };
        if (isStarting) body.minutes = mins;
        
        fetch(`/api/timer/${deviceId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(() => fetchAutomations());
    });

    // Focus Bindings
    const focusToggleBtn = group.querySelector('.focus-toggle-btn');
    const focusWorkInput = group.querySelector('.focus-work-input');
    const focusRestInput = group.querySelector('.focus-rest-input');
    const focusStatus = group.querySelector('.focus-status');
    const restOptions = group.querySelectorAll('.rest-option');
    const restDimOptions = group.querySelector('.rest-dim-options');
    const focusBrightnessInput = group.querySelector('.focus-brightness-input');
    const focusCtInput = group.querySelector('.focus-ct-input');
    const focusBrightnessVal = group.querySelector('.focus-brightness-val');
    const focusCtVal = group.querySelector('.focus-ct-val');

    if (focusBrightnessInput && focusBrightnessVal) {
        focusBrightnessInput.addEventListener('input', (e) => {
            focusBrightnessVal.textContent = e.target.value + '%';
        });
    }
    
    if (focusCtInput && focusCtVal) {
        focusCtInput.addEventListener('input', (e) => {
            focusCtVal.textContent = e.target.value + 'K';
        });
    }
    
    let currentRestAction = 'dim';

    restOptions.forEach(opt => {
        opt.addEventListener('click', (e) => {
            if (focusWorkInput.disabled) return; // Prevent changing while running
            restOptions.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            currentRestAction = opt.getAttribute('data-action');
            if (currentRestAction === 'off') {
                restDimOptions.classList.add('hidden');
            } else {
                restDimOptions.classList.remove('hidden');
            }
        });
    });
    focusToggleBtn.addEventListener('click', () => {
        const isStarting = !focusToggleBtn.classList.contains('stop-btn');
        let workMins = parseInt(focusWorkInput.value) || 45;
        let restMins = parseInt(focusRestInput.value) || 10;
        
        // Optimistic UI update for snappiness
        if (isStarting) {
            focusToggleBtn.textContent = translations[currentLang].cancel;
            focusToggleBtn.classList.add('stop-btn');
            focusStatus.textContent = `${translations[currentLang].working} (${formatTime(workMins * 60)})`;
            focusStatus.style.color = 'var(--accent-color)';
            focusWorkInput.disabled = true;
            focusRestInput.disabled = true;
            focusBrightnessInput.disabled = true;
            focusCtInput.disabled = true;
            const configPanel = group.querySelector('.focus-config');
            if (configPanel) configPanel.classList.add('disabled-panel');
        } else {
            focusToggleBtn.textContent = translations[currentLang].start;
            focusToggleBtn.classList.remove('stop-btn');
            focusStatus.textContent = translations[currentLang].inactive;
            focusStatus.style.color = 'var(--text-secondary)';
            focusWorkInput.disabled = false;
            focusRestInput.disabled = false;
            focusBrightnessInput.disabled = false;
            focusCtInput.disabled = false;
            const configPanel = group.querySelector('.focus-config');
            if (configPanel) configPanel.classList.remove('disabled-panel');
        }

        const body = { action: isStarting ? 'start' : 'stop' };
        if (isStarting) {
            body.work_mins = workMins;
            body.rest_mins = restMins;
            body.rest_action = currentRestAction;
            body.rest_brightness = parseInt(focusBrightnessInput.value) || 5;
            body.rest_color_temp = parseInt(focusCtInput.value) || 2700;
        }
        fetch(`/api/focus/${deviceId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(() => fetchAutomations());
    });
    
    // Settings Toggle Bindings
    const settingsBtns = group.querySelectorAll('.settings-toggle-btn');
    settingsBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('active');
            const content = btn.closest('.automation-section').querySelector('.hidden-content');
            if (content) {
                content.classList.toggle('expanded');
            }
        });
    });
});

function formatTime(seconds) {
    if (seconds <= 0) return "00:00";
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
}

// Local state for 1-second countdown ticks
const localState = {};

async function fetchAutomations() {
    deviceGroups.forEach(async group => {
        const deviceId = group.dataset.deviceId;
        if (!localState[deviceId]) localState[deviceId] = {};
        
        try {
            // Fetch Timer
            const tRes = await fetch(`/api/timer/${deviceId}`);
            const tData = await tRes.json();
            const timerStatus = group.querySelector('.timer-status');
            const timerToggleBtn = group.querySelector('.timer-toggle-btn');
            const timerInput = group.querySelector('.timer-input');

            if (tData.active) {
                localState[deviceId].timerActive = true;
                localState[deviceId].timerRemaining = tData.remaining_seconds;
                timerStatus.textContent = translations[currentLang].turns_off_in.replace('{time}', formatTime(tData.remaining_seconds));
                timerStatus.style.color = 'var(--accent-color)';
                timerToggleBtn.textContent = translations[currentLang].cancel;
                timerToggleBtn.classList.add('stop-btn');
                timerInput.disabled = true;
                const configPanel = group.querySelector('.timer-config');
                if (configPanel) configPanel.classList.add('disabled-panel');
            } else {
                localState[deviceId].timerActive = false;
                timerStatus.textContent = translations[currentLang].inactive;
                timerStatus.style.color = 'var(--text-secondary)';
                timerToggleBtn.textContent = translations[currentLang].start;
                timerToggleBtn.classList.remove('stop-btn');
                timerInput.disabled = false;
                const configPanel = group.querySelector('.timer-config');
                if (configPanel) configPanel.classList.remove('disabled-panel');
            }

            // Fetch Focus
            const fRes = await fetch(`/api/focus/${deviceId}`);
            const fData = await fRes.json();
            const focusStatus = group.querySelector('.focus-status');
            const focusToggleBtn = group.querySelector('.focus-toggle-btn');
            const focusWorkInput = group.querySelector('.focus-work-input');
            const focusRestInput = group.querySelector('.focus-rest-input');
            const focusBrightnessInput = group.querySelector('.focus-brightness-input');
            const focusCtInput = group.querySelector('.focus-ct-input');

            if (fData.active) {
                localState[deviceId].focusActive = true;
                localState[deviceId].focusRemaining = fData.remaining_seconds;
                localState[deviceId].focusState = fData.state;
                let stateName = fData.state === 'working' ? translations[currentLang].working : translations[currentLang].resting;
                focusStatus.textContent = `${stateName} (${formatTime(fData.remaining_seconds)})`;
                focusStatus.style.color = fData.state === 'working' ? 'var(--accent-color)' : '#FFB340';
                focusToggleBtn.textContent = translations[currentLang].cancel;
                focusToggleBtn.classList.add('stop-btn');
                focusWorkInput.disabled = true;
                focusRestInput.disabled = true;
                focusBrightnessInput.disabled = true;
                focusCtInput.disabled = true;
                const configPanel = group.querySelector('.focus-config');
                if (configPanel) configPanel.classList.add('disabled-panel');
            } else {
                localState[deviceId].focusActive = false;
                focusStatus.textContent = translations[currentLang].inactive;
                focusStatus.style.color = 'var(--text-secondary)';
                focusToggleBtn.textContent = translations[currentLang].start;
                focusToggleBtn.classList.remove('stop-btn');
                focusWorkInput.disabled = false;
                focusRestInput.disabled = false;
                focusBrightnessInput.disabled = false;
                focusCtInput.disabled = false;
                const configPanel = group.querySelector('.focus-config');
                if (configPanel) configPanel.classList.remove('disabled-panel');
            }
        } catch(e) {
            console.error("Failed to fetch automations for", deviceId, e);
        }
    });
}

// Poll status every 3 seconds
setInterval(() => {
    fetchAllStatus();
    fetchAutomations();
}, 3000);

// Local 1-second tick to update UI countdowns smoothly
setInterval(() => {
    deviceGroups.forEach(group => {
        const deviceId = group.dataset.deviceId;
        if (!localState[deviceId]) return;

        const state = localState[deviceId];
        const timerStatus = group.querySelector('.timer-status');
        const focusStatus = group.querySelector('.focus-status');

        if (state.timerActive && state.timerRemaining > 0) {
            state.timerRemaining -= 1;
            timerStatus.textContent = translations[currentLang].turns_off_in.replace('{time}', formatTime(state.timerRemaining));
        }

        if (state.focusActive && state.focusRemaining > 0) {
            state.focusRemaining -= 1;
            let stateName = state.focusState === 'working' ? translations[currentLang].working : translations[currentLang].resting;
            focusStatus.textContent = `${stateName} (${formatTime(state.focusRemaining)})`;
        }
    });
}, 1000);

// Initial fetch
fetchAllStatus();
fetchAutomations();

// Bind wheel scrolling for number inputs
const numberInputs = document.querySelectorAll('.apple-input[type="number"]');
numberInputs.forEach(input => {
    input.addEventListener('wheel', (e) => {
        // Prevent default page scroll
        e.preventDefault();
        
        let val = parseInt(input.value) || 0;
        let step = parseInt(input.step) || 1;
        let min = parseInt(input.min);
        let max = parseInt(input.max);
        
        if (e.deltaY < 0) {
            val += step;
        } else {
            val -= step;
        }
        
        if (!isNaN(min) && val < min) val = min;
        if (!isNaN(max) && val > max) val = max;
        
        input.value = val;
    }, { passive: false });
});
