"use strict";// overcome current Chrome and Firefox issues with ECMA6 stuff like classes
/***********************************************************
 * Airsuck JS custom vehicle for Ships
 * v. 0.1
 *
 * Licensed under GPL V3
 * https://github.com/ThreeSixes/airSuck
 * 
 * Ship class extends the default Vehicle class
 *
 * Deps: jQuery, vehicles.js
 **********************************************************/

// Register vehicle type
if(debug){console.log('Registering vehicle type: AIS');}
registerVehicleType('airAIS','AIS','fa-ship',function(msgJSON) {return new Ship(msgJSON);},function(container) {$(container).append('<tr><th>ID</th><th>Flag</th><th>Velocity</th><th>Course</th><th>Destination</th><th>Pos</th></tr>');});

/***************************************************
 * AIS OBJECT DECLARATION
 **************************************************/
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
    this.dirIcoScale = 0.15; // Scale of the icon.
    this.ndIcoPath = "m 0,0 -20,20 20,20 20,-20 -20,-20"; // Path we want to use for AIS targets that we don't have direction data for.
    this.ndIcoScale = 0.21; // Scale of the icon.
    this.vehColorActive = "#0000ff"; // Color of active ship icons (hex)
    this.vehColorInactive = "#000066"; // Color of nonresponsive ship icons (hex)
    this.stkColor = "#00ffff"; // Color of the path
    // set the name string
    this.name = this.parseName();
    // create the table entry
    this.createTableEntry();
  }
}

/***************************************************
 * FUNCTION DETERMINES VEHICLE NAME
 **************************************************/
Ship.prototype.parseName = function() {
  let idStr='';
  // If we have a vessel name
  if (this.vesselName) { if (this.vesselName !== undefined) {idStr += this.vesselName + " "; } }
  // If we have a valid IMO
  if (this.imo) { if (this.imo>0) { idStr += "(" + this.imo + ((this.imoCheck==false) ? "*" : "") + ") "; } }
  // We should always have an MMSI address.
  idStr += "[" + this.addr.toString() + "]";
  return idStr;
};

/***************************************************
 * FUNCTION ADDS VEHICLE TO THE INFO TABLE
 **************************************************/
Ship.prototype.createTableEntry = function() {
  if (debug) {console.log('Creating new table entry for ship: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  let colLength = $('#table-' + this.domName).find('th').length;//number of columns to span for the detail row
  //console.log('AIS table columns determined for: '+this.addr+' as this many columns: '+colLength);
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  $('#table-'+this.domName).children('tbody').append('\
    <tr id="'+this.addr+'-row-summary" class="vehicle-table-entry">\
      <td>'+((this.name==null) ? '--' : this.name)+'</td>\
      <td>'+((this.mmsiCC==null) ? '--' : this.mmsiCC)+'</td>\
      <td>'+((this.velo==null) ? '--' : this.velo + ' kt')+'</td>\
      <td>'+((this.courseOverGnd==null) ? '--' : degreeToCardinal(this.courseOverGnd))+'</td>\
      <td>'+((this.destination==null) ? '--' : this.destination)+'</td>\
      <td>'+((hasPos) ? '*' : '--')+'</td>\
    </tr>\
    <tr id="'+this.addr+'-row-detail" class="vehicle-table-detail">\
      <td colspan="'+colLength+'">\
        <table class="infoTable"><tbody>\
          <tr>\
            <td class="tblHeader">Velocity</td>\
            <td class="tblCell">' +((this.velo==null) ? '--' : this.velo+' kt')+'</td>\
            <td class="tblHeader">Flag</td>\
            <td class="tblCell">' +((this.mmsiCC==null) ? '--' : this.mmsiCC)+ '</td>\
          </tr>\
          <tr>\
            <td class="tblHeader">COG / Hdg</td>\
            <td class="tblCell">' +((this.courseOverGnd==null) ? '--' : this.courseOverGnd)+ ' / ' +((this.heading==null) ? '--' : this.heading+' deg')+ '</td>\
            <td class="tblHeader">Pos. type</td>\
            <td class="tblCell">' +((this.epfdMeta==null) ? '--' : this.epfdMeta)+ '</td>\
          </tr>\
          <tr>\
            <td class="tblHeader">Callsign</td>\
            <td class="tblCell">' +((this.callsign==null) ? '--' : this.callsign)+ '</td>\
            <td class="tblHeader">Draught</td>\
            <td class="tblCell">' +((this.draught==null) ? '--' : ((this.draught>0) ? this.draught.toString()+' m' : '--'))+ '</td>\
          </tr>\
          <tr>\
            <td class="tblHeader">Turn rate</td>\
            <td class="tblCell">' + '--' + '</td>\
            <td class="tblHeader">Dim.</td>\
            <td class="tblCell">' +((this.dimToBow>0 && this.dimToStern >0 && this.dimToPort >0 && this.dimToStarboard >0) ? (this.dimToPort+this.dimToStarboard)+ 'x' +(this.dimToBow+this.dimToStern)+' m' : '--')+ '</td>\
          </tr>\
          <tr>\
            <td class="tblHeader">Type</td>\
            <td class="tblCell">' + ((this.mmsiType==null) ? '--' : this.mmsiType) + '</td>\
            <td class="tblHeader"></td>\
            <td class="tblCell"></td>\
          </tr>\
          <tr>\
            <td class="tblHeader">Nav. Stat.</td>\
            <td class="tblCell" colspan=3>' + ((this.navStatMeta==null) ? '--' : this.navStatMeta) + '</td>\
          </tr>\
        </tbody></table>\
      </td>\
    </tr>\
  ');
  
  // set the row click function to display the row detail and highlight the ship
  $('#'+this.addr+'-row-summary').click(function(){
      if ($(this).next().css('display')=='none') {
        $(this).next().css('display','table-row');
      } else {
        $(this).next().css('display','none');
      }
      // swap the visibility
      //$(this).next().toggle();
    });
  
};

/***************************************************
 * FUNCTION UPDATES VEHICLE IN THE INFO TABLE
 **************************************************/
Ship.prototype.updateTableEntry = function() {
  if (debug) {console.log('Updating table entry for ship: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  $('#'+this.addr+'-row-summary').html('\
    <td>'+this.name+'</td>\
    <td>'+((this.mmsiCC==null) ? '--' : this.mmsiCC)+'</td>\
    <td>'+((this.velo==null) ? '--' : this.velo + ' kt')+'</td>\
    <td>'+((this.courseOverGnd==null) ? '--' : degreeToCardinal(this.courseOverGnd))+'</td>\
    <td>'+((this.destination==null) ? '--' : this.destination)+'</td>\
    <td>'+((hasPos) ? '*' : '--')+'</td>');
};

/***************************************************
 * FUNCTION SETS THE VEHICLE ICON
 * OVERRIDES DEFAULT TO USE courseOverGnd
 **************************************************/
Ship.prototype.setIcon = function() {
   // If we have heading data for the vehicle
  if (this.courseOverGnd != null) {
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
