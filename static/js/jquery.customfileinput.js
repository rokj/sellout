(function($){
    $.fn.customFileInput = function() {
        return this.each(function(){
            var parent = $(this).parent();

            var container = $("<div>", {'class': "custom-file-input"});
            container.css("position", "relative");
            container.height($(this).height());

            // append a style-able browse button
            var browse_button = $("<input>", {
                type: 'button',
                "class": 'custom-file-input',
                value: gettext("Browse") + "..."
            });
            container.prepend(browse_button);

            // append the container to current button's parent
            parent.prepend(container);

            // make the original input transparent and float it above the parent
            $(this).css("opacity", 0);
            $(this).css("position", "absolute");
            $(this).css("z-index", "2");

            // move it over the browse button
            $(this).css("left", "0");

            // make the whole thing as wide as the button
            $(this).width(browse_button.outerWidth());
            $(this).height(browse_button.outerHeight());
        });
    };
}(jQuery));