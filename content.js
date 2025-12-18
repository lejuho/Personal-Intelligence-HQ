// ==UserScript==
// @name         Gemini Manager (Save & Dashboard)
// @namespace    http://tampermonkey.net/
// @version      3.3
// @description  Save Chat to Local DB & View Analytics Dashboard (Auto Wake-up)
// @author       You
// @match        https://gemini.google.com/*
// @connect      127.0.0.1
// @connect      localhost
// @grant        GM_xmlhttpRequest
// ==/UserScript==

(function() {
    'use strict';

    // --- UI 컨테이너 ---
    const container = document.createElement('div');
    container.style.position = 'fixed';
    container.style.left = '320px';
    container.style.bottom = '20px';
    container.style.zIndex = '99999';
    container.style.display = 'flex';
    container.style.flexDirection = 'column-reverse';
    container.style.gap = '10px';
    document.body.appendChild(container);

    function createButton(text, color) {
        const btn = document.createElement('button');
        btn.innerText = text;
        btn.style.padding = '12px 20px';
        btn.style.backgroundColor = color;
        btn.style.color = 'white';
        btn.style.border = 'none';
        btn.style.borderRadius = '50px';
        btn.style.cursor = 'pointer';
        btn.style.fontWeight = 'bold';
        btn.style.fontSize = '14px';
        btn.style.boxShadow = '0 4px 6px rgba(0,0,0,0.2)';
        btn.style.transition = 'transform 0.1s';
        btn.onmousedown = () => btn.style.transform = 'scale(0.95)';
        btn.onmouseup = () => btn.style.transform = 'scale(1)';
        return btn;
    }

    // ==========================================
    //  [핵심] 서버 깨우기 헬퍼 (Tampermonkey용)
    // ==========================================
    function ensureServerRunning(statusBtn, callback) {
        const originalText = statusBtn.innerText;

        // 1. Health Check
        GM_xmlhttpRequest({
            method: "HEAD",
            url: "http://127.0.0.1:8000/docs",
            onload: function(res) {
                if (res.status === 200) {
                    callback(); // 살아있으면 바로 실행
                } else {
                    triggerWakeUp();
                }
            },
            onerror: function() {
                triggerWakeUp();
            }
        });

        function triggerWakeUp() {
            statusBtn.innerText = "🔄 시스템 가동 중...";
            window.location.href = "aisys://run"; // 배치파일 실행

            // 2. Polling (30초 대기)
            let attempts = 0;
            const interval = setInterval(() => {
                attempts++;
                GM_xmlhttpRequest({
                    method: "HEAD",
                    url: "http://127.0.0.1:8000/docs",
                    onload: function(res) {
                        if (res.status === 200) {
                            clearInterval(interval);
                            statusBtn.innerText = originalText;
                            callback(); // 성공 후 실행
                        }
                    }
                });

                if (attempts >= 10) { // 30초 경과
                    clearInterval(interval);
                    statusBtn.innerText = "❌ 가동 실패";
                    setTimeout(() => { statusBtn.innerText = originalText; }, 2000);
                    alert("서버를 켤 수 없습니다. (wake_up.bat 확인 필요)");
                }
            }, 3000);
        }
    }

    // ==========================================
    //  버튼 기능 구현
    // ==========================================

    // 1. 분석 보기 버튼
    const dashBtn = createButton('📊 분석 보기', '#673AB7');
    let dashboardWindow = null;

    dashBtn.onclick = function() {
        ensureServerRunning(dashBtn, () => {
            if (dashboardWindow && !dashboardWindow.closed) {
                dashboardWindow.focus();
                return;
            }
            const width = 500;
            const height = window.screen.height;
            const left = window.screen.width - width;
            dashboardWindow = window.open(
                "http://127.0.0.1:8501",
                "GeminiDashboard",
                `width=${width},height=${height},left=${left},top=0,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=yes`
            );
        });
    };

    // 2. 전체 저장 버튼
    const saveBtn = createButton('📚 전체 저장', '#2196F3');

    saveBtn.onclick = function() {
        const userQueries = document.querySelectorAll('user-query');
        const modelResponses = document.querySelectorAll('model-response');

        if (userQueries.length === 0) {
            alert('저장할 대화 내용이 없습니다.');
            return;
        }

        let chatData = [];
        const count = Math.min(userQueries.length, modelResponses.length);
        for (let i = 0; i < count; i++) {
            chatData.push({
                question: userQueries[i].innerText,
                answer: modelResponses[i].innerText
            });
        }

        const originalText = saveBtn.innerText;

        // 서버 확인 후 저장 실행
        ensureServerRunning(saveBtn, () => {
            saveBtn.innerText = `⏳ ${count}개 저장...`;
            saveBtn.style.backgroundColor = '#FF9800';

            GM_xmlhttpRequest({
                method: "POST",
                url: "http://127.0.0.1:8000/save_all",
                headers: { "Content-Type": "application/json" },
                data: JSON.stringify(chatData),
                onload: function(response) {
                    if (response.status === 200) {
                        const res = JSON.parse(response.responseText);
                        saveBtn.innerText = `✅ +${res.saved_count}`;
                        saveBtn.style.backgroundColor = '#4CAF50';
                        setTimeout(() => {
                            saveBtn.innerText = originalText;
                            saveBtn.style.backgroundColor = '#2196F3';
                        }, 2000);
                    } else {
                        saveBtn.innerText = '❌ 오류';
                    }
                },
                onerror: function(err) {
                     saveBtn.innerText = '❌ 실패';
                     setTimeout(() => {
                         saveBtn.innerText = originalText;
                         saveBtn.style.backgroundColor = '#2196F3';
                     }, 2000);
                }
            });
        });
    };

    container.appendChild(dashBtn);
    container.appendChild(saveBtn);

})();