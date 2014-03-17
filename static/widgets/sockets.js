SocketConnection = function(g, socket_endpoint, company_id, user_id){
    var p = this;

    p.g = g;

    var options = {
        authToken: user_id + ":" + p.g.user_socket_token
    };

    p.connection = new Omnibus(WebSocket, socket_endpoint, options);

    // see docs/SOCKETS for info on channel names
    p.update_channel = p.connection.openChannel("update-" + company_id);

    //p.terminal_channel = p.connection.openChannel("terminal-" + user_id);

    p.update_channel_obj = null;
    p.terminal_channel_obj = null;

    p.connection
        .on(Omnibus.events.CONNECTION_ERROR, function(event){
            console.log("Error");
            console.log(event);
        })
        .on(Omnibus.events.CONNECTION_AUTHENTICATED, function(event){
            console.log("authenticated");
            console.log(event);
        })
        .on(Omnibus.events.CONNECTION_CONNECTED, function(event){
            console.log("connected");
            console.log(event);
        })
        .on("*", function(event){console.log(event);});

    p.update_channel
        .on(Omnibus.events.CHANNEL_SUBSCRIBED, function(event) {
            console.log("channel subscribed");
            console.log(event);
        })
        .on(Omnibus.events.CHANNEL_CLOSE, function(event) {
            console.log(event)
        })
        .on("*", function(event){console.log(event);});
    p.update_channel.send('wtf', 'asdf');

    /* TODO: handle connection events:
    Other events:
    Omnibus.events.CHANNEL_SUBSCRIBED
    Omnibus.events.CHANNEL_UNSUBSCRIBED
    Omnibus.events.CHANNEL_CLOSE
    Omnibus.events.CHANNEL_DESTROY
    Omnibus.events.CONNECTION_CONNECTED
    Omnibus.events.CONNECTION_DISCONNECTED
    Omnibus.events.CONNECTION_AUTHENTICATED
    Omnibus.events.CONNECTION_ERROR
    */

    //p.update_channel_obj = new UpdateChannel(g, g.ws.connection, company_id);
    //p.terminal_channel_obj = new TerminalChannel(g, g.ws.connection, user_id);
};

ChannelBase = function(g, channel){
    // common properties and methods for any websocket channel connection
    var p = this;

    p.g = g;
    p.channel = channel;

    //
    // common channel methods
    //
    p.send_message = function(id, data){
        p.channel.send(id, data);
    };

    //
    // common init
    //


    // channel events
    /*foo.on('msg', function(event){
        console.log(event);
    });*/

    /*setTimeout(function(){
        console.log("sending wtf");
        foo.send('msg', {text: "wtf"}) }, 2000);*/

};

UpdateChannel = function(g, channel){
    var p = this;

    // update channel: one for each company;
    // id = updates-<company-id>
    ChannelBase.call(p, g, channel);

    //
    // methods
    //

    //
    // init
    //

};

TerminalChannel = function(g, channel){
    var p = this;

    // terminal channel: one for each user
    ChannelBase.call(p, g, channel);

    //
    // methods
    //

    //
    // init
    //

    p.send_message('wtf', {text: 'fuk ju'});

};
