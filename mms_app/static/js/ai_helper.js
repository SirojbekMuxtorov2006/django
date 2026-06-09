document.addEventListener("DOMContentLoaded", function () {
    // Sidebar toggle for mobile devices
    const sidebar = document.querySelector(".sidebar");
    const toggleBtn = document.getElementById("sidebarToggleBtn");
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            sidebar.classList.toggle("show");
        });

        // Close sidebar on tapping outer screen body
        document.body.addEventListener("click", function (e) {
            if (sidebar.classList.contains("show") && !sidebar.contains(e.target) && e.target !== toggleBtn) {
                sidebar.classList.remove("show");
            }
        });
    }

    // AI CHAT AJAX LOGIC
    const chatForm = document.getElementById("aiChatForm");
    const messageInput = document.getElementById("aiMessageInput");
    const chatContainer = document.getElementById("chatMessagesContainer");

    if (chatForm && messageInput && chatContainer) {
        chatForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const messageText = messageInput.value.trim();
            if (!messageText) return;

            // 1. Append User Message Bubble
            appendMessage("user", messageText);
            messageInput.value = ""; // clear input
            
            // Scroll to bottom
            scrollToBottom();

            // 2. Append Loading Indicator Bubble
            const loadingId = "ai-loading-" + Date.now();
            appendLoadingBubble(loadingId);
            scrollToBottom();

            // 3. Dispatch AJAX Request
            fetch("/api/chat/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({ message: messageText })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("HTTP error " + response.status);
                }
                return response.json();
            })
            .then(data => {
                // Remove loading bubble
                removeElement(loadingId);
                
                if (data.status === "success") {
                    // Append AI reply bubble
                    appendMessage("ai", data.reply);
                } else {
                    appendMessage("ai", "⚠️ Tizim bilan bog'lanishda xatolik: " + (data.message || "noma'lum xato"));
                }
                scrollToBottom();
            })
            .catch(error => {
                removeElement(loadingId);
                appendMessage("ai", "❌ Aloqa yo'qolgan. Tarmoq ulanishini yoki server holatini tekshiring. (Error: " + error.message + ")");
                scrollToBottom();
            });
        });
    }

    // Helper: Append Bubble
    function appendMessage(sender, text) {
        const bubble = document.createElement("div");
        bubble.className = `${sender}-bubble mb-3 animate-fade-in`;
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        if (sender === "user") {
            bubble.innerHTML = `
                <div class="bubble-header small text-violet text-end"><i class="bi bi-person-fill"></i> Siz</div>
                <div class="bubble-content mt-1 text-end">${escapeHtml(text)}</div>
                <div class="bubble-time mt-1 text-muted small text-end">${timestamp}</div>
            `;
        } else {
            // AI returns markdown-like responses, replace linebreaks with br and format basic markdown
            const formattedText = formatMarkdown(text);
            bubble.innerHTML = `
                <div class="bubble-header small text-cyan"><i class="bi bi-robot"></i> Core AI Commander</div>
                <div class="bubble-content mt-1">${formattedText}</div>
                <div class="bubble-time mt-1 text-muted small">${timestamp}</div>
            `;
        }
        
        chatContainer.appendChild(bubble);
    }

    // Helper: Append Loading Bubble
    function appendLoadingBubble(id) {
        const bubble = document.createElement("div");
        bubble.id = id;
        bubble.className = "ai-bubble mb-3 animate-fade-in";
        bubble.innerHTML = `
            <div class="bubble-header small text-cyan"><i class="bi bi-robot"></i> Core AI Commander</div>
            <div class="bubble-content mt-1 d-flex align-items-center gap-1">
                <span class="spinner-grow spinner-grow-sm text-cyan" role="status"></span>
                <span class="text-muted small italic">Buyruq bajarilmoqda...</span>
            </div>
        `;
        chatContainer.appendChild(bubble);
    }

    // Helper: Remove Element by ID
    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // Helper: Scroll to bottom
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Helper: Get CSRF Token Cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Helper: Escape HTML to prevent XSS
    function escapeHtml(text) {
        const map = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        };
        return text.replace(/[&<>"']/g, function (m) { return map[m]; });
    }

    // Helper: Render simple markdown in browser
    function formatMarkdown(text) {
        // Line breaks
        let html = text.replace(/\n/g, "<br>");
        // Bold tags **text**
        html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        // Bullet list points
        html = html.replace(/<br>\-\s(.*?)/g, "<br>• $1");
        return html;
    }
});
