"use strict";// overcome current Chrome and Firefox issues with ECMA6 stuff like classes
/***********************************************************
 * Airsuck JS custom vehicle for Aircraft
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
if(debug){console.log('Registering vehicle type: SSR');}
registerVehicleType('airSSR','SSR','fa-plane',function(msgJSON) {return new Aircraft(msgJSON);},function(container) {$(container).append('<tr><th>ID</th><th>Cat.</th><th>Flag</th><th>Altitude</th><th>Velocity</th><th>Heading</th><th>Pos</th></tr>');});

/***************************************************
 * SSR OBJECT DECLARATION
 **************************************************/
class Aircraft extends Vehicle {
  constructor(msgJSON) {
    // create the generic vehicle object
    super(msgJSON,'SSR');
    // extend with SSR specific data
    $.extend(true, this, msgJSON);
    // add additional parameters
    this.domName = 'SSR';
    this.maxAge = 2 * (60 * 1000); // How long to retain an aircraft after losing contact (miliseconds)
    // Icon variables
    this.dirIcoPath = "m 0,0 -20,50 20,-20 20,20 -20,-50"; // Path we want to use for ADS-B targets we have direction data for.
    this.dirIcoScale = 0.15; // Scale of the path.
    this.ndIcoPath = "m 15,15 a 15,15 0 1 1 -30,0 15,15 0 1 1 30,0 z"; // Path we want to sue for ADS-B targets we don't have direction data for.
    this.ndIcoSacle = 0.24; // Scale of the path.
    this.vehColorActive = "#ff0000"; // Color of active aircraft icons (hex)
    this.vehColorInactive = "#660000"; // Color of nonresponsive aircraft icons (hex)
    this.stkColor = "#FFFFFF"; // Color of the path
    // set the name string
    this.name = this.parseName();
    // create the table entry
    this.createTableEntry();
  }
}

/***************************************************
 * FUNCTION DETERMINES VEHICLE NAME
 * OVERRIDES DEFAULT TO USE COLOR RAMP
 **************************************************/
Aircraft.prototype.update = function(msgJSON){
  // update data in the object
  $.extend(true, this, msgJSON);
  // if not set to active, reactivate
  if (this.active == false) {this.active=true;}
  
  // set the path color if we have an altitude
  if (this.alt != 'undefined' && this.alt != null) {
    this.stkColor = "#" + polyRamp.colourAt(this.alt / 1000); // Color of the path
  }
  // update the last update parameter
  this.lastUpdate = Date.now();
  // update the vehicle entry in its' table
  this.updateTableEntry();
  // move the maps position
  this.movePosition();
};

/***************************************************
 * FUNCTION DETERMINES VEHICLE NAME
 **************************************************/
Aircraft.prototype.parseName = function() {
  let idStr='';
  // If we have a plane/flight ID
  if (this.idInfo) {
    // If we have 'default' or 'blank' idInfo field
    if (this.idInfo != "@@@@@@@@") {
      // Just blank the field.
      idStr += this.idInfo + " ";
    }
    
  }
  // And if we have a squawk code...
  if (this.aSquawk) {idStr += "(" + this.aSquawk + ") ";}
  // We should always have an ICAO address.
  idStr += "[" + this.addr.toUpperCase() + "]";
  return idStr;
};

/***************************************************
 * FUNCTION ADDS VEHICLE TO THE INFO TABLE
 **************************************************/
Aircraft.prototype.createTableEntry = function() {
  if (debug) {console.log('Creating new table entry for aircraft: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  $('#table-'+this.domName).children('tbody').append('<tr id="'+this.addr+'"><td>'+this.name+'</td><td>'+((this.category==null) ? '--' : this.category)+'</td><td>' +((this.icaoAACC==null) ? '--' : this.icaoAACC)+ '</td><td>'+((this.alt==null) ? '--' : this.alt + ' ft')+'</td><td>'+((this.velo==null) ? '--' : this.velo + ' mph')+'</td><td>'+((this.heading==null) ? '--' : degreeToCardinal(this.heading))+'</td><td>'+((hasPos) ? '*' : '--')+'</td></tr>');
};

/***************************************************
 * FUNCTION UPDATES VEHICLE IN THE INFO TABLE
 **************************************************/
Aircraft.prototype.updateTableEntry = function() {
  if (debug) {console.log('Updating table entry for aircraft: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  $('#'+this.addr).html('<td>'+this.parseName()+'</td><td>'+((this.category==null) ? '--' : this.category)+'</td><td>' +((this.icaoAACC==null) ? '--' : this.icaoAACC)+ '</td><td>'+((this.alt==null) ? '--' : this.alt + ' ft')+'</td><td>'+((this.velo==null) ? '--' : this.velo + ' kt')+'</td><td>'+((this.heading==null) ? '--' : degreeToCardinal(this.heading))+'</td><td>'+((hasPos) ? '*' : '--')+'</td>');
};
