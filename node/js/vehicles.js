/***********************************************************
 * Airsuck JS vehicle-specific functions
 * v. 0.1
 *
 * Licensed under GPL V3
 * https://github.com/ThreeSixes/airSuck
 * 
 * Vehicle creator, manipulation, and destruction functions
 *
 * Deps: jQuery
 **********************************************************/

/***************************************************
 * VEHICLE ICON FACTORY
 **************************************************/
// Create icons for vehicles.
function iconFactory(vehName) {
  var dirIcoPath = null;
  var dirIcoScl = null;
  var ndIcoPath = null;
  var ndIcoScl = null;
  var vehColor = null;
  var vehRotation = null;
  
  // Determine the vehicle age.
    switch (vehData[vehName].type) {
      case "airSSR":
        // Select vehicle properties.
        dirIcoPath = dirAircraft;
        dirIcoScale = dirAircraftScl;
        ndIcoPath = ndAircraft;
        ndIcoScale = ndAircraftScl;
        
        // Pick active/inactive color.
        if (vehData[vehName].active == true) {
          vehColor = aircraftActive; 
        } else {
          vehColor = aircraftInactive;
        }
        
        break;
      
      case "airAIS":
        // Select vehicle properties.
        dirIcoPath = dirShip;
        dirIcoScale = dirShipScl;
        ndIcoPath = ndShip;
        ndIcoScale = ndShipScl;
        
        // Pick active/inactive color.
        if (vehData[vehName].active == true) {
          vehColor = shipActive; 
        } else {
          vehColor = shipInactive;
        }
        
        break;
      
      default:
        break;
    } 
  
  // If we have heading data for the vehicle
  if (('heading' in vehData[vehName]) || ('courseOverGnd' in vehData[vehName])) {
    
    // If we have a heading, that's great.
    if ('heading' in vehData[vehName]) {
      vehRotation = vehData[vehName].heading;
    }
    
    // Pick course over ground above heading if possible.
    if ('courseOverGnd' in vehData[vehName]) {
      vehRotation = vehData[vehName].courseOverGnd;
    }
    
    // Create our icon for a vehicle with heading data.
    newIcon = new google.maps.Marker({
      path: dirIcoPath,
      scale: dirIcoScale,
      strokeWeight: 1.5,
      strokeColor: vehColor,
      rotation: vehRotation
    });
  } else {
    // Create our icon for a vehicle without heading data.
    newIcon = new google.maps.Marker({
      path: ndIcoPath,
      scale: ndIcoScale,
      strokeWeight: 1.5,
      strokeColor: vehColor
    });
  }
  
  // And return it.
  return newIcon;
}

/***************************************************
 * VEHICLE DESRUCTOR
 **************************************************/
// Expire vehicles.
function expireVehicles() {
  // Set the time we started the process of checking.
  var checkStart = new Date().getTime();
  
  // Loop through every vehicle we have data on
  for (var veh in vehData) {
    var vehAge = null;
    
    // Determine the vehicle age.
    switch (vehData[veh].type) {
      case "airSSR":
        vehAge = aircraftAge;
        break;
      
      case "airAIS":
        vehAge = shipAge;
        break;
      
      default:
        // Just expire things we don't support.
        vehAge = 1000;
        break;
    }
    
    // Compute the time delta and set up halflife.
    var vehDelta = checkStart - vehData[veh].lastUpdate;
    var vehHalflife = vehAge / 2;
    var vehNotNuked = true;
    var changed = false;
    
    // Set empty debugging string...
    debugStr = "";
    
    // If we have idInfo...
    if ("idInfo" in vehData[veh]) {
      // Add idInfo if we have it.
      debugStr = vehData[veh].idInfo + " ";
    }
    
    // If we have a squawk...
    if ("aSquawk" in vehData[veh]) {
      // Add the mode A sqawk code.
      debugStr = debugStr + "(" + vehData[veh].aSquawk + ") ";
    }
    
    // Add ICAO address.
    debugStr = debugStr + "[" + vehData[veh].addr + "]";
    
    // Check to see if we haven't heard from them in our age time.
    if (vehDelta >= vehAge) {
      
      // Update debug window
      if (debug) {$('#' + debugBx).attr('value',"Goodbye " + debugStr);}
      
      // Close an open info window, nuke the marker for the expred vehicle, and nuke the vehicle's object.
      vehData[veh].info.close();
      vehData[veh].marker.setMap(null);
      vehData[veh].pathPoly.setVisible(false);
      vehData[veh] = null;
      delete vehData[veh];
      vehNotNuked = false;
      
    } else if ((vehDelta >= vehHalflife) && (vehData[veh].active == true)) {
      
      // Update debug window
      if(debug){$('#' + debugBx).attr('value',"Half life reached for " + debugStr);}
      
      // Deactivate vehicle and change the icon for it.
      vehData[veh].active = false;
      vehData[veh].marker.setIcon(iconFactory(veh));
      changed = true;
    } else {
      // If it's marked as inactive the reactivate it.
      if ((vehDelta < vehHalflife) && (vehData[veh].active == false)) {
        
        // Update debug window
        if(debug){$('#' + debugBx).attr('value',"Reviving " + debugStr);}
        
        // Activate vehicle and change the icon for it.
        vehData[veh].active = true;
        vehData[veh].marker.setIcon(iconFactory(veh));
        changed = true;
      }
    }
    
    // If we have position data
    if (changed && vehNotNuked && vehData[veh].lat) {
      // Create Google maps position object.
      var newPos = new google.maps.LatLng(vehData[veh].lat, vehData[veh].lon);
      
      // Redraw the marker and move inte infowindow.
      vehData[veh].marker.setPosition(newPos);
      vehData[vehName].info.setPosition(newPos);
    }
  }
}