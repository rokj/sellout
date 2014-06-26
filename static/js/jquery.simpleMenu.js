(function($){
    $.fn.simpleMenu = function(content){
        var button = $(this);

        var button_class = "simple-menu-button";
        var opened_class = "opened";

        // simple menu class: send close message to all other menus on click
        button.addClass(button_class);

        // unique message
        var id = "simpleMenu-" + Math.round(Math.random()*1e+10).toString();

        function close(){
            button.data({menu_shown: false});
            button.removeClass(opened_class);
            content.slideUp("fast");
            $(document).unbind("click." + id);
        }

        function open(){
            button.data({menu_shown: true});
            button.addClass(opened_class);
            content.slideDown("fast");

            $(document).on("click."+id, close);
        }

        // register events & behavior
        button
            .data({menu_shown: false})
            .click(function(e){
                // don't click on document
                e.stopPropagation();

                // close other menus
                $("." + button_class).not(button).each(function(){
                    if($(this).hasClass("opened")){
                        $(this).click();
                    }
                });

                if(!button.data().menu_shown) open();
                else close();
            });
    };
}(jQuery));