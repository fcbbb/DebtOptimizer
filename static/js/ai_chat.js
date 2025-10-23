// 聊天相关变量
let currentConversationId = null;
let currentTaskId = null;
// 新增：用于累积 AI 流式响应
let currentAIResponse = '';

// WebSocket连接变量
let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectInterval = 3000;

// DOM元素引用
let sidebar, sidebarOverlay, historyList, newChatBtn, closeSidebar;
let menuBtn, settingsBtn, clearHistoryBtn;
let settingsModal, closeSettings, settingsForm, clearSettingsBtn, saveSettingsBtn;
let chatMessages, messageInput, sendButton, typingIndicator;
// 新增：图片上传相关元素
let imageUpload, uploadButton;

// 创建打字指示器
const typingIndicatorElement = document.createElement('div');
typingIndicatorElement.id = 'typing-indicator-container'; // ✅ 添加 ID
typingIndicatorElement.className = 'message-container bot';
typingIndicatorElement.innerHTML = `
    <div class="avatar bot-avatar">AI</div>
    <div class="message bot-message">
        <div class="typing-indicator" id="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
`;
typingIndicatorElement.style.display = 'none';

// 初始化DOM元素引用
function initializeDOMElements() {
    sidebar = document.getElementById('sidebar');
    sidebarOverlay = document.getElementById('sidebar-overlay');
    historyList = document.getElementById('history-list');
    newChatBtn = document.getElementById('new-chat-btn');
    closeSidebar = document.getElementById('close-sidebar');
    menuBtn = document.getElementById('menu-btn');
    settingsBtn = document.getElementById('settings-btn');
    clearHistoryBtn = document.getElementById('clear-history-btn');
    settingsModal = document.getElementById('settings-modal');
    closeSettings = document.getElementById('close-settings');
    settingsForm = document.getElementById('settings-form');
    clearSettingsBtn = document.getElementById('clear-settings');
    saveSettingsBtn = document.getElementById('save-settings');
    chatMessages = document.getElementById('chat-messages');
    messageInput = document.getElementById('message-input');
    sendButton = document.getElementById('send-button');
    typingIndicator = document.getElementById('typing-indicator');
    // 新增：图片上传相关元素引用
    imageUpload = document.getElementById('image-upload');
    uploadButton = document.getElementById('upload-button');
    
    // 确保chatMessages存在后再添加打字指示器
    if (chatMessages) {
        chatMessages.appendChild(typingIndicatorElement);
    } else {
        console.error('无法找到chat-messages元素');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // 初始化DOM元素引用
    initializeDOMElements();
    
    // 初始化WebSocket连接
    initializeWebSocket();
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 加载历史记录
    loadHistory();
    
    // 添加欢迎消息
    addWelcomeMessage();
});

// 生成UUID函数
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0,
            v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 初始化WebSocket连接
function initializeWebSocket() {
    // 如果没有task_id，则生成一个新的UUID
    if (!currentTaskId) {
        currentTaskId = generateUUID();
    }
    // const wsUrl = `ws://${window.location.host}/ws/chat/${currentTaskId}/`;
    // const wsUrl = `ws://${window.location.host}/ws/ocr/${currentTaskId}/`;
    const wsUrl = `ws://${window.location.host}/ws/agent/${currentTaskId}/`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function(event) {
        reconnectAttempts = 0;
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onerror = function(error) {
    };
    
    ws.onclose = function(event) {
        if (reconnectAttempts < maxReconnectAttempts) {
            setTimeout(() => {
                reconnectAttempts++;
                initializeWebSocket();
            }, reconnectInterval);
        }
    };
}

// 绑定事件监听器
function bindEventListeners() {
    // 侧边栏事件
    if (menuBtn) menuBtn.addEventListener('click', toggleSidebar);
    if (closeSidebar) closeSidebar.addEventListener('click', toggleSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', toggleSidebar);
    
    // 设置弹窗事件
    if (settingsBtn) settingsBtn.addEventListener('click', toggleSettingsModal);
    if (closeSettings) closeSettings.addEventListener('click', toggleSettingsModal);
    if (clearSettingsBtn) clearSettingsBtn.addEventListener('click', clearSettings);
    if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', saveSettings);
    
    // 新对话按钮事件
    if (newChatBtn) newChatBtn.addEventListener('click', createNewConversation);
    
    // 清除历史记录按钮事件
    if (clearHistoryBtn) clearHistoryBtn.addEventListener('click', clearAllHistory);
    
    // 发送消息事件
    if (sendButton) sendButton.addEventListener('click', submitChat);
    if (messageInput) messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitChat();
        }
    });
    
    // 输入框自适应高度
    if (messageInput) messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // 新增：图片上传按钮事件
    if (uploadButton && imageUpload) {
        // 点击上传按钮时触发文件选择
        uploadButton.addEventListener('click', function() {
            imageUpload.click();
        });
        
        // 文件选择完成后触发上传
        imageUpload.addEventListener('change', handleImageUpload);
    }
}

