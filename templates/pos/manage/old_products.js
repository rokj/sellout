

// search box
var last_value;
var update_timeout;
var last_offset = 0;
var advanced_shown = false;

var check_interval_duration = 500;
var update_timeout_duration = 1500;

$(document).ready(function(){
    // functions:
    function update_products(){
        // update products when search criteria has changed (gets called on timeout or on click)
        // assemble a JSON object with all search criteria and pass it to the view
        var search_criteria = {
            general_filter:$("#general_filter").val()
        };

        if(advanced_shown){
            // add criteria from the advanced div
            $(".filter").each(function(){
                if($(this).val()){
                    search_criteria[$(this).attr("id")] = $(this).val();
                }
            });

            // add the category id (stored in .data())
            var cat_filter_id = "category_filter";
            var category = $("#" + cat_filter_id);
            var cat_val = category.val().trim();

            if(cat_val != ""){
                if(cat_val in categories_by_breadcrumbs){
                    search_criteria[cat_filter_id] = categories_by_breadcrumbs[cat_val];
                }
            }
        }

        // send to the view
        send_data("{% url 'pos:search_products' company.url_name %}",
            search_criteria, "{{ csrf_token }}", function(recv_data){
                show_products(recv_data);
        });
        return false;
    }

    function show_products(data){
        // show products that search returned
        // clear products div
        var products_div = $("#products_list");
        products_div.empty();

        if(data.length == 0){
            products_div.append("{% trans 'No products found' %}");
        }

        var i;
        var max_height = 0;
        for(i = 0; i < data.length; i++){
            parse_product(data[i]);

            // make a div for each product
            var parent_div = $("<div>", {"class":"product-details"});
            products_div.append(parent_div);

            // save product to .data()
            parent_div.data(data[i]);
            render_product(parent_div);

            // get product container's height
            max_height = Math.max(parent_div.height(), max_height);
        }

        // in the end, make all products equally high
        $("div.product-details").height(max_height);
    }

    function render_product(div_obj/*parent*/){
        // shows a product box (search result), not edit dialog
        var tmp_obj, i;

        // update this div
        var product = div_obj.data();

        // empty parent and copy all stuff from #product_details_template to it
        div_obj.empty();
        div_obj.append($("div.title, div.product-details-image, table.details", "#product_details_template").clone());

        // add product data to data()
        div_obj.data(product);

        // name
        var title_row_obj = $(".title", div_obj);
        var name_obj = $(".product-name", div_obj);

        name_obj.append(escape(product.name));

        title_row_obj.css("background-color", "#" + product.color);

        if(is_dark(product.color)) title_row_obj.addClass("dark");
        else title_row_obj.removeClass("dark");

        // price
        tmp_obj = $(".product-price", div_obj);
        tmp_obj.append(product.price);

        // image
        show_image(product, $(".product-image", div_obj));

        // category
        $(".product-category", div_obj).append(escape(product.category));
        // tax
        $(".product-tax", div_obj).append(product.tax + "%");
        // description
        //$(".product-description", div_obj).append(escape(product.description));
        // discount list
        /* not shown at the moment
        tmp_obj = $(".product-discounts", div_obj);
        if(product.discounts.length > 0){
            var li_obj;
            for(i = 0; i < product.discounts.length; i++){
                li_obj = $("<li>", {title:""});
                li_obj.append(product.discounts[i].code + " " +
                    discount_amount(product.discounts[i]));

                // tooltip:
                discount_tooltip(product.discounts[i], li_obj);
                tmp_obj.append(li_obj);
            }
        }
        else{
            tmp_obj.text("/");
        }*/

        // private notes
        //$(".product-private-notes", div_obj).append(escape(product.private_notes));
        // stock
        /*if(product.stock){
            $(".product-stock", div_obj).append(product.stock + " " +
                product.unit_type_display + " {% trans 'left in stock' %}");
        }*/

        // shortcut
        $(".product-shortcut", div_obj).append(escape(product.shortcut));
        // code
        $(".product-code", div_obj).append(escape(product.code));

        var edit_button = $("button.product-edit-button", div_obj);
        var delete_button = $("button.product-delete-button", div_obj);
        var favorite_button = $("button.product-favorite-button", div_obj);

        // if a user has no permission to edit/delete, don't show buttons
        if({{can_edit|lower}}){
            // enable and add functionality to:
            // edit button
            edit_button.prop('disabled', false);
            edit_button.click(function(){
                show_product_edit_dialog(div_obj);
            });
            // delete button
            delete_button.prop('disabled', false);
            delete_button.click(function(){
                delete_product(div_obj);
            });
            // favorite button
            favorite_button.prop('disabled', false);
            favorite_button.click(function(){
                toggle_favorite(favorite_button, product);
            });
        }
        else{
            // just disable
            edit_button.prop('disabled', true);
            delete_button.prop('disabled', true);
            favorite_button.prop('disabled', true);
        }

        style_favorite_button(favorite_button, product.favorite);

        div_obj.show();
    }

    function style_favorite_button(button_obj, favorited){
        if(favorited) button_obj.addClass("active");
        else button_obj.removeClass("active");
    }

    function toggle_favorite(button_obj, product){
        send_data("{% url 'pos:toggle_favorite' company.url_name %}", {product_id:product.id}, "{{ csrf_token }}",
            function(response){
                if(response.status != 'ok'){
                    error_message(
                        "{% trans 'Favorite could not be set' %}",
                        response.message);
                }
                else{
                    // update product and the button
                    product.favorite = response.favorite;
                    style_favorite_button(button_obj, product.favorite);
                }
            });
    }

    function discount_amount(discount){
        if(discount.type == 'Percent')
            return " (" + display_number(discount.amount, "{{ separator }}", {{ decimal_places }}) + "%)";
        else
            return " ({{currency|escapejs}} " + display_number(discount.amount, "{{ separator }}", {{ decimal_places }}) + ")";
    }

    function discount_tooltip(discount, li_obj){
        // tooltip - discount details
        var tooltip = "";

        // tooltip = discount.code + "<br />" // discount code (already in the li)
        tooltip += escape(discount.description) + "<br />"; // description

        // if no dates are set, show 'no date limit', otherwise 'from ... to ...'
        if(!discount.start_date && !discount.end_date){
            tooltip += "{% trans 'No date limits' %}"
        }
        else{
            if(discount.start_date) tooltip += "{% trans 'from' %} " + escape(discount.start_date);
            if(discount.end_date) tooltip += " {% trans 'to' %} " + escape(discount.end_date);
        }

        // TODO: set style for inactive discount
        if(!discount.active) tooltip += "<br/>{% trans 'inactive' %}"; // active

        li_obj.tooltip({content:tooltip});
    }

    function find_discount_by_id(discounts, id){
        for(var i = 0; i < discounts.length; i++){
            if(discounts[i].id == id) return i;
        }

        // discount not found
        return null;
    }

    function add_discount(ul_obj, product, id){ // i - index in product.discounts
        // add a list Item and a delete button to product edit dialog
        // add a discount from all_discounts to product
        var i = find_discount_by_id(product.discounts, id);
        var discount = product.discounts[i];

        var li_obj = $("<li>", {title:""});
        li_obj.data(discount); // store id in data() for later retrieval

        discount_tooltip(discount, li_obj);

        // delete button
        var btn_obj = $("<img>", {"class":"delete-discount hoverable", src: "{% static 'icons/cancel.png' %}"});
        btn_obj.click(function(){
            // delete this list Item
            $(this).parent().remove();
            // delete this id from product.discounts
            product.discounts.splice(i, 1);
            // redraw discounts
            refresh_discounts(product);
        });

        li_obj.append(discount.code + " " + discount_amount(discount));
        li_obj.append(btn_obj);
        ul_obj.append(li_obj);
    }

    function refresh_discounts(product){
        // clear everything discount-related and redraw
        var ul_obj = $("#edit_discounts", "#edit_dialog");
        ul_obj.empty();

        // add discounts currently in product
        var i;
        for(i = 0; i < product.discounts.length; i++){
            add_discount(ul_obj, product, product.discounts[i].id);
        }

        // add another Item, this time with all available discounts
        // in a listbox and an 'add' button
        var li_obj = $("<li>");
        var sel_obj = $("<select>", {id:"edit_discount_list"});
        li_obj.append(sel_obj);
        li_obj.data({id:false}); // don't store or send this Item
        ul_obj.append(li_obj);

        // add discounts NOT in product to add listbox
        var added = 0;

        for(i = 0; i < all_discounts.length; i++){
            // ignore discounts that are already in product
            if(find_discount_by_id(product.discounts, all_discounts[i].id) != null){
                continue;
            }

            var opt_obj = $("<option>")
                .attr("value", all_discounts[i].id)
                .append(all_discounts[i].code + " " + discount_amount(all_discounts[i]));

            sel_obj.append(opt_obj);
            added++;
        }
        // only add the listbox if there's anything to add
        if(added > 0){
            // unselect the first Item in listbox to avoid confusion
            sel_obj.prop("selectedIndex", -1);

            sel_obj.unbind().change(function(){ // no add buttons
                var d_i = $(":selected", sel_obj).val(); // currently selected discount's list index

                // add data to product
                product.discounts.push(all_discounts[find_discount_by_id(all_discounts, d_i)]);
                refresh_discounts(product);
            });
        }
        else{
            // remove the last, 'add' entry
            li_obj.remove();
        }

        // make the list sortable, but exclude the last Item
        if(added > 0) ul_obj.sortable({items:"li:not(:last)", stop:get_total_price}); // also update price when sorting stops
        else ul_obj.sortable({items:"li"});

        // update total price
        get_total_price();
    }

    function upload_image_status(status, save_obj, del_obj, upl_obj, img_obj){
        return;
        // no showing and hiding at the moment
        /*var show, hide;

        upl_obj = upl_obj.parent();

        switch(status){
           case 'image':
               // product has image and it is not being edited
               show = [save_obj, del_obj, img_obj];
               hide = [upl_obj];
               break;
           case 'no_image':
               // product has no image and it is not being edited
               show = [save_obj, img_obj];
               hide = [del_obj];
               break;
           case 'uploading':
               // image is uploading
               show = [img_obj];
               hide = [save_obj, del_obj, upl_obj];
               break;
        }

        var i;
        for(i = 0; i < show.length; i++) show[i].show();
        for(i = 0; i < hide.length; i++) hide[i].hide();*/
    }

    function show_image(product, obj){
        if(!product.image){
            // show 'placeholder' image
            obj.css("background-image", "url('{% static 'images/product_placeholder.png' %}')");
            obj.attr("alt", "{% trans 'No image' %}");
        }
        else{
            // show the real image
            obj.css("background-image", "url('" + product.image + "')");
            obj.attr("alt", escape(product.name));
        }
    }

    function show_product_edit_dialog(parent){
        var i, sel_obj;

        var product = parent.data();

        var edit_obj = $("#edit_dialog");

    // save button (unbind previously bound objects)
    var save_btn_obj = $("#edit_product_save", edit_obj);
    save_btn_obj.unbind().click(function(){
        save_product(parent);
    });

    // cancel button
    $("#edit_product_cancel", edit_obj).unbind().click(function(){
        // reload the product
        get_product(parent);
        // destroy the dialog (content will be deleted when it opens again)
        $("#edit_dialog").hide();
        $("#dialog_shadow").fadeOut("fast");
    });

        // init all fields
        $("#edit_product_name", edit_obj).val(product.name).focus();

        // always show price excluding tax first
        sel_obj = $("#edit_product_price_without_tax", edit_obj);
        sel_obj.val(product.price);

        // purchase price
        sel_obj = $("#edit_product_purchase_price");
        sel_obj.val(product.purchase_price);

        // ... per unit (listbox with unit types)
        sel_obj = $("#edit_product_unit_type", edit_obj).empty();

        for(i=0; i<units.length;i++){
            opt_obj = $("<option>")
                .attr("value", units[i].value)
                .text(units[i].name);

            if(units[i].value == product.unit_type){
                opt_obj.attr("selected", "selected");
            }
            sel_obj.append(opt_obj);
        }
        // when changed, update units
        sel_obj.change(update_unit_types);

        // update with default
        update_unit_types();

        // listbox with taxes
        sel_obj = $("#edit_product_tax", edit_obj).empty();

        create_tax_select(sel_obj, product, false);

        // autocomplete with categories
        sel_obj = $("#edit_product_category", edit_obj).empty();
        sel_obj.autocomplete({source: categories_list });
        if(!isNaN(product.category_id)) sel_obj.val(categories_by_id[product.category_id]);
        else sel_obj.val("");

        // product image
        var del_obj = $("#edit_product_delete_image", edit_obj);
        var upl_obj = $("#edit_product_image_upload", edit_obj);
        var img_obj = $("#edit_product_image", edit_obj);

        // reset the upload control (.val() doesn't work for security reasons)
        //$("#edit_product_image_input_form").get(0).reset();

        // show product image, if it exists
        show_image(product, img_obj);

        product.change_image = false;

        // upload <input>: preview image on upload and store base64 data for sending to server
        upl_obj.unbind().change(function(){

        });

        // set dialog title: if there's no name, it's for adding new product
        sel_obj = $("#edit_dialog_title");
        if(product.name)
            sel_obj.text("{% trans 'Edit product' %}");
        else
            sel_obj.text("{% trans 'Add product' %}");


        del_obj.unbind().click(function(){
            // show/hide controls
            upload_image_status('no_image', save_btn_obj, del_obj, upl_obj, img_obj);

            // image was changed
            product.change_image = true;
            // nothing to upload
            product.image_data = null;
            // and also nothing to show
            product.image = null;
            // delete image source and name
            show_image(product, img_obj);
        });

        if(product.image){
            // product already has an image: show it
            show_image(product, img_obj);
            upload_image_status('image', save_btn_obj, del_obj, upl_obj, img_obj);
        }
        else{
            upload_image_status('no_image', save_btn_obj, del_obj, upl_obj, img_obj);
        }

        $("#edit_product_description", edit_obj).val(product.description);
        $("#edit_product_price", edit_obj).val(product.price);

        // discounts
        // add to list
        var ul_obj = $("#edit_discounts", edit_obj);
        ul_obj.empty();

        // for the first time
        refresh_discounts(product);

        $("#edit_product_private_notes", edit_obj).val(product.private_notes);
        $("#edit_product_stock", edit_obj).val(product.stock);
        $("#edit_product_shortcut", edit_obj).val(product.shortcut);
        $("#edit_product_code", edit_obj).val(product.code);

        var base_price_obj = $("#edit_product_price_without_tax").val(product.price);
        var tax_price_obj = $("#edit_product_price_with_tax").val(""); // will be updated with base_price_obj.change()

        // update total price when tax, price or discounts change
        $("#edit_product_tax, " +
            "#edit_product_price_with_tax, " +
            "#edit_product_price_without_tax, " +
            "#edit_product_purchase_price", edit_obj).unbind().change(get_total_price);

        // update price with or without tax
        base_price_obj.change(function(){
            var base_price = get_number($(this).val(), "{{ separator }}");
            // update price with tax
            var tax = get_number(get_tax($("#edit_product_tax").val()).amount, "{{ separator }}");

            if(!base_price) return;
            if(!tax) return;

            tax_price_obj.val(display_number(base_price.times(Big(1).plus(tax.div(Big(100)))), "{{ separator }}", {{ decimal_places }}));

            get_total_price();
        }).change();

        tax_price_obj.change(function(){
            var tax_price = get_number($(this).val(), "{{ separator }}");
            // update price with tax
            var tax = get_number(get_tax($("#edit_product_tax").val()).amount, "{{ separator }}");

            if(!tax_price) return;
            if(!tax) return;

            base_price_obj.val(display_number(tax_price.div(Big(1).plus(tax.div(Big(100)))), "{{ separator }}", {{ decimal_places }}));

            get_total_price();
        });

        get_total_price();

        // initial 'change'
        base_price_obj.change();

        // show the edit 'dialog'
        open_edit_dialog();

        // custom 'widgets'
        $("#edit_product_image_upload").customFileInput("{% trans 'Choose...' %}");



        // focus on product price, instead of 'remove image' button
        base_price_obj.focus();
    }

    function parse_product(product){
        // convert all text numbers in product to Big() numbers
        // price, purchase_price, stock, tax, discounts[amount]
        product.price = get_number(product.price, "{{ separator }}");
        product.purchase_price = get_number(product.purchase_price, "{{ separator }}");
        product.stock = get_number(product.stock, "{{ separator }}");
        product.tax = get_number(product.tax, "{{ separator }}");

        for(var i = 0; i < product.discounts.length; i++){
            product.discounts[i].amount = get_number(product.discounts[i].amount, "{{ separator }}");
        }

        return product;
    }

    function get_product(parent){
        // get product's data from the server and put
        // it where it was before (product.parent)
        var url = "{% url 'pos:get_product' company.url_name %}" + '?' + $.param({product_id: parent.data().id});

        get_data(url, function(data){
            if(data.status == 'error'){
                error_message(
                        "{% trans 'Could not retrieve product' %}",
                        data.message);
            }
            else{
                parent.data(parse_product(data));
                render_product(parent);
            }
        });
    }

    function get_product_discounts(ul_obj){
        // discounts: get all <li> items and put them into an array
        var discounts = [];

        ul_obj.children().each(function(){
            var id = $(this).data().id;
            if(id){
                discounts.push($(this).data()); // the last entry is the listbox and button, don't add that
            }
        });

        return discounts;
    }

    function get_total_price(){
        // tax
        var t = get_number(get_tax($("#edit_product_tax").val()).amount, "{{ separator }}");
        if(!t) return; // don't change anything if something is wrong (or not yet entered)

        // price: always get price without tax
        var price = get_number($("#edit_product_price_without_tax").val(), "{{ separator }}");
        if(!price) return;

        // gather all discounts
        var discounts = get_product_discounts($("ul#edit_discounts"));

        // total_price(tax_first, base_price, tax, discounts, quantity, decimal_places){
        var result = total_price({{tax_first|lower}}, price, t, discounts, Big(1), {{decimal_places}});

        $("#total_price").text(display_number(result.total, "{{separator}}", {{ decimal_places }}));

        // price without tax
        $("#price_without_tax").text(display_number(result.total_tax_exc, "{{separator}}", {{ decimal_places }}));

        // calculate profit and if it's lower than zero, use a different style
        // get the purchase price, if entered
        var purchase_price = get_number($("input#edit_product_purchase_price").val(), "{{separator}}");
        var profit_obj = $("#profit");
        if(purchase_price){
            var profit = result.total_tax_exc.minus(purchase_price);
            profit_obj.text(display_number(profit, "{{separator}}", {{ decimal_places }}));

            if(profit.cmp(Big(0)) < 0){ // use alternate style
                profit_obj.addClass("negative-profit");
            }
            else{
                profit_obj.removeClass("negative-profit");
            }
        }
        else{
            profit_obj.text("");
        }
    }

    function save_product(parent){
        // get product's data from the dialog and send
        // id
        // price - numeric value
        // unit type
        // discounts - list of discount ids
        // image_changed
        // image
        // category - id
        // code
        // shortcut
        // description
        // private notes
        // tax
        // stock
        var product = parent.data();

        var dlg_obj = $("#edit_dialog");

        var data = {};
        data['id'] = product.id;
        data['name'] = $("#edit_product_name", dlg_obj).val();
        data['unit_type'] = $("#edit_product_unit_type", dlg_obj).val();
        // image: if changed, encode uploaded image to base64
        data['change_image'] = product.change_image;
        if(product.change_image) data['image'] = product.image_data;

        data['category_id'] = categories_by_breadcrumbs[$("#edit_product_category", dlg_obj).val()];
        last_chosen_category = data['category_id']; // remember the last used
        data['tax_id'] = $("#edit_product_tax", dlg_obj).val();
        data['description'] = $("#edit_product_description", dlg_obj).val();
        // discounts: strip off everything but ids
        var discounts = get_product_discounts($("ul#edit_discounts", dlg_obj));
        for(var i = 0; i < discounts.length; i++){
            discounts[i] = discounts[i].id;
        }
        data['discount_ids'] = discounts;
        data['private_notes'] = $("#edit_product_private_notes", dlg_obj).val();
        data['stock'] = $("#edit_product_stock", dlg_obj).val();
        data['shortcut'] = $("#edit_product_shortcut", dlg_obj).val();
        data['code'] = $("#edit_product_code", dlg_obj).val();
        // price: always use base price (without tax)
        data['price'] = $("#edit_product_price_without_tax", dlg_obj).val();

        if(!data['price']){
            error_message(
                "{% trans 'Invalid data' %}",
                "{% trans 'Please check product price' %}"
            );
        }

        // purchase price
        data['purchase_price'] = $("#edit_product_purchase_price", dlg_obj).val();

        if(data['id'] == "-1"){
            // it's a new product
            // refresh search criteria
            send_data("{{ add_url|escapejs }}", data, "{{csrf_token}}",
                function(response){
                    if(response.status != 'ok')
                        error_message("{% trans 'Error saving product' %}", response.message);
                    else{
                        // save the new product data
                        parent.data(response.data);
                        // re-do the current search and close the dialog
                        update_products();
                        close_edit_dialog();
                    }
                }
            );
        }
        else{
            // the product's been edited
            // send data to server and update the div with the retrieved 'cleaned' data
            send_data("{% url 'pos:edit_product' company.url_name %}", data, "{{csrf_token}}",
                function(response){
                    if(response.status != 'ok')
                        error_message("{% trans 'Error saving product' %}", response.message);
                    else{
                        get_product(parent);
                        close_edit_dialog();
                    }
                }
            );
        }
    }

    function open_edit_dialog(){
        var shadow = $("#dialog_shadow");

        shadow.fadeIn("fast", function(){
            $("#edit_dialog").show();
        });
        shadow.unbind().click(close_edit_dialog);
    }

    function close_edit_dialog(){
        $("#edit_dialog").hide();
        $("#dialog_shadow").fadeOut("fast");
    }

    function delete_product(parent){
        var product = parent.data();
        var data = {};
        data['id'] = product.id;
        // confirm deletion
        confirmation_dialog(
            "{% trans 'Are you sure?' context 'confirmation dialog title' %}",
            "{% trans 'Delete product ' %} '" + product.name + "'?",
                function(){
                    send_data("{% url 'pos:delete_product' company.url_name %}", data, "{{ csrf_token }}",
                        function(data){
                            if(data.status != 'ok') error_message("{% trans 'Error deleting product' %}", data.message);
                            else{
                            // remove the product's div and delete the variable
                            parent.remove();
                        }
                    });
                },
                function(){}
        );
    }

    function update_unit_types(){
        // when the unit types edit changes, update all static labels with the changed units
        var ut = $("#edit_product_unit_type").val();

        var ut_display = ut;

        // try to find a better name (the actual display unit instead of m^2)
        for(var i = 0; i < units.length; i++){
            if(units[i].value == ut){
                ut_display = units[i].name;
                break;
            }
        }

        $("span.unit-readonly").each(function(){
            $(this).text(ut_display);
        });
    }

    function create_tax_select(sel_obj, product, select_none){
        var opt_obj;

        for(i=0; i < tax_rates.length; i++){
            opt_obj = $("<option>")
                .attr("value", tax_rates[i].id)
                .text(escape(tax_rates[i].name) + " (" + tax_rates[i].amount + "%)");

            if(product && product.tax){ // use product's tax if editing
                if(tax_rates[i].id == product.tax_id){
                    // select the chosen tax
                    opt_obj.attr("selected", "selected");
                }
            }
            else{ // set default tax if adding new products
                if(tax_rates[i].id == {{default_tax_id}}){
                    // select the chosen tax
                    opt_obj.attr("selected", "selected");
                }
            }
            sel_obj.append(opt_obj);
        }

        if(select_none){
            opt_obj = $("<option>")
                    .attr("value", null)
                    .text("---");

            sel_obj.append(opt_obj);

            if(!product) opt_obj.attr("selected", "selected");
        }

    }

    ////////////////////
    // data retrieval
    ////////////////////
    // categories list
    var i;
    categories_list = [];
    categories_by_breadcrumbs = {};
    categories_by_id = {};

    for(i = 0; i < category_data.length; i++){
        categories_list.push(category_data[i].breadcrumbs);
        categories_by_breadcrumbs[category_data[i].breadcrumbs] = category_data[i].id;
        categories_by_id[category_data[i].id] = category_data[i].breadcrumbs;
    }

    // unit types
    units = [];
    for(i=0; i < units_data.length; i++){
        units.push({"value":units_data[i][0], "name":units_data[i][1]});
    }

    // discounts
    // convert all amounts to Big() numbers
    for(i = 0; i < all_discounts.length; i++){
        all_discounts[i].amount = get_number(all_discounts[i].amount, "{{ separator }}");
    }

    // tax rates
    function get_tax(id){
        // returns the tax object with the given id
        for(var i = 0; i < tax_rates.length; i++){
            if(tax_rates[i].id == id) return tax_rates[i];
        }
        return null;
    }

    ////////////////////
    // searching
    ////////////////////
    var gf_obj = $("#general_filter");
    gf_obj.keypress(function(e){
        if(e.which == 13){ // enter pressed
            update_products();
        }
    });

    // hide the template
    $("div#product_details_template").hide();

    // general products search box timers
    setInterval(function(){ // check for change
        var new_value = gf_obj.val();
        if(last_value != new_value){
            if(new_value.length < 2) return;
            last_value = new_value; // changed, update products
            clearTimeout(update_timeout);
            update_timeout = setTimeout(update_products, update_timeout_duration);
        }
    }, check_interval_duration);

    // advanced search div
    var adv_div_obj = $("#advanced_search");
    adv_div_obj.hide();

    var adv_chk_obj = $("#advanced_search_toggle");

    function toggle_search(show){
        if(show){
           adv_div_obj.show();
           $(".basic", adv_chk_obj).hide();
           $(".advanced", adv_chk_obj).show();
        }
        else{
           adv_div_obj.hide();
           $(".basic", adv_chk_obj).show();
           $(".advanced", adv_chk_obj).hide();
        }

        advanced_shown = show;
    }

    adv_chk_obj.click(function(){
        toggle_search(!advanced_shown);
        return false;
    });

    // categories autocomplete list
    var cat_inp_obj = $("#category_filter");
    cat_inp_obj.autocomplete({
        source: categories_list,
        minLength: 0,
        delay: check_interval_duration
    });

    cat_inp_obj.focus(function(){
        cat_inp_obj.autocomplete("search", "");
    });

    // tax rates select
    create_tax_select($("#tax_filter"), null, true);

    // update products on button click
    $("#update_results").click(function(){
        update_products();
    });

    ///////////////////////////
    // creating new products
    ///////////////////////////
    if({{can_edit|lower}}){ {% comment %} |lower because: python: True, javascript: true {% endcomment %}
        $("#add_product").click(function(){
            // show the edit dialog with nothing but default values

            // empty product
            var product = {
                "id":-1,// new product's id = -1 until the server assigns an id
                "discounts": [] // no discounts so far
            };
            // save it to a dummy div
            var parent = $("#new_product_dummy").empty();
            parent.data(product);

            show_product_edit_dialog(parent);
        });
    }
    else{
        $("#add_product").prop("disabled", true);
    }

    gf_obj.focus();

    // matching urls:
    // supporting two searches:
    //   - products from category: #category:'category-id'
    //   - basic search: #query:'search-query'
    var url_separator = ':';

    function clear_search(){
        $(".filter", "#advanced_search").val("");
    }


});