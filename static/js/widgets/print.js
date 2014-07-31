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
    // g: terminal globals
    // bill: Bill() objects
    var receipt;

    if(type == 'small') receipt = g.items.small_receipt_template;
    else receipt = g.items.large_receipt_template;

    receipt = receipt.clone().removeAttr("id");

    // company details:
    $(".company .name", receipt).text(g.data.company.name);

    var company_details = $(".company .details", receipt);
    company_details.html(company_address(g.data.company));

    if(type != 'small'){
        // add special info about company: phone, website
        company_details.append(
            join([g.data.company.phone, "<br/>",
            g.data.company.website], false));
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
        if(g.objects.terminal.register.print_logo && g.items.company_monochrome_logo){
            // if company's logo exists, append
            $(".receipt-logo", receipt).append(g.items.company_monochrome_logo);
        }
    }
    else{
        if(g.items.company_color_logo){
            // if company's logo exists, append
            $(".receipt-logo", receipt).append(g.items.company_color_logo);
        }
    }

    // location and register location (if selected in register settings)
    if(g.objects.terminal.register.print_location && g.objects.terminal.register.location){
        $(".register-location", receipt).text(g.objects.terminal.register.location);
    }

    // serial number
    $(".bill-serial-content", receipt).text(bill.data.serial);

    // collect tax rates
    var i, t, item;
    var c = 'A';
    var tax_rates = {/* rate:{letter, tax_sum, gross_sum} */};

    // bill items:
    var items_list = $(".items-body", receipt);
    var item_template_1 = $(".receipt-row.first", receipt);
    var item_template_2 = $(".receipt-row.second", receipt);
    var io1, io2;

    for(i = 0; i < bill.data.items.length; i++){
        // get item data
        item = bill.data.items[i];

        // handle taxes
        t = item.tax_percent;

        if(!(t in tax_rates)){
            tax_rates[t] = {
                letter: c,
                tax_sum: get_number(item.tax_absolute, g.config.separator),
                net_sum: get_number(item.total_without_tax, g.config.separator),
                gross_sum: get_number(item.total, g.config.separator)
            };

            // next character for next tax rate
            c = String.fromCharCode(c.charCodeAt(0)+1);
        }
        else{
            tax_rates[t].tax_sum = tax_rates[t].tax_sum.plus(get_number(item.tax_absolute, g.config.separator));
            tax_rates[t].net_sum = tax_rates[t].net_sum.plus(get_number(item.total_without_tax, g.config.separator));
            tax_rates[t].gross_sum = tax_rates[t].gross_sum.plus(get_number(item.total, g.config.separator));
        }

        // clone the two rows
        io1 = item_template_1.clone();
        io2 = item_template_2.clone();

        // name
        $(".item-name", io1).text(item.name);

        // quantity and unit type
        if(item.unit_type == 'Piece') $(".item-unit", io2).html('&nbsp;');
        else $(".item-unit", io2).text(item.unit_type);


        $(".item-quantity", io2).text(item.quantity);

        // amount
        $(".item-amount", io2).text(item.total + " " + tax_rates[t].letter);

        $(".item-price", io2).text(item.base_price);
        $(".item-tax", io2).text(item.tax_percent + "%");
        $(".item-discount", io2).text(item.discount_absolute);

        // append to items_list
        items_list.append(io1);
        items_list.append(io2);
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
        $(".tax-net", tax_row).text(dn(data.net_sum, g));
        $(".tax-absolute", tax_row).text(dn(data.tax_sum, g));
        $(".tax-gross", tax_row).text(dn(data.gross_sum, g));

        tax_table.append(tax_row);
    });

    // set
    tax_row = $(".tax-row.footer", receipt);
    $(".tax-net", tax_row).text(dn(net_sum, g));
    $(".tax-absolute", tax_row).text(dn(tax_sum, g));
    $(".tax-gross", tax_row).text(dn(gross_sum, g));

    // currency
    $(".receipt-currency", receipt).text(g.config.currency);
    // the grand total
    $(".receipt-total", receipt).text(bill.data.total);

    // cashier name
    $(".receipt-cashier-name", receipt).text(g.data.user_name);
    $(".receipt-datetime", receipt).text(
        today(g.config.date_format) + " " + now(g.config.time_format)
    );

    // the calling function will handle the printing
    return receipt;
}