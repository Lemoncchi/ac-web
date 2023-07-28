function downloadWithLocalStorage(cloud_file_id,current_user_username,urlroute) {
    var localStorageData = localStorage.getItem(current_user_username);

    //alert(urlroute)
    // 创建一个隐藏的表单元素
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = urlroute;


    // 创建一个隐藏的input元素，将LocalStorage数据作为值
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'privatekey';
    input.value = localStorageData;


    // 将input元素添加到表单中
    form.appendChild(input);

    //// 将表单添加到页面，并实际提交
    document.body.appendChild(form);
    form.submit();
}