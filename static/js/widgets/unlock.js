UnlockScreen = function(unlock_url, original_url, csrf_token){
    var p = this;

    p.unlock_url = unlock_url;
    p.original_url = original_url;
    p.token = csrf_token;

    p.items = {
        pin: $("#pin"),
        keys: $(".key.number", "#keypad_container"),
        enter: $(".key.enter", "#keypad_container"),
        clear: $(".key.clear", "#keypad_container")
    };

    //
    // methods
    //
    p.key = function(){
        var key = $(this);
        var number = key.attr('data-number');

        // insert this number to pin and keep focus
        var pin_val = p.items.pin.val();

        p.items.pin
            .val('')
            .focus()
            .val(pin_val + number);
    };

    //
    // init
    //

    // bind events on keys
    p.items.keys.unbind().click(p.key);

    // enter: send the 'unlock' to server and when
    p.items.enter.unbind().click(function(){
        send_data(unlock_url, {pin: p.items.pin.val()}, p.token, function(response){
            console.log(response);

            if(response.status != 'ok'){
                error_message(gettext("Unlock failed"), response.message);
            }
            else{
                console.log(response);
                window.location.href = original_url;
            }
        });
    });

    p.items.clear.unbind().click(function(){
        p.items.pin.val("").focus();
    });

    p.items.pin.focus();
};