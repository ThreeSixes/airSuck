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
 * Deps: jQuery, vehicles.js, google maps initialized
 **********************************************************/

/***************************************************
 * SOCKET MESSAGE HANDLER
 **************************************************/

function handleMessage(msg){
  if (!mapLoaded) {
    // Return early - the map isn't loaded yet
    if(debug){console.log("Maps not loaded. Discarding aircraft data.");}
    return;
  }
  if (!sidebarLoaded) {
    // Return early - the map isn't loaded yet
    if(debug){console.log("Sidebar not loaded. Discarding aircraft data.");}
    return;
  }
  // Dump the JSON string to the message box.
  if(debug){$('#' + messageBx).attr('value',msg);}
  
  // JSONify the JSON string.
  let msgJSON = JSON.parse(msg);
  
  // Return early - don't continue processing the keepalive.
  if ('keepalive' in msgJSON) {return;}
  
  // Store the vehicle name for reference in the function
  let vehName = "veh" + msgJSON.addr.toString();
  
  // See if we have a vehicle in our vehicle data.
  if (vehName in vehicles && vehicles[vehName] != null) {
    // existing vehicle, call the update function
    vehicles[vehName].update(msgJSON);
  } else {
    // new vehicle, call the constructor, create marker and set listeners
    let index;// we need an index to manually traverse the vehicleTypes associative array
    let length = vehicleTypes.length;
    for (index=0;index<length;++index) {
      if (msgJSON.type == vehicleTypes[index].protocol) {
        if (debug){console.log('New vehicle found, type registered: ' + msgJSON.type);}
        // add the new vehicle (constructor should call registered update functions)
        vehicles[vehName] = vehicleTypes[index].constructor(msgJSON);
        
        // create a marker icon for the vehicle (may move to the constructor)
        vehicles[vehName].setMarker();
        
        // Add listeners to marker - must be here to access the vehicles array
        vehicles[vehName].marker.addListener('click', function() {
          vehicleMarkerClickListener(vehName);
        });
        vehicles[vehName].marker.addListener('rightclick', function() {
          vehicleMarkerRightClickListener(vehName);
        });
        break;
      } else if (index==length) {
        // vehicle type not registered, drop data
        if (debug){console.log('New vehicle found, type not registered: ' + msgJSON.type + ' Dropping data.')}
      }
    }
  }
}

// Register the message handler
socket.on('message', handleMessage);