// 切换侧边栏
function toggleSidebar() {
    if (sidebar) {
        sidebar.classList.toggle('active');
        // 确保侧边栏的定位正确
        const chatContainer = document.querySelector('#ai-chat-popup .chat-container');
        const mainContent = document.querySelector('#ai-chat-popup .main-content');
        if (chatContainer && mainContent) {
            // 获取主内容区域的计算样式
            const mainContentStyles = window.getComputedStyle(mainContent);
            const mainContentHeight = mainContent.offsetHeight 
                - parseFloat(mainContentStyles.paddingTop) 
                - parseFloat(mainContentStyles.paddingBottom);
            
            // 设置侧边栏的位置和高度
            sidebar.style.top = mainContent.offsetTop + 'px';
            sidebar.style.height = mainContentHeight + 'px';
        }
    }
    if (sidebarOverlay) sidebarOverlay.classList.toggle('active');
}

// 切换设置弹窗
function toggleSettingsModal() {
    if (settingsModal) {
        settingsModal.classList.toggle('active');
        // 如果打开设置弹窗，同时关闭侧边栏
        if (settingsModal.classList.contains('active') && sidebar) {
            sidebar.classList.remove('active');
            if (sidebarOverlay) sidebarOverlay.classList.remove('active');
        }
    }
}

// 清除所有历史记录
function clearAllHistory() {
    if (!chatMessages) {
        return;
    }
    
    if (confirm('确定要清除所有历史记录吗？')) {
        localStorage.removeItem('chatHistory');
        updateHistoryList();
        createNewConversation();
    }
}

// 创建新对话
function createNewConversation() {
    if (!chatMessages) {
        return;
    }
    
    currentConversationId = Date.now().toString();
    messageBuffer = '';
    currentTaskId = null;
    
    // 重新初始化WebSocket连接
    if (ws) {
        ws.close();
    }
    initializeWebSocket();
    
    // 清空聊天区域
    clearChatMessages();
    
    // 添加欢迎消息
    addWelcomeMessage();
    
    // 更新历史记录列表
    updateHistoryList();
    
    // 关闭侧边栏
    toggleSidebar();
}

// 更新历史记录列表
function updateHistoryList() {
    const history = getHistory();
    historyList.innerHTML = '';
    
    // 按时间倒序排列
    const sortedHistory = Object.entries(history).sort((a, b) => b[1].timestamp - a[1].timestamp);
    
    sortedHistory.forEach(([id, conversation]) => {
        const historyItem = createHistoryItem(id, conversation);
        historyList.appendChild(historyItem);
    });
}

// 创建历史记录项
function createHistoryItem(id, conversation) {
    const div = document.createElement('div');
    div.className = `history-item ${id === currentConversationId ? 'active' : ''}`;
    div.innerHTML = `
        <div class="history-item-title">${conversation.title || '新对话'}</div>
        <button class="delete-history">&times;</button>
    `;
    
    // 点击加载对话
    div.querySelector('.history-item-title').addEventListener('click', (e) => {
        e.stopPropagation(); // 阻止事件冒泡到文档级别
        loadConversation(id);
    });
    
    // 删除对话
    div.querySelector('.delete-history').addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('确定要删除这个对话吗？')) {
            const history = getHistory();
            delete history[id];
            saveHistory(history);
            updateHistoryList();
            
            // 如果删除的是当前对话，创建新对话
            if (id === currentConversationId) {
                createNewConversation();
            }
        }
    });
    
    return div;
}

// 加载对话
function loadConversation(id) {
    const history = getHistory();
    if (history[id]) {
        currentConversationId = id;
        displayMessages(history[id].messages);
        updateHistoryList();
        // 关闭侧边栏
        toggleSidebar();
    }
}

