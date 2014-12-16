UnlockScreen = function(unlock_url, csrf_token, ajax, g){
    var p = this;

    p.unlock_url = unlock_url;
    p.token = csrf_token;
    p.ajax = ajax; // if true, redirect after unlock, otherwise just hide #lock_shadow
    p.g = g; // may not be here if this is not ajax

    p.items = {
        pin: $("#pin"),
        keys: $(".key.number", "#keypad_container"),
        enter: $(".key.enter", "#keypad_container"),
        clear: $(".key.clear", "#keypad_container"),

        switch_button: $("#switch_pin_password"),
        switch_to_password: $(".password", "#switch_pin_password"),
        switch_to_pin: $(".pin", "#switch_pin_password"),
        pin_container: $("#pin_container"),
        password_container: $("#password_container"),

        email: $("#id_email"),
        password: $("#id_password"),

        /* only for ajax lock */
        lock_shadow: $("#lock_shadow"),
        lock_content: $("#unlock_dialog_container")
    };

    // current state (showing password or pin)
    p.password_visible = false;
    p.pin_length = parseInt(p.items.pin.attr('maxlength'));
    p.key_event_id = "unlock-confirm";

    //
    // methods
    //
    p.focus_pin = function(){
        setTimeout(function(){
            p.items.pin.focus();
        }, 300);
    };

    p.toggle_screen = function(show){
        if(show){
            p.items.lock_shadow.parent().show();
            p.items.lock_shadow.show();
            p.items.lock_content.show();

            // handle z-indexes so that keypad won't be under any existing dialog
            window.last_dialog_zindex += 1;
            p.items.lock_shadow.css("z-index", ++window.last_dialog_zindex);
            p.items.lock_content.css("z-index", ++window.last_dialog_zindex);

            p.clear_pin();
            p.focus_pin();

            p.bind_enter();
        }
        else{
            p.items.lock_shadow.parent().hide();
            p.items.lock_shadow.hide();
            p.items.lock_content.hide();

            p.unbind_enter();
        }
    };

    p.unbind_enter = function(){
        window.keyboard.remove(p.key_event_id);
    };

    p.bind_enter = function(){
        p.unbind_enter();
        window.keyboard.add(p.key_event_id, 'enter', p.unlock);
    };

    p.key = function(){
        var key = $(this);
        var number = key.attr('data-number');

        // insert this number to pin and keep focus
        var pin_val = p.items.pin.val();

        if(pin_val.length >= p.pin_length) return;

        p.items.pin
            .val('')
            .val(pin_val + number);

        p.focus_pin();
    };

    p.unlock = function(e){
        e.preventDefault();
        e.stopPropagation();

        // assemble the data for sending
        var data = {
            pin: p.items.pin.val(),
            email: p.items.email.val(),
            password: p.items.password.val(),
            unlock_type: p.password_visible ? 'password' : 'pin'
        };

        // send unlock request to server
        send_data(unlock_url, data, p.token, function(response){
            if(response.status != 'ok'){
                custom_dialog(
                    gettext("Could not unlock"),
                    response.message, 300,
                    {
                        ok: gettext("OK"),
                        ok_action: function(){
                            p.clear_pin();
                            p.focus_pin();

                            p.bind_enter();
                        }
                    }
                );
            }
            else{
                if(p.ajax){
                    if(p.ajax){
                        p.toggle_screen(false);
                        p.switch_user_data(response);

                        window.session_locked = false;
                    }
                }
                else{
                    window.location.href = response.redirect_url;
                }
            }
        });
    };

    p.switch_user_data = function(response){
        // change user id and user name
        p.g.data.user_name = response.user_name;
        p.g.data.user_id = response.user_id;
        p.g.csrf_token = response.csrf_token;
        p.token = response.csrf_token;

        $("a.button-text", "#user_button").text(p.g.data.user_name);

        // TODO: change user data and redraw terminal (no relevant settings so far)
    };

    p.clear_pin = function(){
        p.items.pin.val("");
    };

    //
    // init
    //

    // capture links for locking
    if(ajax){
        $("a#switch_user").click(function(e){
            e.preventDefault();

            var lock_url = $(this).attr('href');

            send_data(lock_url, {}, p.token, function(response){
                if(response.status != 'ok'){
                    error_message(gettext("Locking failed"),
                        response.message);
                }
                else{
                    // lock the screen
                    p.toggle_screen(true);
                    window.session_locked = true;
                }
            });
        });
    }

    // bind events on keys
    p.items.keys.unbind().click(p.key);

    // enter: send the 'unlock' to server and when
    p.items.enter.unbind().click(p.unlock);

    // clear button: clear pin input
    p.items.clear.unbind().click(function(){
        p.clear_pin();
        p.focus_pin();
    });

    // switch button
    p.items.switch_button.unbind().click(function(e){
        e.preventDefault();
        e.stopPropagation();

        if(p.password_visible){
            p.items.pin_container.show();
            p.items.password_container.hide();
            p.items.switch_to_password.show();
            p.items.switch_to_pin.hide();
        }
        else{
            p.items.pin_container.hide();
            p.items.password_container.show();
            p.items.switch_to_password.hide();
            p.items.switch_to_pin.show();
        }

        p.password_visible = !p.password_visible;
    });

    p.clear_pin();
    p.focus_pin();

    // keys (only for static html)
    window.keyboard.add('unlock-confirm', 'enter', p.unlock);
};