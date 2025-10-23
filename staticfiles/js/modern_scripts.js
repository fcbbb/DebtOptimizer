// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('modern_scripts.js 已加载');
    
    // 添加可爱的装饰元素
    addDecorations();
    
    // 为所有按钮添加点击特效
    addButtonEffects();
    
    // 初始化AJAX功能
    initAjaxFunctions();
});

// 初始化AJAX功能
function initAjaxFunctions() {
    console.log('初始化AJAX功能...');
    
    // 为所有切换状态按钮添加AJAX事件
    const toggleButtons = document.querySelectorAll('.toggle-status-btn');
    const contractReminderButtons = document.querySelectorAll('.contract-reminder-btn');
    
    console.log('找到切换状态按钮:', toggleButtons.length);
    console.log('找到签约提醒按钮:', contractReminderButtons.length);
    
    // 处理签约提醒按钮的点击事件
    contractReminderButtons.forEach(button => {
        console.log('为签约提醒按钮绑定事件:', button.dataset.customerId);
        
        button.addEventListener('click', function(event) {
            const customerId = this.dataset.customerId;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         document.querySelector('[name=csrf-token]')?.content || 
                         this.dataset.csrf;
            
            console.log('点击签约提醒按钮，客户ID:', customerId, 'CSRF令牌:', !!csrfToken);
            
            // 防止默认行为
            event.preventDefault();
            
            // 保存原始文本和类名
            const originalText = this.textContent;
            const originalClassName = this.className;
            
            // 显示加载状态
            this.textContent = '处理中...';
            this.disabled = true;
            
            // 创建表单数据
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            // 发送AJAX请求
            fetch(`/core/customer/${customerId}/contract-reminder/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('收到响应状态:', response.status);
                if (!response.ok) {
                    return response.text().then(text => {
                        console.error('响应错误:', text);
                        throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('收到响应数据:', data);
                // 恢复按钮状态
                this.disabled = false;
                
                if (data.success) {
                    // 更新按钮状态
                    this.textContent = '已处理';
                    this.classList.remove('btn-secondary');
                    this.classList.add('btn-success');
                    
                    // 检查是否所有客户都已处理完成
                    if (data.all_completed) {
                        // 隐藏签约提醒区域，显示完成消息
                        const reminderSection = document.querySelector('.contract-reminders-section');
                        if (reminderSection) {
                            reminderSection.innerHTML = `
                                <div class="text-center py-4">
                                    <h4>🎉 所有签约提醒已处理完成！</h4>
                                    <p class="text-muted">太棒了！所有客户的签约提醒都已处理完成。</p>
                                </div>
                            `;
                        }
                        // 显示庆祝弹窗
                        showCelebration();
                    } else {
                        // 只显示小提示，不弹窗
                        console.log('签约提醒处理完成，但还有未处理的客户');
                    }
                } else {
                    console.warn('签约提醒操作未成功:', data);
                    alert('操作失败: ' + (data.error || '未知错误'));
                    // 恢复原始状态
                    this.innerHTML = originalText;
                }
            })
            .catch(error => {
                console.error('请求失败:', error);
                // 恢复按钮状态
                this.disabled = false;
                this.innerHTML = originalText;
                alert('操作失败: ' + error.message);
            });
        });
    });

    // 处理切换状态按钮的点击事件
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const customerId = this.dataset.customerId;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         document.querySelector('[name=csrf-token]')?.content || 
                         this.dataset.csrf;
            
            console.log('点击切换状态按钮，客户ID:', customerId, 'CSRF令牌:', !!csrfToken);
            
            // 防止默认行为
            event.preventDefault();
            
            // 保存原始文本和类名
            const originalText = this.textContent;
            const originalClassName = this.className;
            
            // 显示加载状态
            this.textContent = '处理中...';
            this.disabled = true;
            
            // 创建表单数据
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            // 发送AJAX请求
            fetch(`/core/customer/${customerId}/toggle-status/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                // 恢复按钮状态
                this.disabled = false;
                this.innerHTML = originalText;
                
                if (data.success) {
                    // 更新按钮状态
                    if (data.is_completed) {
                        this.textContent = '已完成';
                        this.classList.remove('btn-secondary');
                        this.classList.add('btn-success');
                    } else {
                        this.textContent = '标记完成';
                        this.classList.remove('btn-success');
                        this.classList.add('btn-secondary');
                    }
                    
                    // 如果全部完成且是首次完成，显示庆祝弹窗
                    if (data.all_completed && data.show_celebration) {
                        showCelebration();
                    }
                } else {
                    console.warn('操作未成功:', data);
                    alert('操作失败: ' + (data.error || '未知错误'));
                }
            })
            .catch(error => {
                console.error('请求失败:', error);
                // 恢复按钮状态
                this.disabled = false;
                this.innerHTML = originalText;
                alert('操作失败: ' + error.message);
            });
        });
    });

    console.log('所有按钮事件绑定完成');
}