// 显示消息
function displayMessages(messages) {
    if (!chatMessages) {
        return;
    }
    
    clearChatMessages();
    
    console.log('=== 清空消息后 ===');
    console.log('chatMessages.scrollHeight (清空后):', chatMessages.scrollHeight);
    console.log('chatMessages.clientHeight (清空后):', chatMessages.clientHeight);
    messages.forEach(message => {
        if (message.role === 'user') {
            addUserMessage(message.content, message.timestamp, false);
        } else if (message.role === 'ai') {
            addAIMessage(message.content, message.timestamp, false);
        } else if (message.role === 'thinker') {
            addThinkerMessage(message.content, message.timestamp, false);
        }
    });
    
    scrollToBottom();
}

// 添加欢迎消息
function addWelcomeMessage() {
    const welcomeMessage = "您好！我是您的AI助手，可以帮您分析债务、制定还款计划或提供财务建议。今天有什么我可以帮您的吗？";
    addAIMessage(welcomeMessage, Date.now(), false);
}

// 添加用户消息
function addUserMessage(content, timestamp = Date.now(), save = true) {
    if (!chatMessages) {
        return;
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message-container user-message-container';
    messageElement.innerHTML = `
        <div class="message user-message">
            ${content}
            <div class="message-time">${formatTime(timestamp)}</div>
        </div>
        <div class="avatar user-avatar">我</div>
    `;
    
    // 插入到打字指示器之前
    // ✅ 安全插入到 typingIndicatorElement 前
    if (chatMessages.contains(typingIndicatorElement)) {
        chatMessages.insertBefore(messageElement, typingIndicatorElement);
    } else {
        chatMessages.appendChild(messageElement);
        chatMessages.appendChild(typingIndicatorElement);
    }
    

    
    if (save) {
        saveUserMessage(content, timestamp);
    }
    
    // 确保滚动到底部
    scrollToBottom();
}

// 添加AI消息
function addAIMessage(content, timestamp = Date.now(), save = true) {
    if (!chatMessages) {
        return;
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message-container bot';
    // 确保元素是可见的
    messageElement.style.display = 'flex';
    messageElement.innerHTML = `
        <div class="avatar bot-avatar">AI</div>
        <div class="message bot-message">
            ${content}
            <div class="message-time">${formatTime(timestamp)}</div>
        </div>
    `;
    
    // 插入到打字指示器之前
    // ✅ 安全插入到 typingIndicatorElement 前
    if (chatMessages.contains(typingIndicatorElement)) {
        chatMessages.insertBefore(messageElement, typingIndicatorElement);
    } else {
        chatMessages.appendChild(messageElement);
        chatMessages.appendChild(typingIndicatorElement);
    }
    

    
    if (save) {
        saveAIMessage(content, timestamp);
    }
    
    // 确保滚动到底部
    scrollToBottom();
    
    return messageElement; // 返回创建的元素
}

// 添加思考者消息
function addThinkerMessage(content, timestamp = Date.now(), save = true) {
    if (!chatMessages) {
        return;
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message-container thinker';
    messageElement.innerHTML = `
        <div class="avatar thinker-avatar">💡</div>
        <div class="message thinker-message">
            ${content}
            <div class="message-time">${formatTime(timestamp)}</div>
        </div>
    `;
    
    // 插入到打字指示器之前
    // ✅ 安全插入到 typingIndicatorElement 前
    if (chatMessages.contains(typingIndicatorElement)) {
        chatMessages.insertBefore(messageElement, typingIndicatorElement);
    } else {
        chatMessages.appendChild(messageElement);
        chatMessages.appendChild(typingIndicatorElement);
    }
    

    
    if (save) {
        saveThinkerMessage(content, timestamp);
    }
    
    // 确保滚动到底部
    scrollToBottom();
}

// 格式化时间
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    
    // 如果是今天，只显示时间
    if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    
    // 如果是今年，显示月日和时间
    if (date.getFullYear() === now.getFullYear()) {
        return date.toLocaleDateString('zh-CN', { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    // 其他情况显示完整日期和时间
    return date.toLocaleDateString('zh-CN', { 
        year: 'numeric',
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// 滚动到底部
function scrollToBottom() {
    if (!chatMessages) {
        // chatMessages元素不存在
        return;
    }
    
    // 使用更简洁有效的方法滚动到底部
    // 确保在DOM更新后再执行滚动
    setTimeout(() => {
        // 直接滚动到最大可能位置
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // 为了确保滚动生效，再添加一个微任务检查
        Promise.resolve().then(() => {
            // 如果第一次滚动没有成功，再尝试一次
            if (chatMessages.scrollTop !== chatMessages.scrollHeight) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        });
    }, 0);
}


// 显示打字指示器
function showTypingIndicator() {
    if (!chatMessages) {
        return;
    }
    
    typingIndicatorElement.style.display = 'flex';
    scrollToBottom();
}

// 隐藏打字指示器
function hideTypingIndicator() {
    if (!chatMessages) {
        return;
    }
    
    typingIndicatorElement.style.display = 'none';
}

// 发送消息到后端
function sendMessageToBackend(content) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            type: 'chat_message',
            content: content,
            conversation_id: currentConversationId
        };
        ws.send(JSON.stringify(message));
    } else {
        hideTypingIndicator();
        addAIMessage('抱歉，当前无法连接到服务器。请稍后重试。');
    }
}

// 处理接收到的WebSocket消息
function handleWebSocketMessage(data) {
    switch (data.type) {
        // case 'start_thinking':
        //     // 开始思考阶段
        //     hideTypingIndicator();
        //     addThinkerMessage('');
        //     break;
            

        case 'user_message':
            // 可选：在聊天窗口显示用户消息（避免重复）
            // 通常前端自己已显示，所以可忽略
            return;

        case 'thinking':
            // 更新思考内容
            hideTypingIndicator(); // 隐藏默认 typing
            updateCurrentThinkerMessage(data.content);
            break;
            
        // case 'start_responding':
        //     // 开始回复阶段
        //     break;
            
        case 'response_chunk':
            // 流式回复内容
            updateCurrentAIMessage(data.content);
            break;
            
        case 'response_end':
            // 回复结束
            finalizeCurrentMessages();
            break;
            
        case 'error':
            // 错误处理
            hideTypingIndicator();
            addAIMessage(data.message);
            break;
            
        default:
            // 未知消息类型: data.type
    }
}

// 添加图片消息到聊天界面
function addImageMessageToChat(imageId) {
    if (!chatMessages) {
        return;
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message-container bot';
    messageElement.innerHTML = `
        <div class="avatar bot-avatar">AI</div>
        <div class="message bot-message">
            <p>我已经收到了您上传的图片:</p>
            <img src="/ai_agent/media/temp/${imageId}/" alt="处理后的图片" style="max-width: 300px; max-height: 300px; border-radius: 8px;">
            <div class="message-time">${formatTime(Date.now())}</div>
        </div>
    `;
    
    // 插入到打字指示器之前
    chatMessages.insertBefore(messageElement, typingIndicatorElement);
    
    // 滚动到底部
    scrollToBottom();
}

// 更新当前思考者消息
function updateCurrentThinkerMessage(content) {
    if (!chatMessages) {
        return;
    }
    
    const thinkerMessages = chatMessages.querySelectorAll('.message-container.thinker');
    if (thinkerMessages.length > 0) {
        const lastThinkerMessage = thinkerMessages[thinkerMessages.length - 1];
        const messageDiv = lastThinkerMessage.querySelector('.thinker-message');
        if (messageDiv) {
            // 只更新内容，保留时间戳
            const timeDiv = messageDiv.querySelector('.message-time');
            messageDiv.innerHTML = content;
            if (timeDiv) {
                messageDiv.appendChild(timeDiv);
            }
        }
    }
    scrollToBottom();
}

// 更新当前AI消息
function updateCurrentAIMessage(chunk) {
    if (!chatMessages) {
        return;
    }

    // ✅ 关键：累积 chunk
    currentAIResponse += chunk;

    // ✅ 只选择可见的 AI 消息容器
    const aiMessages = Array.from(chatMessages.querySelectorAll('.message-container.bot')).filter(el => window.getComputedStyle(el).display !== 'none');
    let messageDiv;

    if (aiMessages.length > 0) {
        const lastAIMessage = aiMessages[aiMessages.length - 1];
        lastAIMessage.style.display = 'flex'; // 确保可见
        messageDiv = lastAIMessage.querySelector('.bot-message');
    } else {
        // 极端情况：创建新的 AI 容器
        const newContainer = document.createElement('div');
        newContainer.className = 'message-container bot';
        newContainer.style.display = 'flex';
        newContainer.innerHTML = `
            <div class="avatar bot-avatar">AI</div>
            <div class="message bot-message"></div>
        `;
        chatMessages.insertBefore(newContainer, typingIndicatorElement);
        messageDiv = newContainer.querySelector('.bot-message');
    }

    if (messageDiv) {
        // ✅ 使用 textContent 防 XSS，设置完整累积内容
        // messageDiv.textContent = currentAIResponse;
        // ✅ 将累积的 Markdown 转为安全 HTML
        const sanitizedHtml = DOMPurify.sanitize(marked.parse(currentAIResponse));
        messageDiv.innerHTML = sanitizedHtml;
    }

    scrollToBottom();
}

// // 更新当前AI消息
// function updateCurrentAIMessage(content) {
//     if (!chatMessages) {
//         console.error('chatMessages元素不存在');
//         return;
//     }
//     console.log('更新AI消息内容:', content);
    
//     const aiMessages = chatMessages.querySelectorAll('.message-container.bot');
//     console.log('找到的AI消息数量:', aiMessages.length);
    
//     if (aiMessages.length > 0) {
//         const lastAIMessage = aiMessages[aiMessages.length - 1];
//         console.log('最后一个AI消息元素:', lastAIMessage);
        
//         // 确保元素是可见的
//         lastAIMessage.style.display = 'flex';
        
//         const messageDiv = lastAIMessage.querySelector('.bot-message');
//         if (messageDiv) {
//             console.log('找到bot-message元素:', messageDiv);
//             console.log('更新前的内容:', messageDiv.innerHTML);
            
//             // 只更新内容，保留时间戳
//             const timeDiv = messageDiv.querySelector('.message-time');
//             if (timeDiv) {
//                 console.log('找到时间戳元素:', timeDiv);
//                 // 获取当前内容（不包括时间戳）
//                 const currentContent = messageDiv.innerHTML.replace(timeDiv.outerHTML, '');
//                 // 累积显示内容而不是替换，保留时间戳
//                 messageDiv.innerHTML = content + timeDiv.outerHTML;
//             } else {
//                 // 如果没有时间戳，直接更新内容
//                 messageDiv.innerHTML = content;
//             }
            
//             console.log('更新后的内容:', messageDiv.innerHTML);
//         } else {
//             console.error('未找到bot-message元素');
//         }
//     } else {
//         console.warn('没有找到AI消息元素，创建新的AI消息');
//         // 如果没有AI消息，创建一个新的
//         addAIMessage(content);
//     }
    
//     scrollToBottom();
// }


function finalizeCurrentMessages() {
    
    // 如果这两个不相等，说明引用失效了！
    if (chatMessages !== document.getElementById('chat-messages')) {
        // ❌ chatMessages 引用已失效！
    }
    // 收到完整消息: currentAIResponse
    hideTypingIndicator();

    // ✅ 只选择可见的 AI 消息容器
    const aiMessages = Array.from(chatMessages.querySelectorAll('.message-container.bot')).filter(el => window.getComputedStyle(el).display !== 'none');

    // 可见的 AI 消息数量: aiMessages.length
    if (aiMessages.length > 0) {
        const lastAIMessage = aiMessages[aiMessages.length - 1];
        const messageDiv = lastAIMessage.querySelector('.bot-message');

        // 操作的 AI 容器: lastAIMessage
        // 当前内容: messageDiv ? messageDiv.textContent : 'null'

        if (messageDiv && currentAIResponse.trim()) {
            // 添加时间戳
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = formatTime(Date.now());
            messageDiv.appendChild(timeDiv);

            // 保存完整消息
            saveAIMessage(currentAIResponse, Date.now());
        }
    }

    // ✅ 重置累积变量
    currentAIResponse = '';

    // 更新历史记录标题（你的原有逻辑）
    // const history = getHistory();
    // if (currentConversationId && history[currentConversationId]) {
    //     if (history[currentConversationId].messages.length === 2) {
    //         const firstUserMessage = history[currentConversationId].messages[0].content;
    //         history[currentConversationId].title = firstUserMessage.length > 20 
    //             ? firstUserMessage.substring(0, 20) + '...' 
    //             : firstUserMessage;
    //         saveHistory(history);
    //         updateHistoryList();
    //     }
    // }
}

// // 完成当前消息
// function finalizeCurrentMessages() {
//     hideTypingIndicator();
    
//     // 保存当前对话
//     const history = getHistory();
//     if (currentConversationId && history[currentConversationId]) {
//         // 更新对话标题（如果是第一条消息）
//         if (history[currentConversationId].messages.length === 2) {
//             const firstUserMessage = history[currentConversationId].messages[0].content;
//             history[currentConversationId].title = firstUserMessage.length > 20 
//                 ? firstUserMessage.substring(0, 20) + '...' 
//                 : firstUserMessage;
//             saveHistory(history);
//             updateHistoryList();
//         }
//     }
// }

// 保存用户消息
function saveUserMessage(content, timestamp) {
    if (!currentConversationId) {
        currentConversationId = Date.now().toString();
    }
    
    const history = getHistory();
    if (!history[currentConversationId]) {
        // 使用用户消息内容作为对话标题，而不是默认的"新对话"
        const title = content.length > 20 ? content.substring(0, 20) + '...' : content;
        history[currentConversationId] = {
            title: title,
            timestamp: timestamp,
            messages: []
        };
    }
    
    history[currentConversationId].messages.push({
        role: 'user',
        content: content,
        timestamp: timestamp
    });
    
    saveHistory(history);
    updateHistoryList(); // 更新历史记录列表以显示新的标题
}

// 保存AI消息
function saveAIMessage(content, timestamp) {
    const history = getHistory();
    if (currentConversationId && history[currentConversationId]) {
        history[currentConversationId].messages.push({
            role: 'ai',
            content: content,
            timestamp: timestamp
        });
        
        saveHistory(history);
    }
}

// 保存思考者消息
function saveThinkerMessage(content, timestamp) {
    const history = getHistory();
    if (currentConversationId && history[currentConversationId]) {
        history[currentConversationId].messages.push({
            role: 'thinker',
            content: content,
            timestamp: timestamp
        });
        
        saveHistory(history);
    }
}

// 获取历史记录
function getHistory() {
    const history = localStorage.getItem('chatHistory');
    return history ? JSON.parse(history) : {};
}

// 保存历史记录
function saveHistory(history) {
    localStorage.setItem('chatHistory', JSON.stringify(history));
}

// 加载历史记录
function loadHistory() {
    updateHistoryList();
}

// 清除设置
function clearSettings() {
    document.getElementById('api-url').value = '';
    document.getElementById('api-key').value = '';
    document.getElementById('model-name').value = '';
}

// 保存设置
function saveSettings() {
    const apiUrl = document.getElementById('api-url').value;
    const apiKey = document.getElementById('api-key').value;
    const modelName = document.getElementById('model-name').value;
    
    // 这里可以添加保存到后端或localStorage的逻辑
    // 暂时只显示一个确认消息
    alert('设置已保存！');
    toggleSettingsModal();
}

// 动态调整聊天框高度的函数
function adjustChatHeight() {
    var navbar = document.querySelector('.navbar');
    var popup = document.getElementById('ai-chat-popup');
    var chatContainer = document.querySelector('#ai-chat-popup .chat-container');
    var chatMessages = document.querySelector('#ai-chat-popup .chat-messages');
    var inputArea = document.querySelector('#ai-chat-popup .input-area');
    
    // 如果没有找到必要的元素，直接返回
    if (!popup || !chatContainer || !chatMessages || !inputArea) return;
    
    // 获取导航栏的高度
    var navbarHeight = navbar ? navbar.offsetHeight : 0;
    
    // 获取滚动位置
    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // 根据滚动位置调整聊天框的高度和位置
    if (scrollTop > navbarHeight) {
        // 当滚动超过导航栏高度时，聊天框扩展到顶部
        popup.style.top = '0px';
        popup.style.height = '100vh';
    } else {
        // 当在页面顶部时，保持原有位置和高度
        popup.style.top = navbarHeight + 'px';
        popup.style.height = 'calc(100vh - ' + navbarHeight + 'px)';
    }
    
    // 动态计算并设置聊天消息区域的高度
    // 获取输入区域的实际高度
    var inputAreaHeight = inputArea.offsetHeight || 80; // 默认80px
    
    // 设置聊天容器的高度为弹窗高度减去一些边距
    var popupHeight = popup.offsetHeight || window.innerHeight;
    chatContainer.style.height = (popupHeight - 20) + 'px'; // 减去一些边距
    
    // 设置聊天消息区域的高度为聊天容器高度减去输入区域高度
    var chatContainerHeight = chatContainer.offsetHeight || (popupHeight - 20);
    chatMessages.style.height = (chatContainerHeight - inputAreaHeight - 20) + 'px'; // 减去输入区域高度和一些边距
}

// 当DOM内容加载完成并且所有资源都加载完毕后再次调整高度
window.addEventListener('load', function() {
    setTimeout(function() {
        adjustChatHeight();
    }, 500); // 延迟500ms确保所有元素都已正确渲染
});

// 页面加载完成后初始化聊天框高度
document.addEventListener('DOMContentLoaded', function() {
    // 延迟执行以确保元素已加载
    setTimeout(function() {
        adjustChatHeight();
        
        // 监听滚动事件，动态调整聊天框高度
        window.addEventListener('scroll', function() {
            adjustChatHeight();
        });
        
        // 监听窗口大小变化事件
        var resizeTimer;
        window.addEventListener('resize', function() {
            // 使用防抖动技术优化性能
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                adjustChatHeight();
            }, 250);
        });
    }, 100);
});


function clearChatMessages() {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    // 保存 typingIndicatorElement
    const hasTyping = chatMessages.contains(typingIndicatorElement);
    
    // 清空所有子节点
    while (chatMessages.firstChild) {
        chatMessages.removeChild(chatMessages.firstChild);
    }
    
    // 重新添加 typingIndicatorElement
    chatMessages.appendChild(typingIndicatorElement);
}


// 用于存储待发送的图片ID
let pendingImageId = null;

// 新增：处理图片上传的函数
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('image', file);
    
    // 发送图片到后端
    fetch('/ai_agent/api/upload-image/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.image_id) {
            // 图片上传成功，保存图片ID等待发送
            pendingImageId = data.image_id;
            console.log('图片上传成功，ID:', pendingImageId);
            // 在输入框中显示图片预览
            showPendingImagePreview(data.image_id);
        } else {
            console.error('图片上传失败:', data.error);
            alert('图片上传失败，请重试');
        }
    })
    .catch(error => {
        console.error('上传错误:', error);
        alert('上传过程中出现错误');
    })
    .finally(() => {
        // 重置文件输入框的值，确保可以重复上传同一张图片
        event.target.value = '';
    });
}

// 显示待发送图片预览
function showPendingImagePreview(imageId) {
    // 获取预览容器
    const container = document.getElementById('pending-image-container');
    container.style.display = 'block';
    
    // 调整textarea的padding，为图片预览留出空间
    if (messageInput) {
        messageInput.style.paddingLeft = '70px';
    }
    
    // 清空容器内容
    container.innerHTML = '';
    
    // 创建预览元素
    const previewElement = document.createElement('div');
    previewElement.className = 'pending-image-preview';
    previewElement.id = 'pending-image-preview';
    
    // 创建图片元素
    const img = document.createElement('img');
    img.src = `/ai_agent/media/temp/${imageId}/`;
    img.alt = '待发送图片';
    
    // 图片加载完成后调整尺寸
    img.onload = function() {
        // 确保图片不会超出预览容器
        // 宽图：限制宽度，高度自适应
        if (this.naturalWidth > this.naturalHeight) {
            this.style.maxWidth = '100%';
            this.style.height = 'auto';
        } 
        // 高图：限制高度，宽度自适应
        else {
            this.style.width = 'auto';
            this.style.maxHeight = '100%';
        }
        
        // 确保图片不会超出容器的最大尺寸
        if (this.width > this.parentElement.clientWidth) {
            this.style.maxWidth = '100%';
            this.style.height = 'auto';
        }
        
        if (this.height > this.parentElement.clientHeight) {
            this.style.width = 'auto';
            this.style.maxHeight = '100%';
        }
    };
    
    // 创建删除按钮
    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-pending-image';
    removeBtn.innerHTML = '×';
    removeBtn.onclick = function(event) {
        // 阻止事件冒泡，防止点击删除按钮时关闭整个聊天窗口
        event.stopPropagation();
        
        // 移除图片预览
        container.style.display = 'none';
        container.innerHTML = '';
        pendingImageId = null;
        
        // 恢复textarea的padding
        if (messageInput) {
            messageInput.style.paddingLeft = '15px';
        }
    };
    
    // 组装元素
    previewElement.appendChild(img);
    previewElement.appendChild(removeBtn);
    container.appendChild(previewElement);
}

// 移除待发送图片
function removePendingImage() {
    const container = document.getElementById('pending-image-container');
    container.style.display = 'none';
    container.innerHTML = '';
    pendingImageId = null;
    
    // 恢复textarea的padding
    if (messageInput) {
        messageInput.style.paddingLeft = '15px';
    }
}

// 修改submitChat函数以处理待发送的图片
function submitChat() {
    if (!messageInput) {
        console.error('messageInput元素不存在');
        return;
    }
    
    const content = messageInput.value.trim();
    // 检查是否有待发送的图片
    const hasPendingImage = pendingImageId !== null;
    console.log('检查是否有待发送的图片:', hasPendingImage);
    console.log('待发送图片ID:', pendingImageId);
    temp_image_id = pendingImageId;
    
    // 如果既没有文字也没有图片，则不发送
    if (!content && !hasPendingImage) return;
    
    // 添加用户消息（包括文字和图片）
    if (content) {
        addUserMessage(content);
    }
    
    if (hasPendingImage) {
        // 添加用户图片消息到聊天界面
        addUserImageMessage(pendingImageId);
        // 清除待发送的图片
        removePendingImage();
    }
    
    // 清空输入框
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // 3. ✅ 关键：创建新的 AI 消息容器（为本轮对话准备）
    const aiContainer = document.createElement('div');
    aiContainer.className = 'message-container bot';
    aiContainer.style.display = 'flex'; // 确保可见
    aiContainer.innerHTML = `
        <div class="avatar bot-avatar">AI</div>
        <div class="message bot-message">
            <!-- 流式内容将在这里更新 -->
        </div>
    `;
    
    // 插入到 typing-indicator 之前
    // ✅ 直接使用全局 typingIndicatorElement
    if (chatMessages && chatMessages.contains(typingIndicatorElement)) {
        chatMessages.insertBefore(aiContainer, typingIndicatorElement);
    } else {
        // 极端情况：重新添加 typingIndicatorElement
        chatMessages.appendChild(aiContainer);
        chatMessages.appendChild(typingIndicatorElement);
    }
    
    
    // 显示打字指示器
    showTypingIndicator();
    
    // 发送消息到后端（包括文字和图片）
    if (hasPendingImage) {
        sendImageAndTextMessage(content, temp_image_id);
        console.log('发送图片和文字消息:', content, temp_image_id);
    } else {
        sendMessageToBackend(content);
        console.log('发送文字消息:', content);
    }
}

// 发送图片和文字消息到后端
function sendImageAndTextMessage(content, imageId) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            type: 'image_text_message',
            content: content,
            image_id: imageId,
            conversation_id: currentConversationId
        };
        ws.send(JSON.stringify(message));
    } else {
        console.error('WebSocket未连接');
        hideTypingIndicator();
        addAIMessage('抱歉，当前无法连接到服务器。请稍后重试。');
    }
}

