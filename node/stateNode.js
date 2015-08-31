//  stateNode.js by ThreeSixes (https://github.com/ThreeSixes)
//
//  This project is licensed under GPLv3. See COPYING for dtails.
//
//  This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

// Settings
var webPort = 8090;
var redisPort = 6379;
var redisHost = "brick";
var redisQueue = 'airStateFeed';

// Set up our needed libraries.
var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var redis = require('redis');
var client = redis.createClient(redisPort, redisHost);

// Serve index.html if a browser asks for it.
app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html');
});

// Serve a version of jQuery.
app.get('/jquery-2.1.4.min.js', function(req, res){
  res.sendFile(__dirname + '/jquery-2.1.4.min.js');
});

// When we have a message in Redis send it to all connected clients. 
client.on("message", function (channel, message) {
  io.emit("message", message)
  //console.log("MSG: " + message)
});

// When have a new socket.io connection...
io.on('connection', function(socket){
  // Log a message to the console
  console.log("New client @ " + socket.request.connection.remoteAddress)
  
  // If they try to send us something give some generic error message.
  socket.on('message', function(msg){
    socket.emit("message", "{\"error\": \"Yeah, no.\"}");
  });
});

// Start the HTTP server up on our specified port.
http.listen(webPort, function(){
  console.log('airSuck-stateNode.js listening on *:' + webPort);
});

// Subscribe to the state queue.
client.subscribe(redisQueue);
