"use strict";// overcome current Chrome and Firefox issues with ECMA6 stuff like classes
/***********************************************************
 * Airsuck JS custom vehicle for Ships
 * v. 0.1
 *
 * Licensed under GPL V3
 * https://github.com/ThreeSixes/airSuck
 * 
 * Vehicle creator, manipulation, and destruction functions
 *
 * Deps: jQuery
 **********************************************************/

// Register vehicle type
if(debug){console.log('Registering vehicle type: AIS');}
registerVehicleType('airAIS','AIS','fa-ship',function(msgJSON) {if (debug) {console.log('AIS Constructor called with message: ' + msgJSON);}return new Ship(msgJSON);},function(container) {$(container).append('<tr><th>ID</th><th>Type</th><th>Flag</th><th>Velocity</th><th>Destination</th><th>Has Pos</th></tr>');});

// AIS object extending Vehicle
class Ship extends Vehicle {
  constructor(msgJSON) {
    // create the generic vehicle object
    super(msgJSON,'AIS');
    // extend with AIS specific data
    $.extend(true, this, msgJSON);
    // add additional parameters
    this.domName = 'AIS';
    this.maxAge = 5 * (60 * 1000); // How long to retain a ship after losing contact (miliseconds)
    // gMap icon stuff
    this.dirIcoPath = "m 0,0 -20,50 40,0 -20,-50"; // Path we want to use for AIS targets that we have direction data for.
    this.dirIcoScale = 0.15; // Scale of the path.
    this.ndIcoPath = "m 0,0 -20,20 20,20 20,-20 -20,-20"; // Path we want to use for AIS targets that we don't have direction data for.
    this.ndIcoSacle = 0.21; // Scale of the path.
    this.vehColorActive = "#0000ff"; // Color of active ship icons (hex)
    this.vehColorInactive = "#000066"; // Color of nonresponsive ship icons (hex)
    // set the name string
    this.name = this.parseName();
    // create the table entry
    this.createTableEntry();
  }
}

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

// icon factory - overrides default to use courseOverGnd instead of heading where available
Ship.prototype.createIcon = function() {
   // If we have heading data for the vehicle
  if (this.courseOverGnd != 'undefined') {
    // Create our icon for a vehicle with heading data.
    var newIcon = new google.maps.Marker({
      path: this.dirIcoPath,
      scale: this.dirIcoScale,
      strokeWeight: 1.5,
      strokeColor: (this.active == true) ? this.vehColorActive : this.vehColorInactive,
      rotation: this.courseOverGnd
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
}
