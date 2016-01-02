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
 * SETUP AND LOAD MAPS
 **************************************************/
$(document).ready(function(){
   // load Vehicles early as the types are prerequisite to other files
    $.getScript("js/vehicles.js",function(){
        // Start the vehcile expiration routine which should be executed at the specified interval.
        window.setInterval(function(){
          // If our map has been loaded then we can start "expiring" vehicles.
          if (mapLoaded) { expireVehicles(); }
        }, vehExpireCheckInterval);    
    });//Load the vehicle constructor
    // Load RainbowVis to color vehicle paths by height
    $.getScript("js/rainbowvis.js",function(){
        // Instanciate RainbowVis and set global color ramp by plane height
        window.polyRamp = new Rainbow();
        polyRamp.setNumberRange(minimumAltitude,maximumAltitude);
        polyRamp.setSpectrum(spectrum[0], spectrum[1], spectrum[2], spectrum[3]);
    });
    $.getScript("js/gmap_popup.js");//Load the google map popup constructors
    // Load the mapping system (Google only at the moment)
    $.getScript("https://maps.googleapis.com/maps/api/js?&callback=initMap&signed_in=true");
    // Global Google Maps objects are global. :)
      window.map = null;
      window.mapLoaded = false;
      window.vehData = {};// Create a generic array to hold our vehicle data
    $.getScript("js/gmap_init.js");//Initialize Gmaps by loading the initMap function
});

/***************************************************
 * LOAD MESSAGE HANDLER
 **************************************************/
$(document).ready(function(){
    $.getScript("js/messages.js");
});

/***************************************************
 * LOAD SIDEBAR
 **************************************************/
$(document).ready(function(){
         // load sidebar
         $.getScript("js/sidebar.js",function(){
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
});
