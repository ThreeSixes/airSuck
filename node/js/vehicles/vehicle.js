"use strict";// overcome current Chrome and Firefox issues with ECMA6 stuff like classes
/***********************************************************
 * Airsuck JS vehicle-specific functions
 * v. 0.1
 *
 * Licensed under GPL V3
 * https://github.com/ThreeSixes/airSuck
 * 
 * Vehicle class prototype definition and functions, some
 * to be replaced by custom vehicle types
 *
 * Deps: jQuery
 **********************************************************/

/***************************************************
 * TO DO
 **************************************************/
// Create a destructor registration for additional functions as destruction
// Create an updater registration for additional functions as update

/***************************************************
 * MISC HELPERS
 **************************************************/

// Converts a heading from degrees to a cardinal direction, 16 settings
function degreeToCardinal(degree) {
  let bearing;
  //determing the relevant bearing
  bearing = Math.round(degree / (360/16));
  // return the relevant cardinal bearing
  switch (bearing) {
    case 0:return 'N';break;
    case 1:return 'NNE';break;
    case 2:return 'NE';break;
    case 3:return 'ENE';break;
    case 4:return 'E';break;
    case 5:return 'ESE';break;
    case 6:return 'SE';break;
    case 7:return 'SSE';break;
    case 8:return 'S';break;
    case 9:return 'SSW';break;
    case 10:return 'SW';break;
    case 11:return 'WSW';break;
    case 12:return 'W';break;
    case 13:return 'WNW';break;
    case 14:return 'NW';break;
    case 15:return 'NNW';break;
    case 16:return 'N';break;
    default:
      if (debug){console.log('degreeToBearing: error in calculating bearing');}
      return null;
      break;
  }
};

/***************************************************
 * VEHICLE PROTOTYPE
 **************************************************/

