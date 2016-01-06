"use strict";// overcome current Chrome and Firefox issues with ECMA6 stuff like classes
/***********************************************************
 * Airsuck JS initiator
 * v. 0.1
 *
 * Licensed under GPL V3
 * https://github.com/ThreeSixes/airSuck
 * 
 * Load required and optional JS files,
 * init JS main functions
 *
 * Deps: jquery
 **********************************************************/

/***************************************************
 * LOAD CONFIG OPTIONS AND HELPER SCRIPTS
 **************************************************/
// Load config options
$.getScript("js/config.js",function(){
   if (debug) {
     //debug set, create the screen debug elements
     $('body').append('<form><input type="text" class="dbgBx" id="debugBx" value="Debug stream..." /><input type="text" class="msgBx" id="message" value="Waiting for message data..." /></form>');
   }
   // set the html object ID for sending on-screen debug and messages
   window.debugBx = 'debugBx';//name of the debug input ID
   window.messageBx = 'message';//name of the message input ID
});// Load script dependencies

// Load Socket.IO
$.getScript("socket.io/socket.io.js",function(){
    window.socket = io();// Instanciate Socket.IO
});

/***************************************************
 * SETUP AND LOAD VEHICLES
 **************************************************/
// load Vehicles early as the types are prerequisite to other files
// load the Vehicle class first
 $.getScript("js/vehicles/vehicle.js",function(){
     // Start the vehcile expiration routine which should be executed at the specified interval.
     window.setInterval(function(){
       // If our map has been loaded then we can start "expiring" vehicles.
       if (mapLoaded) { expireVehicles(); }
     }, vehExpireCheckInterval);
     // Load any custom vehicles
     let index;
     for(index=0;index<loadCustomVehicles.length;index++) {
         if (debug) {console.log('Loading custom vehicle: ' + loadCustomVehicles[index]);}
         $.getScript("js/vehicles/" + loadCustomVehicles[index]);
     }
     
      // Prevent race condition where sidebar loads before vehicle types finish registration.
      setTimeout(function(){
         // Load the message handler
         $.getScript("js/core/messages.js");
         
         // load sidebar (here so it loads in the right order...)
         $.getScript("js/core/sidebar.js",function(){
            // setup the sidebar on successful load
            setupSidebar();
            
            // load font-awesome for icons
            $('<link/>', {
               rel: 'stylesheet',
               type: 'text/css',
               href: '/css/font-awesome/css/font-awesome.min.css'
            }).appendTo('head');
            
            // load sidebar CSS
            $('<link/>', {
               rel: 'stylesheet',
               type: 'text/css',
               href: '/css/sidebar.css'
            }).appendTo('head');
         });  
      }, 0.05);
     
 });

/***************************************************
 * SETUP AND LOAD MAPS
 **************************************************/
$(document).ready(function(){
    // Load RainbowVis to color vehicle paths by height
    $.getScript("js/plugins/rainbowvis.js",function(){
        // Instanciate RainbowVis and set global color ramp by plane height
        window.polyRamp = new Rainbow();
        polyRamp.setNumberRange(minimumAltitude,maximumAltitude);
        polyRamp.setSpectrum(spectrum[0], spectrum[1], spectrum[2], spectrum[3]);
    });
    // Load the mapping system (Google only at the moment)
    $.getScript("https://maps.googleapis.com/maps/api/js?&callback=initMap&signed_in=true");
    // Global Google Maps objects are global. :)
      window.map = null;
      window.mapLoaded = false;
      window.vehData = {};// Create a generic array to hold our vehicle data
    $.getScript("js/core/gmap_init.js");//Initialize Gmaps by loading the initMap function
});
