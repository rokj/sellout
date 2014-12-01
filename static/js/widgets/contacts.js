Contacts = function(g){
    // a list of contacts (ready to be used for writing bills)
    var p = this;

    p.g = g;

    // data (will be initialized below, under init)
    p.individuals_list = []; // a list for autocomplete {label:. value:}
    p.individuals_by_id = {};

    p.companies_list = [];
    p.companies_by_id = {};

    p.selected = null; // will be used on save
    p.data_changed = false; // if true, the contact will have to be re-saved

    // dialog and its items
    p.dialog = $("#contacts");
    p.individual_form = $(".individual-form", p.dialog);
    p.company_form = $(".company-form", p.dialog);

    p.items = {
        individual: {
            first_name: $(".first-name", p.individual_form),
            last_name: $(".last-name", p.individual_form),
            sex: $(".sex", p.individual_form),
            email: $(".email", p.individual_form),
            street_address: $(".street-address", p.individual_form),
            postcode: $(".postcode", p.individual_form),
            city: $(".city", p.individual_form),
            state: $(".state", p.individual_form),
            country: $(".country", p.individual_form),
            phone: $(".phone", p.individual_form),
            date_of_birth: $(".date-of-birth", p.individual_form)
        },
        company: {
            name: $(".name", p.company_form),
            email: $(".email", p.company_form),
            street_address: $(".street-address", p.company_form),
            postcode: $(".postcode", p.company_form),
            city: $(".city", p.company_form),
            state: $(".state", p.company_form),
            country: $(".country", p.company_form),
            phone: $(".phone", p.company_form),
            vat: $(".vat", p.company_form)
        },
        company_switch: $(".company-switch", p.dialog),
        individual_switch: $(".individual-switch", p.dialog),

        save_button: $(".save", p.dialog),
        cancel_button: $(".cancel", p.dialog),
        clear_button: $(".clear", p.dialog),

        bill_label: $("#bill_contact_label"), // the label for selected contact
        bill_contact: $("#bill_contact_name") // the name of the selected contact (right after label)

    };

    //
    // methods
    //
    p.prepare_contact = function(c){
        var i, t;

        // adds contact to internal dictionaries for later retrieval
        if(c.type == 'Company'){
            // see if the contact exists already
            if(c.id in p.companies_by_id){
                // find the entry in companies_list and remove it,
                // the dictionary entry will be overwritten anyway
                for(i = 0; i < p.companies_list.length; i++){
                    if(p.companies_list[i].value == c.id){ // ACHTUNG, it's value, not ID (autocomplete...)
                        remove_from_array(p.companies_list, i);
                        break;
                    }
                }

            }

            if(c.vat) t = c.vat + ": ";
            else t = "";

            p.companies_list.push({
                label: t + c.company_name,
                value: c.id
            });

            p.companies_by_id[c.id] = c;
        }
        else{
            if(c.id in p.individuals_by_id){
                // find the entry in companies_list and remove it,
                // the dictionary entry will be overwritten anyway
                for(i = 0; i < p.individuals_list.length; i++){
                    if(p.individuals_list[i].value == c.id){
                        remove_from_array(p.individuals_list, i);
                        break;
                    }
                }

            }

            if(c.street_address) t = ", " + c.street_address;
            else t = "";


            p.individuals_list.push({
                label: c.first_name + " " + c.last_name + t,
                value: c.id
            });

            p.individuals_by_id[c.id] = c;
        }
    };

    p.choose_contact = function(){
        // return contact id or null if nothing has been chosen
        custom_dialog(gettext("Select contact"),
            p.dialog, 550);

        p.data_changed = false;

        if(p.g.objects.bill.contact){
            // there is already a contact selected, show it
            p.selected = p.g.objects.bill.contact;

            if(p.selected.type == 'Individual') p.select_individual(p.selected.id);
            else p.select_company(p.selected.id);
        }
        else{
            // no contact is selected yet, clear fields
            p.clear_fields();
        }
    };

    p.remove_contact = function(){
        p.clear_fields();
        p.g.objects.bill.contact = null;

        p.update_labels();
        p.close_action();
    };

    p.toggle_type = function(company){
        if(company){
            // hide the individual form and change buttons' classes
            p.individual_form.hide();
            p.items.individual_switch.removeClass("active");

            p.company_form.show();
            p.items.company_switch.addClass("active");
        }
        else{
            p.individual_form.show();
            p.items.individual_switch.addClass("active");

            p.company_form.hide();
            p.items.company_switch.removeClass("active");
        }
    };

    p.clear_fields = function(){
        var key;
        for(key in p.items.company){
            if(p.items.company.hasOwnProperty(key)){
                p.items.company[key].val("");
            }
        }

        for(key in p.items.individual){
            if(p.items.individual.hasOwnProperty(key)){
                p.items.individual[key].val("");
            }
        }

        // some special fields:
        // countries: choose the company's country
        p.items.company.country.val(p.g.data.company.country);
        p.items.individual.country.val(p.g.data.company.country);
        // sex: undisclosed
        p.items.individual.sex.val("U");
    };

    p.select_company = function(id){
        if(!id){
            p.clear_fields();
            p.selected = null;
        }

        // get the company details from the id and fill all data
        var c = p.companies_by_id[id];

        p.items.company.name.val(c.company_name);
        p.items.company.email.val(c.email);
        p.items.company.street_address.val(c.street_address);
        p.items.company.postcode.val(c.postcode);
        p.items.company.city.val(c.city);
        p.items.company.state.val(c.state);
        p.items.company.country.val(c.country);
        p.items.company.phone.val(c.phone);
        p.items.company.vat.val(c.vat);

        // show the company section (tab) of the dialog
        p.toggle_type(true);

        p.selected = c;
    };

    p.select_individual = function(id){
        if(!id){
            p.clear_fields();
            p.selected = null;
        }

        // get the company details from the id and fill all data
        var c = p.individuals_by_id[id];

        p.items.individual.first_name.val(c.first_name);
        p.items.individual.last_name.val(c.last_name);
        p.items.individual.sex.val(c.sex);
        p.items.individual.street_address.val(c.street_address);
        p.items.individual.postcode.val(c.postcode);
        p.items.individual.city.val(c.city);
        p.items.individual.state.val(c.state);
        p.items.individual.country.val(c.country);
        p.items.individual.email.val(c.email);
        p.items.individual.phone.val(c.phone);
        p.items.individual.date_of_birth.val(c.date_of_birth);

        // select the individual section of the dialog
        p.toggle_type(false);

        p.selected = c;
    };

    p.update_labels = function(){
        if(p.g.objects.bill.contact){
            p.items.bill_label.show();
            p.items.bill_contact.show();

            // fill the contact with names
            var c = p.g.objects.bill.contact;

            if(c.type == 'Individual'){
                p.items.bill_contact.text(
                    join([c.first_name, " ", c.last_name], false) // the function comes from print.js
                );
            }
            else{
                p.items.bill_contact.text(c.company_name);
            }
        }
        else{
            p.items.bill_label.hide();
            p.items.bill_contact.hide();
        }

        // resize the terminal
        p.g.objects.terminal.size_layout();
    };

    p.select_contact = function(){
        if(p.selected && !p.data_changed){
            // an existing contact is selected, use that data
            p.g.objects.bill.contact = p.selected;
            p.close_action();
        }
        else{
            // nothing is selected, create a new contact or edit existing one
            var data, id;

            if(p.selected && p.selected.id) id = p.selected.id; // editing an existing contact
            else id = -1; // creating a new contacts

            // see which type of contact is being created (check button classes)
            if(p.items.individual_switch.hasClass("active")){
                // it's an individual
                data = {
                    id: id,
                    type: 'Individual',
                    first_name: p.items.individual.first_name.val(),
                    last_name: p.items.individual.last_name.val(),
                    sex: p.items.individual.sex.val(),
                    street_address: p.items.individual.street_address.val(),
                    postcode: p.items.individual.postcode.val(),
                    city: p.items.individual.city.val(),
                    state: p.items.individual.state.val(),
                    country: p.items.individual.country.val(),
                    email: p.items.individual.email.val(),
                    phone: p.items.individual.phone.val(),
                    date_of_birth: p.items.individual.date_of_birth.val()
                };
            }
            else{
                // it's a company
                data = {
                    id: id,
                    type: 'Company',
                    company_name: p.items.company.name.val(),
                    street_address: p.items.company.street_address.val(),
                    postcode: p.items.company.postcode.val(),
                    city: p.items.company.city.val(),
                    state: p.items.company.state.val(),
                    country: p.items.company.country.val(),
                    email: p.items.company.email.val(),
                    phone: p.items.company.phone.val(),
                    vat: p.items.company.vat.val()
                };
            }

            send_data(p.g.urls.quick_contacts, data, p.g.csrf_token, function(response){
                    if(response.status != 'ok'){
                        error_message(
                            gettext("Saving contact failed"),
                            response.message
                        );
                    }
                    else{
                        // add a new contact
                        p.prepare_contact(response.data);

                        // the contact is added
                        p.selected = response.data;
                        p.g.objects.bill.contact = response.data;

                        p.close_action();
                    }
                });
        }
    };

    p.close_action = function(){
        p.dialog.close_dialog();
        p.update_labels();
    };

    //
    // init
    //

    // buttons and bindings
    p.toggle_type(true); // default is company

    p.items.individual_switch.click(function(){ p.toggle_type(false); });
    p.items.company_switch.click(function(){ p.toggle_type(true); });

    // prepare data: labels and values
    for(var i = 0; i < p.g.data.contacts.length; i++){
        p.prepare_contact(p.g.data.contacts[i]);
    }

    // initialize autocompletes
    function cs(event, ui){
        event.preventDefault(); // on select event: fill in the company details
        p.select_company(ui.item.value); // value contains company id
    }

    p.items.company.name.autocomplete({
        source: p.companies_list,
        appendTo: p.dialog,
        select: cs,
        focus: cs
    });

    function is(event, ui){
        event.preventDefault(); // on select event: fill in the company details
        p.select_individual(ui.item.value); // value contains company id
    }

    p.items.individual.first_name.autocomplete({
        source: p.individuals_list,
        appendTo: p.dialog,
        select: is,
        focus: is
    });

    // clear if there's anything left from the previous contact
    p.clear_fields();

    // clear, save and cancel buttons
    p.items.clear_button.unbind().click(p.remove_contact);
    p.items.save_button.unbind().click(p.select_contact);
    p.items.cancel_button.unbind().click(p.close_action);

    // most inputs: when changed, re-save the contact entry
    $.each(p.items.individual, function(key, value){
        value.unbind().change(function(){ p.data_changed = true; });
    });
    $.each(p.items.company, function(key, value){
        value.unbind().change(function(){p.data_changed = true; });
    });

    // if there's a contact selected already, update bill
    p.update_labels();
};