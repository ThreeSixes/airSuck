"use strict";// overcome current Chrome and Firefox issues with ECMA6 stuff like classes
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
 * MISC HELPERS
 **************************************************/

// Converts a heading from degrees to a N,S,E,W
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
    this.active = true;
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

// update function, created as prototype for single definition
Vehicle.prototype.update = function(msgJSON){
  if(debug){console.log('Vehicle updater called for: ' + this.addr);}
  // update data in the object
  $.extend(true, this, msgJSON);
  // update the last update parameter
  this.lastUpdate = new Date().getTime();
  // temporary, need to make these modular and use the updateFunctions array, static for now
  this.updateTableEntry();
  // run each function registered in the updateFunctions array
  this.updateFunctions.forEach(function(){
    //updater(this.addr);
  });
};

// create the destructor as a prototype function (defined once)
Vehicle.prototype.destroy = function(){
  if(debug){console.log('Vehicle destructor called for: ' + this.addr);}
  // run each function registered in the updateFunctions array
  this.destructorFunctions.forEach(function(){
    //destructor(this.addr);
  });
};

// ********************
// TO AIS FILE

// AIS object extending Vehicle
class Ship extends Vehicle {
  constructor(msgJSON) {
    // create the generic vehicle object
    super(msgJSON,'AIS');
    // extend with AIS specific data
    $.extend(true, this, msgJSON);
    // add additional parameters
    this.domName = 'AIS';
    // set the name string
    this.name = this.parseName();
    // create the table entry
    this.createTableEntry();
  }
}

// Register vehicle type
if(debug){console.log('Registering vehicle type: AIS');}
//vehicleTypes['airAIS'] = {
vehicleTypes.push({
  protocol: 'airAIS',
  domName: 'AIS',
  faIcon: 'fa-ship',
  constructor: function(msgJSON) {
    if (debug) {console.log('AIS Constructor called with message: ' + msgJSON);}
    return new Ship(msgJSON);
    },
  buildTable: function(container) {
    $(container).append('<tr><th>ID</th><th>Type</th><th>Flag</th><th>Velocity</th><th>Destination</th><th>Has Pos</th></tr>');
  }
});

// Prototype function to create the vehicle name for display
Ship.prototype.parseName = function() {
  let idStr='';
  // If we have a vessel name
  if (this.vesselName) {idStr += this.vesselName + " ";}
  // If we have a valid IMO
  idStr += "(" + this.imo + ((this.imoCheck==false) ? "*" : "") + ") ";
  if (this.aSquawk) {idStr += "(" + this.aSquawk + ") ";}
  // We should always have an MMSI address.
  idStr += "[" + this.addr.toString() + "]";
  return idStr;
  /*
  // If we an IMO that doesn't check out...
    if ("imoCheck" in vehData[vehName]) {
      if (vehData[vehName].imoCheck == false) {
        imoFlagStr = "*";
      }
    }
    // If we have a non-zero IMO...
    if ("imo" in vehData[vehName]) {
      if (vehData[vehName].imo > 0) {
        idStr += "(" + vehData[vehName].imo + imoFlagStr + ") ";
      }
    }*/
};

// Prototype function to add an entry to the ship table
Ship.prototype.createTableEntry = function() {
  if (debug) {console.log('Creating new table entry for ship: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  $('#table-'+this.domName).children('tbody').append('<tr id="'+this.addr+'"><td>'+this.name+'</td><td>'+((this.shipType==null) ? '' : this.shipType)+'</td><td>'+((this.mmsiCC==null) ? '' : this.mmsiCC)+'</td><td>'+((this.velo==null) ? '' : this.velo + ' kts')+'</td><td>'+((this.destination==null) ? '' : this.destination)+'</td><td>'+hasPos+'</td></tr>');
};
// Prototype function to update entry in the ship table
Ship.prototype.updateTableEntry = function() {
  if (debug) {console.log('Updating new table entry for ship: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  $('#'+this.addr).html('<td>'+this.name+'</td><td>'+((this.shipType==null) ? '' : this.shipType)+'</td><td>'+((this.mmsiCC==null) ? '' : this.mmsiCC)+'</td><td>'+((this.velo==null) ? '' : this.velo + ' kts')+'</td><td>'+((this.destination==null) ? '' : this.destination)+'</td><td>'+hasPos+'</td>');
};

//Ship.prototype.updateIcon = function() {};

// ********************
// TO SSR FILE

// SSR object extending Vehicle
class Aircraft extends Vehicle {
  constructor(msgJSON) {
    // create the generic vehicle object
    super(msgJSON,'SSR');
    // extend with SSR specific data
    $.extend(true, this, msgJSON);
    // add additional parameters
    this.domName = 'SSR';
    // set the name string
    this.name = this.parseName();
    // create the table entry
    this.createTableEntry();
  }
}

// Register vehicle type
if(debug){console.log('Registering vehicle type: SSR');}
//vehicleTypes['airSSR'] = {
vehicleTypes.push({
  protocol: 'airSSR',
  domName: 'SSR',
  faIcon: 'fa-plane',
  constructor: function(msgJSON) {
    if (debug) {console.log('SSR Constructor called with message: ' + msgJSON);}
    return new Aircraft(msgJSON);
    },
  buildTable: function(container) {
    $(container).append('<tr><th>ID</th><th>Type</th><th>Altitude</th><th>Velocity</th><th>Heading</th><th>Has Pos</th></tr>');
  }
  });

// Prototype function to create the vehicle name for display
Aircraft.prototype.parseName = function() {
  let idStr='';
  // If we have a plane/flight ID
  if (this.idInfo) {idStr += this.idInfo + " ";}
  // And if we have a squawk code...
  if (this.aSquawk) {idStr += "(" + this.aSquawk + ") ";}
  // We should always have an ICAO address.
  idStr += "[" + this.addr.toUpperCase() + "]";
  return idStr;
};

// Prototype function to add an entry to the aircraft table
Aircraft.prototype.createTableEntry = function() {
  if (debug) {console.log('Creating new table entry for aircraft: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  $('#table-'+this.domName).children('tbody').append('<tr id="'+this.addr+'"><td>'+this.name+'</td><td>'+((this.category==null) ? '' : this.category)+'</td><td>'+((this.alt==null) ? '' : this.alt + ' ft')+'</td><td>'+((this.velo==null) ? '' : this.velo + ' mph')+'</td><td>'+((this.heading==null) ? '' : degreeToCardinal(this.heading))+'</td><td>'+hasPos+'</td></tr>');
};
// Prototype function to update an entry in the aircraft table
Aircraft.prototype.updateTableEntry = function() {
  if (debug) {console.log('Updating table entry for aircraft: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  $('#'+this.addr).html('<td>'+this.name+'</td><td>'+((this.category==null) ? '' : this.category)+'</td><td>'+((this.alt==null) ? '' : this.alt + ' ft')+'</td><td>'+((this.velo==null) ? '' : this.velo + ' mph')+'</td><td>'+((this.heading==null) ? '' : degreeToCardinal(this.heading))+'</td><td>'+hasPos+'</td>');
  };

//Aircraft.prototype.updateIcon = function() {};







/***************************************************
 * VEHICLE ICON FACTORY
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
    var debugStr = "";
    
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
      vehData[veh].info.setPosition(newPos);
    }
  }
}