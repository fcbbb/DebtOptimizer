document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(button => {
        button.addEventListener('click', function() {
            const customerId = this.dataset.customerId;
            const csrfToken = this.dataset.csrf;
            
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            fetch(`/core/customer/${customerId}/toggle-status/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.status === 403) {
                    return response.text().then(text => {
                        throw new Error('权限错误 (403)');
                    });
                }
                if (response.status === 404) {
                    return response.text().then(text => {
                        throw new Error('资源不存在 (404)');
                    });
                }
                if (!response.ok) {
                    throw new Error(`HTTP错误: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    if (data.is_completed) {
                        this.textContent = '已完成';
                        this.classList.remove('btn-secondary');
                        this.classList.add('btn-success');
                    } else {
                        this.textContent = '标记完成';
                        this.classList.remove('btn-success');
                        this.classList.add('btn-secondary');
                    }
                    
                    if (data.all_completed && data.show_celebration) {
                        location.reload();
                    }
                }
            })
            .catch(error => {
                if (!error.message.includes('权限错误') && !error.message.includes('资源不存在')) {
                    alert('操作失败，请重试');
                }
            });
        });
    });
});