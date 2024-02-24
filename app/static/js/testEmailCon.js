function testEmail(){
    testStatus = document.getElementById('test-email-status');
    testStatus.innerHTML = 'testing connection...';
    $.ajax({
        url: test_email_url,
        type: 'POST', 
        success: function(data){
            console.log(data)
            testStatus.innerHTML = data;
        }
    })
}
