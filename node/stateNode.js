//  stateNode.js by ThreeSixes (https://github.com/ThreeSixes)
//
//  This project is licensed under GPLv3. See COPYING for dtails.
//
//  This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

// Settings
var cfg = require('./nodeConfig.js');
var config = cfg.getConfig();

// Set up our needed libraries.
var express = require('express');
var app = express();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var redis = require('redis');
var client = redis.createClient(config.server.redisPort, config.server.redisHost);

// If we're doing syslog let's load and setup the syslog stuff.
if (config.server.logMode == "syslog") {
  // Load the module.
  var syslog = require('node-syslog');
  
  // Configure the module.
  syslog.init("stateNode.js", syslog.LOG_PID | syslog.LOG_ODELAY, syslog.LOG_DAEMON);
}

// Log event.
function log(eventText) {
  // See how we log.
  switch (config.server.logMode) {
    // We're using syslog.
    case "syslog":
      //do the thing
      syslog.log(syslog.LOG_NOTICE, eventText);
      break;
    
    // We're logging to the console.
    case "console":
      // Do a console.log().
      console.log(new Date().toISOString().replace(/T/, ' ') + ' - ' + eventText);
      break;
    
    // No logging.
    case "none":
      // Do nothing.
      break;
    
    // IDK?
    default:
      break;
  }
}

// Serve index.html if a browser asks for it.
app.get('/', function(req, res){
  res.sendFile(__dirname + '/wwwroot/index.html');
});

// Serve our wwwroot folder as the web root.
app.use('/', express.static(__dirname + '/wwwroot'));

// When we have a message in Redis send it to all connected clients. 
client.on("message", function (channel, message) {
  io.emit("message", message)
});

// When we have an error on the redis queue. 
client.on("error", function (err) {
  // Log the client error.
  log("Redis client error detected: " + err);
  
  // Find a way to wait.
  
  // Try to subscribe to the queue again.
  subscribe();
});

// When have a new socket.io connection...
io.on('connection', function(socket){
  // Log a message to the console
  log("New client @ " + socket.request.connection.remoteAddress)
  
  // If they try to send us something give some generic error message.
  socket.on('message', function(msg){
    socket.emit("message", "{\"error\": \"Yeah, no.\"}");
  });
});

// Start the HTTP server up on our specified port.
http.listen(config.server.webPort, function(){
  // Log That we're now listening.
  log('stateNode.js listening on *:' + config.server.webPort);
  
  // Send a keepalive and schedule the next keepalive xmission.
  txKeepalive();
});

// Transmit a keepalive to all connected clients.
function txKeepalive() {
  // Create formatted date string.
  dateStr = new Date().toISOString().replace(/T/, ' ');
  dateStr = dateStr.substring(0, dateStr.length - 5);
  
  // Send keepalive message.
  io.emit("message", "{\"keepalive\": \"" + dateStr + "\"}");
  
  // Schedule our keepalive in our specified interval.
  setTimeout(txKeepalive, config.server.keepaliveInterval);
}

// Subscribe to our state queue.
function subscribe() {
  // Connect to our pub/sub queue.
  log('Subscribing to pub/sub queue.');
  
  // Subscribe to the state queue.
  client.subscribe(config.server.redisQueue);
}

// If we're enabled start up.
if (config.server.enabled) {
  // Subscribe to the state queue.
  log('Starting stateNode...');
  subscribe();
} else {
  log("node.js server not enabled in configuration, but executed.")
}
