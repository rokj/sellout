(function($){
    $.fn.simpleMenu = function(content) {
        // register events & behavior
        return this.each(function(){
            var p = $(this);

            p
                .data({menu_shown: false})
                .click(function(){
                    if(!p.data().menu_shown){
                        p.data({menu_shown: true});
                        content.removeClass("menu-hidden", true); // (animate = true)
                    }
                    else{
                        p.data({menu_shown: false});
                        content.addClass("menu-hidden", true);
                    }
                });
        });
    };
}(jQuery));