// 添加可爱的装饰元素
function addDecorations() {
    // 创建第一个装饰元素
    const decoration1 = document.createElement('div');
    decoration1.className = 'decoration decoration-1';
    document.body.appendChild(decoration1);
    
    // 创建第二个装饰元素
    const decoration2 = document.createElement('div');
    decoration2.className = 'decoration decoration-2';
    document.body.appendChild(decoration2);
}

// 为按钮添加点击特效
function addButtonEffects() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        // 排除toggle-status-btn和contract-reminder-btn，因为它们已经有AJAX处理
        if (button.classList.contains('toggle-status-btn') || button.classList.contains('contract-reminder-btn')) {
            return; // 跳过这些按钮
        }
        
        button.addEventListener('click', function(e) {
            // 创建点击波纹效果
            createRipple(e, this);
        });
        
        // 保存按钮原始文本
        button.dataset.originalText = button.innerHTML;
    });
}

// 创建点击波纹效果
function createRipple(e, button) {
    // 移除之前的波纹
    const existingRipple = button.querySelector('.ripple');
    if (existingRipple) {
        existingRipple.remove();
    }
    
    // 获取点击位置
    const x = e.clientX - e.target.getBoundingClientRect().left;
    const y = e.clientY - e.target.getBoundingClientRect().top;
    
    // 创建波纹元素
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    
    // 添加到按钮
    button.appendChild(ripple);
    
    // 设置波纹大小
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;
    
    ripple.style.width = ripple.style.height = `${diameter}px`;
    ripple.style.left = `${x - radius}px`;
    ripple.style.top = `${y - radius}px`;
    
    // 动画结束后移除波纹
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// 显示庆祝动画
function showCelebration() {
    // 随机选择一条鼓励语
    const compliments = [
        '太棒了！你做到了！',
        '超级厉害！继续加油！',
        '完美完成！给自己一个赞！',
        '太优秀了！效率真高！',
        '哇塞！你真是个小能手！',
        '做得漂亮！再接再厉！',
        '太赞了！你真的很棒！',
        '出色的工作！继续保持！',
        '完美！你是最棒的！',
        '太厉害了！为你骄傲！'
    ];
    
    const randomCompliment = compliments[Math.floor(Math.random() * compliments.length)];
    
    // 创建庆祝元素
    const celebration = document.createElement('div');
    celebration.className = 'celebration';
    celebration.style.zIndex = '9999';
    celebration.innerHTML = `
        <h2>🎉 成功啦！🎉</h2>
        <p>${randomCompliment}</p>
        <button class="btn btn-primary mt-3" id="closeCelebration">太棒了！</button>
    `;
    
    // 添加到页面
    document.body.appendChild(celebration);
    
    // 添加关闭按钮事件
    document.getElementById('closeCelebration').addEventListener('click', function() {
        celebration.style.opacity = '0';
        celebration.style.transform = 'translate(-50%, -50%) scale(0.8)';
        celebration.style.transition = 'all 1s ease';
        
        setTimeout(() => {
            celebration.remove();
        }, 1000);
    });
    
    // 自动关闭
    setTimeout(() => {
        if (celebration.parentElement) {
            celebration.remove();
        }
    }, 5000);
}

// 添加波纹效果的CSS
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple {
        to {
            transform: scale(2.5);
            opacity: 0;
        }
    }
    
    .celebration {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: #fff;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        text-align: center;
        max-width: 90%;
        z-index: 9999;
        animation: popIn 0.5s ease;
        border: 3px solid #ff9aa2;
    }
    
    @keyframes popIn {
        from {
            transform: translate(-50%, -50%) scale(0.8);
            opacity: 0;
        }
        to {
            transform: translate(-50%, -50%) scale(1);
            opacity: 1;
        }
    }
    
    .decoration {
        position: fixed;
        z-index: -1;
        opacity: 0.1;
        pointer-events: none;
    }
    
    .decoration-1 {
        top: 10%;
        right: 5%;
        width: 100px;
        height: 100px;
        background: linear-gradient(45deg, #ff9aa2, #ffd1dc);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    
    .decoration-2 {
        bottom: 10%;
        left: 5%;
        width: 80px;
        height: 80px;
        background: linear-gradient(45deg, #87ceeb, #b0e0e6);
        border-radius: 50%;
        animation: float 8s ease-in-out infinite reverse;
    }
    
    @keyframes float {
        0%, 100% {
            transform: translateY(0px);
        }
        50% {
            transform: translateY(-20px);
        }
    }
`;

document.head.appendChild(style);