// 新增：添加用户图片消息到聊天界面
function addUserImageMessage(imageId) {
    if (!chatMessages) {
        console.error('chatMessages元素不存在');
        return;
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message-container user-message-container';
    messageElement.innerHTML = `
        <div class="message user-message">
            <img src="/ai_agent/media/temp/${imageId}/" alt="上传的图片" style="max-width: 300px; max-height: 300px; border-radius: 8px;">
            <div class="message-time">${formatTime(Date.now())}</div>
        </div>
        <div class="avatar user-avatar">我</div>
    `;
    
    // 插入到打字指示器之前
    if (chatMessages.contains(typingIndicatorElement)) {
        chatMessages.insertBefore(messageElement, typingIndicatorElement);
    } else {
        chatMessages.appendChild(messageElement);
        chatMessages.appendChild(typingIndicatorElement);
    }
    
    // 保存图片消息
    saveUserImageMessage(imageId, Date.now());
    
    // 滚动到底部
    scrollToBottom();
}

// 新增：保存用户图片消息
function saveUserImageMessage(imageId, timestamp) {
    if (!currentConversationId) {
        currentConversationId = Date.now().toString();
    }
    
    const history = getHistory();
    if (!history[currentConversationId]) {
        history[currentConversationId] = {
            title: '图片消息',
            timestamp: timestamp,
            messages: []
        };
    }
    
    history[currentConversationId].messages.push({
        role: 'user',
        content: `[图片: ${imageId}]`,
        image_id: imageId,
        timestamp: timestamp
    });
    
    saveHistory(history);
    updateHistoryList();
}

