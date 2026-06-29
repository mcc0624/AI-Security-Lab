/* AI+安全实训 - 前端 JavaScript */
/* 学生可以自由修改此文件，增加前端交互功能 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('用户信息管理平台已加载');

    // 登录页表单处理
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // 前端也可以做校验，但真正的安全校验应在后端
            console.log('登录请求已提交');
        });
    }
});
