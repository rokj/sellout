/*
Setup steps:
 - welcome: thanks, invite to use a guided setup and tutorial
   + next step
   - skip the tutorial

 - create: taxes

 - create: category

 - create: product

 - create: register

 - change PIN (+ explanation for inviting users)

 - visit terminal

 - search for product (only read-only show)
 - bill options
 - finish bill (and mention bill management)

 - end: go to home, show support and 'run tutorial' buttons

*/
Tutorial = function(step, save_url){
    var p = this;

    p.current_step = step;
    p.save_url = save_url;

    p.items = {
        start_button: $("#start_tutorial"),

        dialog: $("#tutorial_dialog").appendTo("body"),

        title: $("#tutorial_title"),
        text: $("#tutorial_text"),
        button_container: $("#tutorial_dialog_buttons"),
        next_button: $("#tutorial_next"),
        prev_button: $("#tutorial_prev"),
        cancel_button: $("#tutorial_cancel"),

        shadow: $("<div>", {"class": "tutorial-shadow hidden"}).appendTo($("body")),

        disable_div: $("<div>", {id: "disable_elements"}),

        help_image: $("#tutorial_help_image"),

        arrow: $("#tutorial_arrow")
    };

    p.shadows = []; // holds shadow divs that 'highlight' an element (dim all other elements, actually)
                    // indexes: 0 - top, 1 - left, 2 - right, 3 - bottom

    p.HL_MARGIN = 5; // distance from the elements in pixels
    p.DLG_MARGIN = 20; // distance between the dialog and the thing it points to

    p.resize_timeout = null;

    // steps:
    //
    // methods
    //

    p.get_size = function(element, outer){
        if(!element) return null;

        if(outer) return { width: element.outerWidth(), height: element.outerHeight() };
        else return { width: element.width(), height: element.height() };
    };

    p.step = function(title, text, element, position, disabled, prev_btn, next_btn, pre_callback, post_callback){
        p.items.dialog.show();
        p.remove_highlight();

        if(element) element = $(element); // element is a string containing a selector

        var dlg_size;

        // things to do before
        if(pre_callback) pre_callback();

        // set texts
        p.items.title.html(title);
        p.items.text.html(text);

        if(next_btn) p.items.next_button.show().val(next_btn);
        else p.items.next_button.hide();

        if(prev_btn) p.items.prev_button.show().val(prev_btn);
        else p.items.prev_button.hide();

        if(next_btn && !prev_btn) p.items.button_container.addClass("single-button");
        else p.items.button_container.removeClass("single-button");

        p.items.prev_button.unbind().click(function(){
            p.current_step -= 2;
            p.next_step();
        });

        if(element){
            p.position_dialog(element, position, disabled);
        }
        else{
            p.highlight_element(null, false);
            p.items.arrow.hide();

            // there's no element, center the dialog
            dlg_size = p.get_size(p.items.dialog, true);

            p.items.dialog
                .css("left", "50%")
                .css("margin-left", -dlg_size.width/2 + "px")
                .css("top", "50%")
                .css("margin-top", -dlg_size.height/2 + "px");
        }

        // things to do after
        if(post_callback) p.items.next_button.unbind().click(post_callback);
        else p.items.next_button.unbind().click(p.next_step);

        // common to all steps
        p.items.cancel_button.unbind().click(p.help_slide);
    };

    p.next_step = function(){
        // execute post_callback of the previous step, if there's one
        s = p.tutorial_steps[p.current_step];
        p.step(s.title, s.text, s.element, s.pos, s.disabled, s.prev_btn, s.next_btn, s.pre_callback, s.post_callback);

        p.current_step += 1;
    };

    p.position_dialog = function(element, position, disabled){
        var dlg_size, element_size, element_pos;

        element_size = p.get_size(element, true);
        element_pos = element.offset();

        // position the shadows
        p.remove_highlight();
        p.highlight_element(element, disabled);

        // remove center positioning
        p.items.dialog.css("margin-left", "auto").css("margin-top", "auto");

        dlg_size = p.get_size(p.items.dialog, true);

        // dialog position:
        var x, y; // the new dialog position

        switch(position){
            default:
            case 'right':
                x = element_pos.left + element_size.width + p.DLG_MARGIN;
                y = element_pos.top + element_size.height/2 - dlg_size.height/2;
                break;
            case 'below':
                x = element_pos.left + element_size.width/2 - dlg_size.width/2;
                y = element_pos.top + element_size.height + p.DLG_MARGIN;
                break;
            case 'left':
                x = element_pos.left - dlg_size.width - p.DLG_MARGIN;
                y = element_pos.top + element_size.height/2 - dlg_size.height/2;
                break;
            case 'above':
                x = element_pos.left + element_size.width/2 - dlg_size.width/2;
                y = element_pos.top - dlg_size.height - p.DLG_MARGIN;
                break;
        }

        // check if the element will be positioned outside the window
        var win_size = p.get_size($(window), false);

        if(x < p.DLG_MARGIN) x = p.DLG_MARGIN;
        else if(x + dlg_size.width > win_size.width - p.DLG_MARGIN) x = win_size.width - dlg_size.width - p.DLG_MARGIN;

        if(y < p.DLG_MARGIN) y = p.DLG_MARGIN;
        else if(y + dlg_size.height > win_size.height - p.DLG_MARGIN) y = win_size.height - dlg_size.height - p.DLG_MARGIN;

        p.items.dialog.offset({left: x, top: y});

        var ax, ay; // the arrow position, relative to the element

        switch(position){
            default:
            case 'right':
                ax = 0;
                ay = element_pos.top + element_size.height/2 - y;
                break;
            case 'below':
                ax = element_pos.left + element_size.width/2 - x;
                ay = 0;
                break;
            case 'left':
                ax = dlg_size.width;
                ay = element_pos.top + element_size.height/2 - y;
                break;
            case 'above':
                ax = element_pos.left + element_size.width/2 - x;
                ay = dlg_size.height;
                break;
        }

        p.items.arrow.show();
        p.items.arrow.css("left", ax);
        p.items.arrow.css("top", ay);
    };

    p.help_slide = function(){
        p.step(
            gettext("Help"), // title,
            gettext("In case you want to take this tutorial again, look for this icon on your dashboard: "), // text,
            null, // element,
            null, // position,
            null, // disabled,
            null, // prev_btn,
            gettext("Got it"), // next_btn,
            function(){ // pre_callback,
                p.items.help_image.show();
                p.items.cancel_button.hide();
            },
            function(){ // post_callback
                p.items.help_image.hide();
                p.items.cancel_button.show();
                p.stop_tutorial();
            });
    };

    p.stop_tutorial = function(){
        p.remove_highlight();
        p.items.dialog.hide("fast");

        p.save_tutorial_status(null);

        // unbind all events that might be waiting
        $("#add_project").unbind("click.tutorial");
        $(document)
            .unbind("task-initialized")
            .unbind("time-saved")
            .unbind("new-task-time");

        $(window).unbind("resize.tutorial");
    };

    p.run_tutorial = function(){
        p.save_tutorial_status(function(){
            p.current_step = -1;
            p.next_step();
        });

        $(window).unbind("resize.tutorial").on("resize.tutorial", function(){
            if(p.current_step == -1) return;

            var s = p.tutorial_steps[p.current_step];

            if(resize_timeout) clearTimeout(resize_timeout);

            if(s.element){
                setTimeout(function(){
                    p.position_dialog($(s.element), s.pos, s.disabled);
                }, 500);
            }
        });
     };

    p.save_tutorial_status = function(callback){
        send_data(p.save_url, {step: p.current_step}, p.g.csrf_token, function(response){
            if(response.status != 'ok'){
                console.error("save_tutorial_status: " + response.message);
            }
            else{
                if(callback) callback();
            }
        });
    };

    p.highlight_element = function(element, disabled){
        var i;

        if(!element){
            // shadow the whole screen
            p.items.shadow.show();
        }
        else{
            function move_to(win, el, top, left, width, height){
                // don't go over the edges
                if(top < 0){
                    height += top; // subtract from height what will be added to top
                    top = 0;
                }

                if(left < 0){
                    width += left;
                    left = 0;
                }

                if(left + width > win.width){
                    width = win.width - left;
                }

                if(top + height > win.height){
                    height = win.height - top;
                }

                // now position
                el.offset({left: left, top: top});
                el.width(width);
                el.height(height);
            }

            var pos = element.offset();
            pos.left -= p.HL_MARGIN;
            pos.top -= p.HL_MARGIN;
            pos.right = pos.left + element.outerWidth() + 2*p.HL_MARGIN;
            pos.bottom = pos.top + element.outerHeight() + 2*p.HL_MARGIN;

            var size = p.get_size(element, true);
            size.width += 2*p.HL_MARGIN;
            size.height += 2*p.HL_MARGIN;

            var div = $("<div>", {"class": "tutorial-shadow"});

            for(i = 0; i < 4; i++){
                p.shadows[i] = div.clone().appendTo("body");
            }

            var win = p.get_size($(window), false);

            // position the shadows:
            // top div
            move_to(win, p.shadows[0],
                0,
                pos.left,
                size.width,
                pos.top);

            // left div
            move_to(win, p.shadows[1],
                0,
                0,
                pos.left,
                win.height);

            // right
            move_to(win, p.shadows[2],
                0,
                pos.left + size.width,
                win.width - pos.left - size.width,
                win.height);

            // bottom
            move_to(win, p.shadows[3],
                pos.top + size.height,
                pos.left,
                size.width,
                win.height - pos.top - size.height);

            if(disabled){
                // if the element should be disabled, put a div over it
                p.items.disable_div.appendTo($("body"));
                p.items.disable_div.offset({top: pos.top + p.HL_MARGIN, left: pos.left + p.HL_MARGIN});
                p.items.disable_div.outerWidth(size.width - 2*p.HL_MARGIN);
                p.items.disable_div.outerHeight(size.height - 2*p.HL_MARGIN);
            }

        }
    };

    p.remove_highlight = function(){
        // hide the fullscreen shadow
        p.items.shadow.hide();

        // the div that disables buttons etc.
        p.items.disable_div.remove();

        // the highlight shadows
        // no shadows have been initialized yet, don't do anything
        if(!p.shadows[0]) return;

        for(var i = 0; i < 4; i++){
            p.shadows[i].hide().remove();
            p.shadows[i] = null;
        }
    };

    //
    // the data
    //
    p.tutorial_steps = [
    {
        title: gettext("Hello!"),
        text: gettext("Thank you for choosing Sellout! This guide will show you the basic features and will also help you complete the first setup."),
        element: null,
        pos: null,
        disabled: null,
        prev_btn: null,
        next_btn: gettext("Begin!"),
        pre_callback: null,
        post_callback: null
    },
    {
        title: gettext("Your companies"),
        text: gettext("Tole nucas. nared novo ali pocakaj, da te en majstr povabi."),
        element: "#tutorial_companies_list", // the element is not a $ object because it may not be created yet
        pos: 'below',
        disabled: true,
        prev_btn: gettext("Back"),
        next_btn: gettext("Next"),
        pre_callback: null,
        post_callback: null
    },
    {
        title: gettext("Your notifications"),
        text: gettext("Kle te povabjo in ti zaratschunajo. Zdej pa nared firmo ali potschakej na invajt."),
        element: "#tutorial_notifications",
        pos: 'below',
        disabled: true,
        prev_btn: null,
        next_btn: null,
        pre_callback: null,
        post_callback: null
    },
    {
        title: gettext("Add, Search, Sort"),
        text: gettext("Use these buttons to organise your tasks."),
        element: "#task_tools",
        pos: 'above',
        disabled: true,
        prev_btn: null,
        next_btn: gettext("Next tip"),
        pre_callback: null,
        post_callback: null
    },
    {
        title: gettext("New Task"),
        text: gettext("Name your task and save it. You can add other parameters too if you like. Click the green tick when you are done."),
        element: "#add_project",
        pos: 'above',
        disabled: false,
        prev_btn: gettext("Back"),
        next_btn: null,
        pre_callback: function(){
            // remove the shadow on button click
            $("#add_project").on("click.tutorial", function(){
                p.remove_highlight();
                p.items.dialog.hide();
            });

            // next step when task is saved
            $(document).on("task-initialized", function(){
                p.next_step();
            });
        },
        post_callback: function(){
            // unbind stuff from this step
            $("#add_project").unbind("click.tutorial");
            $(document).unbind("task-initialized");
        }
    },
    {
        title: gettext("Add Time"),
        text: gettext("When you already have a task, you keep adding times to it as long as you work on it. <br/><br/>"+
            "Click the plus icon to add."),
        element: "#tasks_timetable_container img.add-time",
        pos: 'left',
        disabled: false,
        prev_btn: null,
        next_btn: null,
        pre_callback: function(){
            $(document).on("new-task-time", function(){
                p.next_step();
            });
        },
        post_callback: function(){
            $(document).unbind("new-task-time");
        }
    },
    {
        title: gettext("Shortcuts"),
        text: gettext("Try using mousewheel on time and date boxes. You also don't have to type separators "+
                "between numbers in dates and times.<br/><br/>"+
                "Click the green tick when you're done."),
        element: "#tasks_timetable_container tbody tr.time-container",
        pos: 'above',
        disabled: false,
        prev_btn: null,
        next_btn: null,
        pre_callback: function(){
            $(document).on("time-saved", function(){
                p.next_step();
            });
        },
        post_callback: function(){
            $(document).unbind("time-saved");
        }
    },
    {
        title: gettext("StartStop feature"),
        text: gettext("You have entered a time entry by entering times and dates by hand. But if you want "+
                "to make your life easier, you can click the Start button and select a task you'll be working on. " +
                "When you click Stop, start and end times will be added automatically."),
        element: "#start_stop_button",
        pos: 'right',
        disabled: true,
        prev_btn: null,
        next_btn: gettext("Next tip"),
        pre_callback: null,
        post_callback: null
    },
    {
        title: gettext("Groups"),
        text: gettext("All your projects and tasks are stored in a group. You can edit its name, make new ones and invite "+
            "others to a group. This lets you assign tasks to your team and and offers you an insight of their work."),
        element: "#groups_bar",
        pos: 'below',
        disabled: true,
        prev_btn: gettext("Back"),
        next_btn: gettext("Next tip"),
        pre_callback: null,
        post_callback: null
    },
    {
        title: gettext("User Account"),
        text: gettext("Here you will find your account details, all subscriptions, group management and other settings. " +
            "Support center is also here."),
        element:"#user_menu_container",
        pos: 'below',
        disabled: true,
        prev_btn: gettext("Back"),
        next_btn: gettext("Next tip"),
        pre_callback: null,
        post_callback: null
    },
    {
        title: gettext("That's it!"),
        text: gettext("We are at the end of the tour. <br/><br/>"+
            "Hopefully you get the picture by now. Timebits offers even more extra features you could find useful during your workday.<br/><br/>"+
            "Make sure you check out the calendar, statistics, export options, the shared notes feature, etc.<br/><br/>"+
            " We hope you enjoy Timebits!"),
        element: null,
        pos: null,
        disabled: null,
        prev_btn: gettext("Back"),
        next_btn: gettext("Close"),
        pre_callback: null,
        post_callback: function(){
            p.help_slide();
        }
    }
    ];

    //
    // init
    //
    p.items.start_button.unbind().click(p.run_tutorial);

    // run the tutorial from the appropriate step, if needed
    if(p.current_step != -1){
        p.next_step();
    }
};