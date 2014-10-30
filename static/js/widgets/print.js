function join(text, newline){
    // joins text with separators and leaves out separators if there's no text
    // text/separators is an array of strings
    var r = "";
    var i, l = text.length;
    var t;

    if(text.length % 2 != 1){
        console.error("Length of text must be an odd number");
        return "!Error!";
    }

    text.push(""); // to simplify for loop

    for(i = 0; i < l; i += 2){
        if(typeof text[i] != 'string') continue;

        t = text[i].trim();
        if(t.length > 0){
            r += escape(t) + text[i+1];
        }
    }

    if(newline && r.trim()) r += "<br />";

    return r;
}

function individual_address(contact){
    // returns 'formatted' individual address:
    return join([contact.street_address, ", ", contact.postcode, ", ", contact.city], true) +
        join([contact.state, ", ", contact.country_name], false);
}

function company_address(contact){
    // see individual_address
    var vat;

    if(contact.vat) vat = gettext("VAT") + ": " + contact.vat;
    else vat = '';

    return join([contact.street_address || contact.street, ", ", contact.postcode, " ", contact.city], true) +
        join([contact.state, ", ", contact.country_name], true) +
        join([vat, "<br/>", contact.website], true);
}

function format_receipt(g, bill, type){
    return format_receipt_t(
        g.items,
        g.data.company,
        g.config,
        g.objects.terminal.register,
        bill, type);
}

function format_receipt_t(
        items, // jquery objects: small/large_receipt_template, company_monochrome/color_logo
        company, // company_to_dict
        config, // must include: currency, separator, decimal_places, date_format, time_format
        register, // register_to_dict
        bill, // json
        type){ // string
    var receipt;

    if(type == 'small') receipt = items.small_receipt_template;
    else receipt = items.large_receipt_template;

    receipt = receipt.clone().removeAttr("id");

    // company details:
    $(".company .name", receipt).text(company.name);

    var company_details = $(".company .details", receipt);
    company_details.html(company_address(company));

    if(type != 'small' && company.phone){
        // add special info about company: phone, website
        company_details.append(gettext("Phone") + ": " + company.phone);
    }

    // the same for client company (if selected)
    if(bill.contact){
        if(bill.contact.type == 'Individual'){
            $(".client .name", receipt).html(join([bill.contact.first_name, " ", bill.contact.last_name], false));
            $(".client .details", receipt).html(individual_address(bill.contact));
        }
        else{
            $(".client .name", receipt).text(bill.contact.company_name);
            $(".client .details", receipt).html(company_address(bill.contact));
        }
    }

    // logo
    if(type == 'small'){
        if(register.print_logo && items.company_monochrome_logo){
            // if company's logo exists, append
            $(".receipt-logo", receipt).append(items.company_monochrome_logo);
        }
    }
    else{
        if(items.company_color_logo){
            // if company's logo exists, append
            $(".receipt-logo", receipt).append(items.company_color_logo);
        }
    }

    // location and register location (if selected in register settings)
    if(register.print_location && register.location){
        $(".register-location", receipt).text(register.location);
    }

    // serial number
    $(".bill-serial-content", receipt).text(bill.serial);

    // collect tax rates
    var i, t, item;
    var c = 'A';
    var tax_rates = {/* rate:{letter, tax_sum, gross_sum} */};

    // bill items:
    var items_list = $(".items-body", receipt);
    var item_template = $(".receipt-row", receipt);
    var io;

    for(i = 0; i < bill.items.length; i++){
        // get item data
        item = bill.items[i];

        // handle taxes
        t = item.tax_percent;

        if(!(t in tax_rates)){
            tax_rates[t] = {
                letter: c,
                tax_sum: get_number(item.tax_absolute, config.separator),
                net_sum: get_number(item.total_without_tax, config.separator),
                gross_sum: get_number(item.total, config.separator)
            };

            // next character for next tax rate
            c = String.fromCharCode(c.charCodeAt(0)+1);
        }
        else{
            tax_rates[t].tax_sum = tax_rates[t].tax_sum.plus(get_number(item.tax_absolute, config.separator));
            tax_rates[t].net_sum = tax_rates[t].net_sum.plus(get_number(item.total_without_tax, config.separator));
            tax_rates[t].gross_sum = tax_rates[t].gross_sum.plus(get_number(item.total, config.separator));
        }

        // clone the two rows
        io = item_template.clone().show();

        // name
        $(".item-name", io).text(item.name);
        // item notes (if any)
        $(".item-notes", io).text(item.bill_notes);
        // quantity and unit type
        if(item.unit_type == 'Piece') $(".item-unit", io).html('&nbsp;');
        else $(".item-unit", io).text(item.unit_type);
        // quantity
        $(".item-quantity", io).text(item.quantity);
        // amount
        $(".item-amount", io).text(item.total);
        // tax
        $(".item-tax", io).text(tax_rates[t].letter);
        // price
        $(".item-price", io).text(item.base_price);
        // discount
        $(".item-discount", io).text(item.discount_absolute);

        // append to items_list
        items_list.append(io);
        items_list.append(io);
    }

    // tax rates
    var tax_table = $(".tax-rates .tax-body", receipt);
    var tax_template = $(".tax-row.header", receipt).clone().removeClass("header");
    var tax_row;

    // sums for items
    var net_sum = Big(0);
    var tax_sum = Big(0);
    var gross_sum = Big(0);

    $.each(tax_rates, function(rate, data){
        tax_row = tax_template.clone();

        net_sum = net_sum.plus(data.net_sum);
        tax_sum = tax_sum.plus(data.tax_sum);
        gross_sum = gross_sum.plus(data.gross_sum);

        $(".tax-id", tax_row).text(data.letter);
        $(".tax-percent", tax_row).text(rate + " %");
        $(".tax-net", tax_row).text(display_number(data.net_sum, config.separator, config.decimal_places));
        $(".tax-absolute", tax_row).text(display_number(data.tax_sum, config.separator, config.decimal_places));
        $(".tax-gross", tax_row).text(display_number(data.gross_sum, config.separator, config.decimal_places));

        tax_table.append(tax_row);
    });

    // set
    tax_row = $(".tax-row.footer", receipt);
    $(".tax-net", tax_row).text(display_number(net_sum, config.separator, config.decimal_places));
    $(".tax-absolute", tax_row).text(display_number(tax_sum, config.separator, config.decimal_places));
    $(".tax-gross", tax_row).text(display_number(gross_sum, config.separator, config.decimal_places));

    // currency
    $(".receipt-currency", receipt).text(config.currency);
    // the grand total
    $(".receipt-total", receipt).text(bill.total);

    // cashier name
    console.log(bill)
    $(".receipt-cashier-name", receipt).text(bill.user);
    $(".receipt-datetime", receipt).text(
        today(config.date_format) + " " + now(config.time_format)
    );

    // the calling function will handle the printing
    return receipt;
}