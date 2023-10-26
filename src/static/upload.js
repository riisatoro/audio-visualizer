$(document).ready(function() {
    $('.file-form').on('submit', function(e){
        e.preventDefault();
        jQuery.ajax({
        type: 'POST',
        url:"/upload",
        data: new FormData($(".file-form")[0]),
        processData: false,
        contentType: false,
        success: function(response) {
            window.location.replace(response.redirect_url);
         }
    });
    })
});
