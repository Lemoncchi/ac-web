
function localStorage_set(data){

    // 获取表单数据
    if(!formData){
        var formData = new FormData();
        formData.append('username', 'your_username');
    }   
    else{
        formData.append('username', 'your_username');
    }
        // 将数据存储到 localStorage 中
    for (const [key, value] of Object.entries( data ) ) {
        localStorage.setItem(key, value);
    }
}
