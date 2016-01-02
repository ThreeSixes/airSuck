"use strict";// overcome current Chrome and Firefox issues with ECMA6 stuff like classes
/***********************************************************
 * Airsuck JS Socket Message Handler
 * v. 0.1
 *
 * Licensed under GPL V3
 * https://github.com/ThreeSixes/airSuck
 *
 * Handles socket.io messages for vehicle data coming from node
 *
 * Deps: jQuery, vehicles.js
 **********************************************************/

/***************************************************
 * SOCKET MESSAGE HANDLER
 **************************************************/

function handleMessage(msg){
  if (!mapLoaded) {
    if(debug){console.log("Maps not loaded. Discarding aircraft data.");}
    return;
  }
  
  // Dump the JSON string to the message box.
  if(debug){$('#' + messageBx).attr('value',msg);}
  
  // JSONify the JSON string.
  var msgJSON = JSON.parse(msg);
  
  // Don't continue processing the keepalive.
  if ('keepalive' in msgJSON) {
    return;
  }
  
  // Vehicle name
  var vehName = "veh" + msgJSON.addr.toString();
  
  // See if we have a vehicle in our vehicle data.
  // #### This decides to update an object or create a new one as necessary. Updates to the info window and such should be here.
  if (vehName in vehData) {
    // Update the properties for the aircraft.
    $.extend(true, vehData[vehName], msgJSON, {lastUpdate: new Date().getTime()});
    
    // If the info window is open, update it.
    if (vehData[vehName].info.shown == true) {
      // Set the content box.
      vehData[vehName].info.setContent(infoFactory(vehName));
    }
    
    // ********** VEHICLE OBJECTS **********
    // if (vehName in vehicles) { // replace the main IF above
    // Update vehicle info
    if (debug){console.log('Vehicle update received for: ' + msgJSON.addr);}
    // add the new vehicle (constructor should call registered update functions)
    vehicles[vehName].update(msgJSON);
    if (debug){console.log('Successfully updated: ' + vehicles[vehName].addr);}
    
    // ********** VEHICLE OBJECTS **********
    
  } else {
    // Add a new vehicle.
    vehData[vehName] = {
      lastPos: "none",
      lastUpdate: new Date().getTime(),
      active: true,
      pathPoly: new google.maps.Polyline({
        map: map,
        clickable: false,
        draggable: false,
        editable: false,
        geodesic: false,
        strokeOpacity: pathStrokeOpacity,
        strokeWeight: pathStrokeWeight,
        visible: true,
        zIndex: pathzIndex,
        path: new google.maps.MVCArray()
      })
    };
    
    // ********** VEHICLE OBJECTS **********
    
    // Add vehicle to the object array
    let index;
    let length = vehicleTypes.length;
    for (index=0;index<length;++index) {
      if (msgJSON.type == vehicleTypes[index].protocol) {
        if (debug){console.log('New vehicle found, type registered: ' + msgJSON.type);}
        // add the new vehicle (constructor should call registered update functions)
        vehicles[vehName] = vehicleTypes[index].constructor(msgJSON);
        if (debug){console.log('Successfully added: ' + vehicles[vehName].addr);}
        break;
      } else if (index==length) {
        // vehicle type not registered, drop data
        if (debug){console.log('New vehicle found, type not registered: ' + msgJSON.type + ' Dropping data.')}
      }
    }
    // ********** VEHICLE OBJECTS **********
    
    
    
    // Create objects for the aircraft's marker and current data as well as a flag for position changes, etc.
    $.extend(true, vehData[vehName], msgJSON);
    
    // Create our marker.
    var aMarker = new google.maps.Marker({
      icon: iconFactory(vehName, true),
      map: map,
      vehName: vehName
    });
      
    // Create our info window.
    var infowindow = new google.maps.InfoWindow({
      content: "",
      shown: false
    });
    
    // Add listener to marker to open info window
    aMarker.addListener('click', function() {
      // If our infoWindow is being shown...
      if (vehData[this.vehName].info.shown) {
        // Close it.
        vehData[this.vehName].info.close();
        vehData[this.vehName].info.setContent("");
        vehData[this.vehName].info.shown = false;
      } else {
        // Set data in case we don't have it, open it, and flag it as open.
        vehData[this.vehName].info.setContent(infoFactory(this.vehName));
        vehData[this.vehName].info.open(map, vehData[this.vehName].marker);
        vehData[this.vehName].info.shown = true;
        
      }
    });
    
    // Add listener to marker to show the path
    aMarker.addListener('rightclick', function() {
      // Check to see if the path is visible and reverse the visiblity
      if (vehData[this.vehName].pathPoly.getVisible() == true) {
        vehData[this.vehName].pathPoly.setVisible(false);
      } else {
        vehData[this.vehName].pathPoly.setVisible(true);
      }
    });
    
    // Run a second extend operation to set the marker and info window
    $.extend(true, vehData[vehName], {marker: aMarker, info: infowindow});
    
    // Set empty debugging string...
    var debugStr = "";
    
    // If we have idInfo...
    if ("idInfo" in vehData[vehName]) {
      // Add idInfo if we have it.
      debugStr = vehData[vehName].idInfo + " ";
    }
    
    // If we have a squawk...
    if ("aSquawk" in vehData[vehName]) {
      // Add the mode A sqawk code.
      debugStr = debugStr + "(" + vehData[vehName].aSquawk + ") ";
    }
    
    // If we have an IMO...
    if ("imo" in vehData[vehName]) {
      // Add the IMO if it's nonzero
      if (vehData[vehName].imo > 0) {
        debugStr = debugStr + "(" + vehData[vehName].imo + ") ";
      }
    }
    
    // Add address.
    debugStr = debugStr + "[" + vehData[vehName].addr.toString().toUpperCase() + "] ";
    
    // Update debug window
    if(debug){$('#' + debugBx).attr('value',"Hello " + debugStr);}
  }
  
  // If we have latitude and by extension longitude data...
  if (("lat" in vehData[vehName]) && mapLoaded) {
    
    // Figure out where we are in 2D space to determine whether or not we should move the marker.
    var thisPos = vehData[vehName].lat + "," + vehData[vehName].lon;
    
    // If we have new position daa...
    if (vehData[vehName].lastPos != thisPos) {
      var storePoint = [null, null, null]; // Lat, Lon, Alt
      var storeAlt = null;
      
      // If we have altitude data, we should store it.
      if ("alt" in vehData[vehName]) {
        storeAlt = vehData[vehName].alt;
      }
      
      // Create a new Google Maps LatLng object to use for the next two steps:
      var newPos = new google.maps.LatLng(vehData[vehName].lat, vehData[vehName].lon);
      
      // copy the path object
      var pathObject = vehData[vehName].pathPoly.getPath();
      
      // update with the new path
      pathObject.push(newPos);
      
      // push back to the polyline
      vehData[vehName].pathPoly.setPath(pathObject);
      
      var stkColor;
      if (vehData[vehName].type == "airAIS") {
        stkColor = "#00ffff";
      } else if (vehData[vehName].type == "airSSR") {
        stkColor = "#" + polyRamp.colourAt(vehData[vehName].alt / 1000);
      }
      // TESTING COLOR - set by height
      vehData[vehName].pathPoly.setOptions({strokeColor: stkColor});
      
      // Modify the icon to have the correct rotation, and to indicate there's bearing data.
      vehData[vehName].marker.setIcon(iconFactory(vehName, true));
      
      // Set the 2D data with what we have now.
      vehData[vehName].lastPos = thisPos;
      
      // Move the marker.
      vehData[vehName].marker.setPosition(newPos);
      
      // Set the initial location of the info window
      vehData[vehName].info.setPosition(newPos);
      
    }
  }
}

// When we get a message, put it in the box.
socket.on('message', handleMessage);