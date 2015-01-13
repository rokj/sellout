Payment = function(g, bill){
    // this object is called after the bill has been sent to server and checked;
    // choose payment type, pay and confirm (bitcoin and similar),
    // then create a new bill
    var p = this;

    p.g = g;
    p.bill = bill;
    p.data = p.bill.data;

    p.payment_interval = null; // a reference to timer for bitcoin queries on server
    p.bitcoin_payment_dots_interval = null;
    p.btc_qrcode_text = "";

    p.body = $("body");
    p.dialog = $("#payment");

    p.items = {
        cash:{
             button: $(".payment-type.cash", p.dialog),
             section: $(".payment-details.cash", p.dialog),

             paid_box: $(".cash .customer-paid", p.dialog),
             return_box: $(".cash .return-change", p.dialog)
        },
        credit_card:{
            button: $(".payment-type.credit-card", p.dialog),
            section: $(".payment-details.credit-card", p.dialog)
        },
        paypal:{
            button: $(".payment-type.paypal", p.dialog),
            section: $(".payment-details.paypal", p.dialog),
            customer_email: $('.payment-details.paypal #customer_email', p.dialog),
            send_invoice: $('.payment-details.paypal #send_paypal_invoice', p.dialog)
        },
        bitcoin:{
            button: $(".payment-type.bitcoin", p.dialog),
            section: $(".payment-details.bitcoin", p.dialog),
            btc_qrcode: $(".payment-details.bitcoin .btc-qrcode", p.dialog),
            bigger_btc_qrcode: $("div.bigger-btc-qrcode"),
            btc_amount: $(".payment-details.bitcoin .btc-amount", p.dialog),
            btc_address: $(".payment-details.bitcoin .btc-address", p.dialog),
            btc_address_container: $(".payment-details.bitcoin .btc-address-container", p.dialog),
            status_dialog: $(".status", p.dialog),
            status_dots: $(".status .waiting-payment .dot", p.dialog),
            status: {
                waiting_payment: $(".status .waiting-payment", p.dialog),
                paid: $(".status .paid", p.dialog)
            }
        },

        total: $(".bill-total", p.dialog), // common to all sections (payment types)
        shadow: $("#fullscreen_shadow"),

        print_button: $(".print", p.dialog),
        cancel_button: $("#cancel_payment", p.dialog)
    };

    //
    // methods
    //
    p.switch_section = function(section){
        // the last section is stored in g.settings
        send_data(p.g.urls.change_payment_type, {bill_id: p.data.id, type: section}, p.g.csrf_token, function(response) {
            if (response.status == 'ok') {
                clearInterval(p.payment_interval);
                clearInterval(p.bitcoin_payment_dots_interval);

                p.dialog.removeClass("cash");
                p.dialog.removeClass("credit_card");
                p.dialog.removeClass("bitcoin");
                p.dialog.removeClass("paypal");

                p.dialog.addClass(section);

                // first, hide sections
                p.items.cash.button.removeClass("active");
                p.items.cash.section.hide();

                p.items.credit_card.button.removeClass("active");
                p.items.credit_card.section.hide();

                p.toggle_bitcoin_section(false);
                p.toggle_paypal_section(false);

                // now display the required section
                p.g.settings.last_payment_type = section;

                switch (p.g.settings.last_payment_type) {
                    case "cash":
                        p.items.cash.button.addClass("active");
                        p.items.cash.section.show();

                        p.items.cash.paid_box.val("");
                        p.items.cash.return_box.val("");

                        p.items.cash.paid_box.focus();

                        p.items.print_button.show();
                        break;
                    case "credit_card":
                        p.items.credit_card.button.addClass("active");
                        p.items.credit_card.section.show();

                        p.items.print_button.show();
                        break;
                    case "paypal":
                        p.items.paypal.button.addClass("active");
                        p.items.paypal.section.show();
                        break;
                    case "bitcoin":
                        p.toggle_bitcoin_section(true);

                        p.items.print_button.hide();
                        break;
                }
            }
        });
    };

    p.toggle_paypal_section = function(show){
        if(show){
            p.items.paypal.button.addClass("active");
            p.items.paypal.section.show();

            if(p.payment_interval) clearInterval(p.payment_interval);

            // disable the print button on the dialog
            toggle_element(p.items.print_button, false);

            /*
            send_data(p.g.urls.get_payment_btc_info, {bill_id: p.data.id}, p.g.csrf_token, function(response) {
                if (response.status == 'ok') {
                    if ('data' in response && 'btc_address' in response.data && 'btc_amount' in response.data) {
                        p.items.bitcoin.btc_address.val(response.data.btc_address);
                        p.items.bitcoin.btc_address.data("value", response.data.btc_address);
                        p.items.bitcoin.btc_amount.html(response.data.btc_amount);
                        p.items.bitcoin.btc_qrcode.html("");
                        p.items.bitcoin.btc_qrcode.qrcode({width: 180, height: 160, text: "bitcoin:" + response.data.btc_address + "?amount=" + response.data.btc_amount, background: "#ebebeb"});

                        // set up a timer that will check if the bill has been paid
                        p.payment_interval = setInterval(function () {
                            send_data(p.g.urls.check_bill_status, {bill_id: p.data.id}, p.g.csrf_token, function (response) {
                                if (response.status != 'ok') {
                                    // something went wrong
                                    alert(response.message);
                                } else if (response.status == 'ok') {
                                    if (response.data.paid == 'true') {
                                        // paid, finish the thing
                                        alert("paid");
                                        // TODO

                                        clearInterval(p.payment_interval);
                                    }
                                    else {
                                        // not paid yet, continue polling

                                    }
                                }
                                console.log(response);
                            });
                        }, 2000);
                    } else {
                        error_message(gettext("Bitcoin payment problem"), gettext("Something went wrong when trying to get information about Bitcoin payment. Try later, or be nice and contact support."))
                    }
                }
            });
            */
        }
        else{
            p.items.paypal.button.removeClass("active");
            p.items.paypal.section.hide();

            // enable the print button
        }
    };

    p.items.paypal.send_invoice.click(function() {
        send_data(p.g.urls.send_invoice, {bill_id: p.data.id, customer_email: p.items.paypal.customer_email.val()}, p.g.csrf_token, function(response) {
            if (response.status == 'ok') {
                alert('sent invoice');
            }
        });
    });

    p.toggle_bitcoin_section = function(show){
        if(show){
            p.items.bitcoin.button.addClass("active");
            p.items.bitcoin.section.show();

            if(p.payment_interval) clearInterval(p.payment_interval);

            p.items.bitcoin.btc_qrcode.html("");
            p.items.bitcoin.btc_amount.val("");
            p.items.bitcoin.btc_address.html("");

            send_data(p.g.urls.get_payment_btc_info, {bill_id: p.data.id}, p.g.csrf_token, function(response) {
                if (response.status == 'ok') {
                    if ('data' in response && 'btc_address' in response.data && 'btc_amount' in response.data) {
                        p.items.bitcoin.status_dialog.show();
                        p.items.bitcoin.btc_address.val(response.data.btc_address);
                        p.items.bitcoin.btc_address.data("value", response.data.btc_address);
                        p.items.bitcoin.btc_amount.html(response.data.btc_amount);
                        p.items.bitcoin.btc_qrcode.html("");

                        p.btc_qrcode_text = "bitcoin:" + response.data.btc_address + "?amount=" + response.data.btc_amount;
                        p.items.bitcoin.btc_qrcode.qrcode({width: 120, height: 120, text: p.btc_qrcode_text, background: "#ebebeb"});

                        p.items.bitcoin.btc_qrcode.unbind().click(function() {
                            p.items.bitcoin.bigger_btc_qrcode.html("");
                            p.items.shadow
                                .css("z-index", window.last_dialog_zindex)
                                .hide()
                                .appendTo(p.body)
                                .fadeIn(function() {
                                    p.items.bitcoin.bigger_btc_qrcode.qrcode({width: 400, height: 400, text: p.btc_qrcode_text, background: "#ebebeb"});
                                    p.items.bitcoin.bigger_btc_qrcode.removeClass("hidden");
                                    p.bind_bigger_qrcode_dialog();
                                });
                        });

                        // set up a timer that will check if the bill has been paid
                        p.payment_interval = setInterval(function () {
                            send_data(p.g.urls.check_bill_status, {bill_id: p.data.id}, p.g.csrf_token, function (response) {
                                if (response.status != 'ok') {
                                    // something went wrong
                                    alert(response.message);
                                } else if (response.status == 'ok') {
                                    if (response.data.paid == true) {
                                        // paid, finish the thing
                                        clearInterval(p.payment_interval);
                                        clearInterval(p.bitcoin_payment_dots_interval);

                                        p.items.bitcoin.status.waiting_payment.hide();
                                        p.items.bitcoin.status.paid.css('display', 'block');
                                        p.items.print_button.show();
                                        p.items.cash.button.unbind();
                                        p.items.credit_card.button.unbind();
                                        p.items.cash.button.addClass('disabled');
                                        p.items.credit_card.button.addClass('disabled');

                                        toggle_element(p.items.print_button, true);
                                    } else {
                                        // not paid yet, continue polling
                                    }
                                }
                            });
                        }, 2000);

                        p.bitcoin_payment_dots_interval = setInterval(function () {
                            var active = 0;
                            var i = 0;

                            p.items.bitcoin.status_dots.each(function () {
                                if ($(this).hasClass('active')) {
                                    active = i;

                                    return false;
                                }

                                i++;
                            });

                            p.items.bitcoin.status_dots.removeClass("active");

                            if (active == 2) {
                                active = 0;
                            } else {
                                active++;
                            }

                            var i = 0;
                            p.items.bitcoin.status_dots.each(function () {
                                if (active == i) {
                                    $(this).addClass('active');

                                    return false;
                                }

                                i++;
                            });
                        }, 800);
                    } else {
                        error_message(gettext("Bitcoin payment problem"), gettext("Something went wrong when trying to get information about Bitcoin payment. Try later, or be nice and contact support."))
                    }
                }
            });
        } else {
            p.items.bitcoin.button.removeClass("active");
            p.items.bitcoin.section.hide();
            p.items.bitcoin.status_dialog.hide();
            // enable the print button
        }
    };

    p.toggle_dialog = function(show){
        if(show){
            p.dialog.show();
            p.items.shadow.fadeIn("fast");
        }
        else{
            p.dialog.hide();
            p.items.shadow.fadeOut("fast");
        }
    };

    p.print = function(html){
        // decide what to do depending on user's print settings

        // create a new element, and append it to body
        var receipt = $("<div>");

        // cut off all HTML yada yada that's already on this page
        var cutoff_to = "<!-- JS CUTOFF TO -->";
        var cutoff_from = "<!-- JS CUTOFF FROM -->";

        html = html.split(cutoff_to).pop(); // cut everything up to _to
        html = html.split(cutoff_from)[0]; // cut everyhing from _from on

        // printer driver:
        switch(p.g.objects.terminal.register.printer_driver){
            case 'System':
                // create some fine html graphics
                // create a HTML receipt and issue javascript print() method and that's it
                receipt.html(html);
                receipt.printThis();
                break;
            default:
                alert("Printer driver not implemented: " +
                    p.g.objects.terminal.register.printer_driver);
                break;
        }

        receipt.remove();
    };

    p.cancel = function(){
        confirmation_dialog(
            gettext("Confirm cancellation"),
            gettext("Are you sure you want to cancel this bill?"),
            function(){
                // yes, the user is 'sure';
                // send an update with status='Canceled' to the server
                var data = {
                    bill_id: p.data.id,
                    status: 'canceled'
                };

                send_data(p.g.urls.finish_bill, data, p.g.csrf_token, function(response){
                    if(response.status != 'ok'){
                        error_message(
                            gettext("Could not update bill status"),
                            response.message
                        );
                    }
                    else{
                        // create a new bill and close this dialog
                        p.g.objects.bill.clear();
                        p.toggle_dialog(false);
                    }
                });
            },
            function(){
            }
        );
    };

    p.finish = function(){
        // send an update of the bill to the server and print the bill
        var data = {
            bill_id: p.data.id,
            status: 'paid',
            payment_type: p.g.settings.last_payment_type,

            print: true,
            bill_format: p.g.objects.terminal.register.receipt_format
        };

        switch(data.payment_type){
            case 'cash':
                data.payment_reference = p.items.cash.paid_box.val();
                break;
            case 'credit_card':

                break;
            case 'bitcoin':

                break;
        }

        send_data(p.g.urls.finish_bill, data, p.g.csrf_token, function(response){
            if(response.status != 'ok'){
                error_message(
                    gettext("Could not save bill"),
                    response.message
                );
            }
            else{
                // everything is OK, print the thing
                p.print(response.bill);

                // the deal is finished. clear all stuff and create a new bill
                p.g.objects.bill.clear();

                // close the dialog
                p.toggle_dialog(false);

                // remove keyboard bindings
            }
        });
    };

    p.bind_escape_payment_dialog = function() {
        window.keyboard.add('escape-payment-dialog', 'escape', function() {
            window.keyboard.remove('escape-payment-dialog', 'escape');
            p.items.cancel_button.click();
        });
    }

    p.close_bigger_qrcode = function() {
        window.keyboard.remove('escape-bigger-qrcode-dialog', 'escape');
        window.keyboard.remove('escape-bigger-qrcode-dialog', 'enter');
        p.body.unbind();

        p.items.shadow.fadeOut("fast", function(){
            p.items.shadow.remove();
            p.items.bitcoin.bigger_btc_qrcode.addClass("hidden");
        });
    }

    p.bind_bigger_qrcode_dialog = function() {
        window.keyboard.add('escape-bigger-qrcode-dialog', 'escape', function() {
            p.close_bigger_qrcode();
        });

        window.keyboard.add('escape-bigger-qrcode-dialog', 'enter', function() {
            p.close_bigger_qrcode();
        });

        p.body.click(function() {
            p.close_bigger_qrcode();
        });
    }

    //
    // init
    //
    // events:
    // buttons
    p.items.cash.button.unbind().click(function(){ p.switch_section("cash"); });
    p.items.credit_card.button.unbind().click(function(){ p.switch_section("credit_card"); });
    p.items.bitcoin.button.unbind().click(function(){ p.switch_section("bitcoin"); });
    p.items.paypal.button.unbind().click(function(){ p.switch_section("paypal"); });

    // set total text
    p.items.total.text(p.data.total);

    // cash section: calculate return change on text input
    p.items.cash.paid_box.unbind().keyup(function(){
        var total = get_number(p.data.total, p.g.config.separator);
        if(!total){
            console.error("Bill has invalid total value");
            return; // wtf!
        }

        var paid = get_number($(this).val(), p.g.config.decimal_separator);
        if(!paid) return; // just ignore this key

        var ret = paid.minus(total);

        p.items.cash.return_box.val(dn(ret, p.g));
    });

    p.items.bitcoin.btc_address.click(function() {
        p.items.bitcoin.btc_address.focus().select();
    });

    p.items.bitcoin.btc_address.on('keyup keypress blur change', function() {
        $(this).val($(this).data("value"));
        p.items.bitcoin.btc_address.focus().select();
    });

    // the print ( = finish) button
    p.items.print_button.unbind().click(p.finish);

    // cancel button
    p.items.cancel_button.unbind().click(p.cancel);

    // show the dialog
    p.toggle_dialog(true);

    // show the details
    if(!p.g.settings.last_payment_type) p.g.settings.last_payment_type = "cash";
    p.switch_section(p.g.settings.last_payment_type);
};