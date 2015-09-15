//  client.js by ThreeSixes (https://github.com/ThreeSixes)
//
//  This project is licensed under GPLv3. See COPYING for dtails.
//
//  This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

// Settings
var cfg = require('./config.js');
var config = cfg.getConfig();

// Main objects
var net = require('net');
var d1090 = new net.Socket();

// Log event.
function log(eventText) {
    // Just do a console.log().
    console.log(new Date().toISOString().replace(/T/, ' ') + ' - ' + eventText);
}

// Process message arrays.
function handleMessage(message) {
    
    // Loop through messages we got at the same time.
    for(i = 0; i < message.length; ++i) {
        
        // If we have non-empty data...
        if (message[i] != "") {
            log("Frame " + message[i]);
        }
    }
}

// Connect to our source dump1090 instance to get the "binary" frame data.
function connect2Dump1090() {
    // Connect up, log connection success.
    d1090.connect(config.client.dump1090Port, config.client.dump1090Host, function() {
        log('Connected to ' + config.client.dump1090Host + ':' + config.client.dump1090Port);
    });
}

// When we get data...
d1090.on('error', function(err) {
    // Puke error message out.
    log("Dump1090 socket error:\n" + err);
    
    // Destroy the connection since we don't want it anymore...
    d1090.destroy();
    
    // Find a way to wait for n amount of time.
    
    // Attempt reconnect.
    connect2Dump1090();
});

// When we get data...
d1090.on('data', function(data) {
    // Object -> String
    data = data.toString();
    
    // String -> Array
    data = data.split("\n");
    
    // Do something useful with the message.
    handleMessage(data)
});

// When the connection is closed...
d1090.on('close', function() {
    log('dump1090 connection to ' + config.client.dump1090Host + ':' + config.client.dump1090Port + ' closed');
});

// Make the initial attempt to connect, assuming we're enabled.
if (config.client.enabled) {
    connect2Dump1090();
}