class Vehicle {
  constructor(msgJSON,protocol){
    if(debug){console.log('Vehicle constructor executed for vehicle: ' + msgJSON.addr + ', Using protocol: ' + protocol);}
    this.addr = msgJSON.addr;
    this.protocol = protocol;// communications protocol used (AIS,SSR)
    this.updateFunctions = [];// array to register update functions such as refreshing table rows, icons, popups
    this.destructorFunction = [];// array to register destructor functions
    this.lastPos = "none";
    this.lastUpdate = new Date().getTime();
    this.active = true;// set true if the vehicle is currently active
    this.maxAge = 1000;// default vehicle expiration time in milliseconds since last contact
    // gMap icon stuff
    this.dirIcoPath = "m 0,0 -20,50 20,-20 20,20 -20,-50"; // Path we want to use for ADS-B targets we have direction data for.
    this.dirIcoScale = 0.15; // Scale of the path.
    this.ndIcoPath = "m 15,15 a 15,15 0 1 1 -30,0 15,15 0 1 1 30,0 z"; // Path we want to sue for ADS-B targets we don't have direction data for.
    this.ndIcoSacle = 0.24; // Scale of the path.
    this.vehColorActive = "#ff0000"; // Color of active aircraft icons (hex)
    this.vehColorInactive = "#660000"; // Color of nonresponsive aircraft icons (hex)
    // gMap polygon path object
    this.pathPoly = new google.maps.Polyline({
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
    
  }
}

/***************************************************
 * FUNCTIONS UPDATE THE VEHICLE INFO AND TABLE ENTRY
 * updateTableEntry function to be overridden by
 * custom vehicle types
 **************************************************/
Vehicle.prototype.updateTableEntry = function(){
  if (debug){console.log('Error: Function updateTableEntry not set for protocol: '+this.protocol);}
  return;
};


Vehicle.prototype.update = function(msgJSON){
  // update data in the object
  $.extend(true, this, msgJSON);
  // update the last update parameter
  this.lastUpdate = Date.now();
  // temporary, need to make these modular and use the updateFunctions array, static for now
  this.updateTableEntry();
  // run each function registered in the updateFunctions array
  this.updateFunctions.forEach(function(){
    //updater(this.addr);
  });
};

/***************************************************
 * VEHICLE DESTRUCTOR
 * CUSTOM VEHICLES MAY REGISTER ADDITIONAL
 * DESTRUCTOR FUNCTIONS
 **************************************************/
Vehicle.prototype.destroy = function(){
  if(debug){console.log('Destroying vehicle: ' + this.parseName());}
  
  // Run add-on destructor processes
  //this.destructorFunctions.forEach(function(){
    //destructor(this.addr);
  //});
  
  // Remove table entries
  $('#'+this.addr).remove();
  
  // Default destructor processes
  //if(this.info != 'undefined'){this.info.close();}// close the gMap info window
  //this.pathPoly.setVisible(false);// turn off the path
  //this.marker.setMap(null);// remove the icon from the map
  //vehicles[this.addr] = null;// invalidate this object, can't fully delete since its gone in ECMAScript 6...
};

/***************************************************
 * FUNCTION SETS THE ICON TO HALFLIFE, SETS INACTIVE
 **************************************************/
Vehicle.prototype.setHalflife = function(){
  if(debug){console.log("Halflife reached for " + this.parseName());}
  // Deactivate vehicle and change the icon for it.
  this.active = false;
  //if(this.marker!='undefined'){this.marker.setIcon(this.createIcon());}
};

/***************************************************
 * FUNCTION DETERMINES IF A VEHICLE SHOULD BE
 * SET TO HALFLIFE, EXPIRED, OR REMAIN ACTIVE
 **************************************************/
Vehicle.prototype.checkExpiration = function(){
  //if(debug){console.log("Checking expiration for " + this.parseName());}
  // Compute the time delta
  let vehDelta = Date.now() - this.lastUpdate;
  // Return Active, Halflife, or Expired
  if (vehDelta >= this.maxAge) {
    return('Expired');
  } else if ((vehDelta >= (this.maxAge/2)) && (this.active == true)) {
    return('Halflife');
  } else {
    return('Active');
  }
};

/***************************************************
 * DEFAULT FUNCTION DETERMINES VEHICLE NAME
 * TO BE OVERRIDEN BY CUSTOM VEHICLES
 **************************************************/
Vehicle.prototype.parseName = function() {
  // default vehicle name function, to be customized per vehicle type
  return this.addr.toUpperCase();
};

/***************************************************
 * FUNCTION CREATES VEHICLE ICONS FOR GMAPS
 * OVERRIDE IF USING A DIFFERENT HEADING
 **************************************************/
Vehicle.prototype.createIcon = function() {
   // If we have heading data for the vehicle
  if (this.heading != 'undefined') {
    // Create our icon for a vehicle with heading data.
    var newIcon = new google.maps.Marker({
      path: this.dirIcoPath,
      scale: this.dirIcoScale,
      strokeWeight: 1.5,
      strokeColor: (this.active == true) ? this.vehColorActive : this.vehColorInactive,
      rotation: this.heading
    });
  } else {
    // Create our icon for a vehicle without heading data.
    var newIcon = new google.maps.Marker({
      path: this.ndIcoPath,
      scale: this.ndIcoScale,
      strokeWeight: 1.5,
      strokeColor: (this.active == true) ? this.vehColorActive : this.vehColorInactive
    });
  }
  // And return it.
  return newIcon;
};

/***************************************************
 * FUNCTION ADDS A GMAPS MARKER TO THE VEHICLE
 **************************************************/
Vehicle.prototype.setMarker = function() {
  // Create our marker.
  this.marker = new google.maps.Marker({
    icon: this.createIcon(),
    map: map,
    vehName: vehName
  });
  
  // Add listener to marker to open info window
  this.marker.addListener('click', function() {
    // If our infoWindow is being shown...
    if (this.info.shown) {
      // Close it.
      this.info.close();
      this.info.setContent("");
      this.info.shown = false;
    } else {
      // Set data in case we don't have it, open it, and flag it as open.
      this.info.setContent(infoFactory(this.addr));
      this.info.open(map, this.marker);
      this.info.shown = true;
    }
  });
  
  // Add listener to marker to show the path
  this.marker.addListener('rightclick', function() {
    // Check to see if the path is visible and reverse the visiblity
    if (this.pathPoly.getVisible() == true) {
      this.pathPoly.setVisible(false);
    } else {
      this.pathPoly.setVisible(true);
    }
  });
}

/***************************************************
 * FUNCTION MOVES THE VEHICLE MARKER AND INFO POSITIONS
 **************************************************/
Vehicle.prototype.movePosition = function() {
    // Figure out where we are in 2D space to determine whether or not we should move the marker.
    let thisPos = this.lat + "," + this.lon;
    // If we have new position daa...
    if (this.lastPos != thisPos) {
      // Create a new Google Maps LatLng object to use for the next two steps:
      let newPos = new google.maps.LatLng(this.lat, this.lon);
      // copy the path object
      let pathObject = this.pathPoly.getPath();
      
      // update with the new path
      pathObject.push(newPos);
      // push back to the polyline
      this.pathPoly.setPath(pathObject);
      // set the polyline color
      this.pathPoly.setOptions({strokeColor: this.stkColor});
      // Modify the icon to have the correct rotation, and to indicate there's bearing data.
      this.marker.setIcon(this.setIcon());
      
      // Set the 2D data with what we have now.
      this.lastPos = thisPos;
      
      // Move the marker.
      this.marker.setPosition(thisPos);
      // Set the initial location of the info window
      this.info.setPosition(thisPos);
    }
};

/***************************************************
 * FUNCTION ADDS A GMAPS INFO WINDOW TO THE VEHICLE
 **************************************************/
Vehicle.prototype.setInfoWindow = function() {
  // Create our info window.
  this.info = new google.maps.InfoWindow({
    content: "",
    shown: false
  });
}

/***************************************************
 * VEHICLE TYPE REGISTRATION
 * CUSTOM VEHICLES NEED TO REGISTER USING THIS FUNCTION
 **************************************************/
// Function to register new vehicle types
function registerVehicleType(newProtocol,newDomName,newFaIcon,newConstructor,newTableHeader) {
  // TO DO: validate input
  vehicleTypes.push({
    protocol: newProtocol,// the name to look for in the type field of incoming data
    domName: newDomName,// the name used for this vehicle type in the DOM
    faIcon: newFaIcon,// the icon used for this vehicle type in the sidebar and menus
    constructor: newConstructor,// constructor function for this vehicle type
    buildTable: newTableHeader// header row to use for this vehicle type in its' data table
  });
};



/***************************************************
 *
 *
 *
 *
 * CODE BELOW TO BE REPLACED IN VEHICLE OBJECTS
 *
 *
 *
 *
 **************************************************/

/***************************************************
 * VEHICLE ICON FACTORY
 * REPLACED FOR VEHICLE OBJECTS
 **************************************************/
// Create icons for vehicles.
function iconFactory(vehName) {
  var dirIcoPath = null;
  var dirIcoScale = null;
  var ndIcoPath = null;
  var ndIcoScale = null;
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
    var newIcon = new google.maps.Marker({
      path: dirIcoPath,
      scale: dirIcoScale,
      strokeWeight: 1.5,
      strokeColor: vehColor,
      rotation: vehRotation
    });
  } else {
    // Create our icon for a vehicle without heading data.
    var newIcon = new google.maps.Marker({
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
 * VEHICLE DESRUCTOR - to be replaced for Vehicle Objects
 * REPLACED FOR VEHICLE OBJECTS
 **************************************************/
// Expire vehicles.
function expireVehicles() {
  
  // ***********************************************************
  // ************** EXPIRE CODE FOR VEHICLE OBJECTS ************
  // ***********************************************************
  if (debug){console.log("Expiration check running");}
  let key;
  for (key in vehicles) {
    // Get the state of the vehicle and take appropriate action
    // Don't run the check on nulled objects because JS ECMAScript 6 doesn't allow delete...
    if (vehicles[key]!=null) {
      switch (vehicles[key].checkExpiration()) {
          case 'Halflife':
            if (debug) {console.log('Halflife determined for vehicle: '+vehicles[key].parseName());}
            vehicles[key].setHalflife();
            break;
          case 'Expired':
            if (debug) {console.log('Expiration determined for vehicle: '+vehicles[key].parseName());}
            // Vehicle expired, cleanup the vehicles things...
            vehicles[key].destroy();
            // Nullify the entry since ECMAScript 6 doesn't let us use destroy
            vehicles[key]=null;
            break;
          default:
            // Do nothing on active or other
            break;
      }
    }
  }
  // ***********************************************************
  // ***********************************************************
  
  
  // Set the time we started the process of checking.
  var checkStart = new Date().getTime();
  // ************** LOOPS THROUGH VEHICLES ***************
  // Loop through every vehicle we have data on
  for (var veh in vehData) {
    var vehAge = null;
    // Determine the vehicle age.
    switch (vehData[veh].type) {
      case "airSSR":vehAge = aircraftAge;break;
      case "airAIS":vehAge = shipAge;break;
      default:
        // Just expire things we don't support.
        vehAge = 1000;break;
    }
    // Compute the time delta and set up halflife.
    var vehDelta = checkStart - vehData[veh].lastUpdate;
    var vehHalflife = vehAge / 2;
    var vehNotNuked = true;
    var changed = false;
    
    // Set empty debugging string...
    var debugStr = "";
    // If we have idInfo...
    if ("idInfo" in vehData[veh]) {debugStr = vehData[veh].idInfo + " ";}
    // If we have a squawk...
    if ("aSquawk" in vehData[veh]) {debugStr = debugStr + "(" + vehData[veh].aSquawk + ") ";}
    // Add ICAO address.
    debugStr = debugStr + "[" + vehData[veh].addr + "]";
    
    // Check to see if we haven't heard from them in our age time.
    if (vehDelta >= vehAge) {
      // ************** KILLS AN OBJECT BEYOND ITS EXPIRATION AGE ***************
      
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
      // ************** TURNS ICON TO INACTIVE ***************
      
      // Update debug window
      if(debug){$('#' + debugBx).attr('value',"Half life reached for " + debugStr);}
      
      // Deactivate vehicle and change the icon for it.
      vehData[veh].active = false;
      vehData[veh].marker.setIcon(iconFactory(veh));
      changed = true;
    } else {
      // ************** ACTIVATES INACTIVE ICON ***************
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
    
    /*
    // ************** MOVES VEHICLE ICON - ADD TO UPDATE FUNCTION ***************
    // If we have position data
    if (changed && vehNotNuked && vehData[veh].lat) {
      // Create Google maps position object.
      var newPos = new google.maps.LatLng(vehData[veh].lat, vehData[veh].lon);
      
      // Redraw the marker and move inte infowindow.
      vehData[veh].marker.setPosition(newPos);
      vehData[veh].info.setPosition(newPos);
    }*/
  }
}