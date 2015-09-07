//  stateNode.js by ThreeSixes (https://github.com/ThreeSixes)
//
//  This project is licensed under GPLv3. See COPYING for dtails.
//
//  This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

// Settings
var cfg = require('./config.js');
var config = cfg.getConfig();

// Set up our needed libraries.
var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var redis = require('redis');
var client = redis.createClient(config.redisPort, config.redisHost);

// Serve index.html if a browser asks for it.
app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html');
});

// Serve a version of jQuery.
app.get('/jquery-2.1.4.min.js', function(req, res){
  res.sendFile(__dirname + '/jquery-2.1.4.min.js');
});

// Serve a version of rainbowvis.js
app.get('/rainbowvis.js', function(req, res){
  res.sendFile(__dirname + '/rainbowvis.js');
});

// When we have a message in Redis send it to all connected clients. 
client.on("message", function (channel, message) {
  io.emit("message", message)
});

// When have a new socket.io connection...
io.on('connection', function(socket){
  // Log a message to the console
  console.log(new Date().toISOString().replace(/T/, ' ') + " - New client @ " + socket.request.connection.remoteAddress)
  
  // If they try to send us something give some generic error message.
  socket.on('message', function(msg){
    socket.emit("message", "{\"error\": \"Yeah, no.\"}");
  });
});

// Start the HTTP server up on our specified port.
http.listen(config.webPort, function(){
  // Log That we're now listening.
  console.log(new Date().toISOString().replace(/T/, ' ') + ' - stateNode.js listening on *:' + config.webPort);
  
  // Send a keepalive and schedule the next keepalive xmission.
  txKeepalive();
});

// Transmit a keepalive to all connected clients.
function txKeepalive() {
  // Create formatted date string.
  dateStr = new Date().toISOString().replace(/T/, ' ');
  dateStr = dateStr.substring(0, dateStr.length - 5);
  
  // Log keepalive transmission.
  //console.log(new Date().toISOString().replace(/T/, ' ') + " - Sent keepalive")
  
  // Send keepalive message.
  io.emit("message", "{\"keepalive\": \"" + dateStr + "\"}");
  
  // Schedule our keepalive in our specified interval.
  setTimeout(txKeepalive, config.keepaliveInterval);
}

// Subscribe to the state queue.
client.subscribe(config.redisQueue);

