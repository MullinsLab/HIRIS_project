function prep_upload_progress_bar(form_name, file_input_name, progress_bar_name, post_url, redirect_url){
    const upload_form = document.getElementById(form_name);
    const input_file = document.getElementById(file_input_name);
    const progress_bar = document.getElementById(progress_bar_name);
    console.log('started script');

    $("#"+form_name).bind( "submit", function(e) {
        console.log('hit form');
        e.preventDefault();
        var formData = new FormData(this);
        const media_data = input_file.files[0];
        if(media_data != null){
            // console.log(media_data);
            progress_bar.classList.remove("not-visible");
        }

        $.ajax({
            type: 'POST',
            url: post_url,
            data: formData,
            dataType: 'json',
            beforeSend: function(){
            },
            xhr:function(){
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', e=>{
                    if(e.lengthComputable){
                        const percentProgress = (e.loaded/e.total)*100;
                        // console.log(percentProgress);
                        progress_bar.innerHTML = `<div class="progress-bar progress-bar-striped bg-success" 
                role="progressbar" style="width: ${percentProgress}%" aria-valuenow="${percentProgress}" aria-valuemin="0" 
                aria-valuemax="100"></div>`
                    }
                });
                return xhr
            },
            success: function(response){
                window.location = redirect_url;
            },
            error: function(err){
                console.log(err);
            },
            cache: false,
            contentType: false,
            processData: false,
        });
    });
};