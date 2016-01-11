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
  // update data in the object **do this first**
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
 * TO DO: separate the table info population function
 * so we don't duplicate with the update function
 **************************************************/
Aircraft.prototype.createTableEntry = function() {
  if (debug) {console.log('Creating new table entry for aircraft: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  let colLength = $('#table-' + this.domName).find('th').length;//number of columns to span for the detail row
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  
  // Handle mode A stuff out-of-band.
  if (this.aSquawkMeta != null) {
    var aSquawkMetaStr = '<tr>\
          <td class="tblHeader">Squawk meta</td>\
          <td class="tblCell" colspan=3>'+this.aSquawkMeta+'</td>\
        </tr>';
  }
  
  $('#table-'+this.domName).children('tbody').append('\
    <tr id="'+this.addr+'-row-summary" class="vehicle-table-entry">\
      <td>'+this.name+'</td>\
      <td>'+((this.category==null) ? '--' : this.category)+'</td>\
      <td>' +((this.icaoAACC==null) ? '--' : this.icaoAACC)+ '</td>\
      <td>'+((this.alt==null) ? '--' : this.alt + ' ft')+'</td>\
      <td>'+((this.velo==null) ? '--' : this.velo + ' mph')+'</td>\
      <td>'+((this.heading==null) ? '--' : degreeToCardinal(this.heading))+'</td>\
      <td>'+((hasPos) ? '*' : '--')+'</td>\
    </tr>\
    <tr id="'+this.addr+'-row-detail" class="vehicle-table-detail">\
      <td colspan="'+colLength+'">\
        <table class="infoTable"><tbody>\
           <tr>\
        <td class="tblHeader">Air/Gnd</td>\
        <td class="tblCell">' +((this.vertStat==null) ? '--' : this.vertStat)+ '</td>\
        <td class="tblHeader">Flight status</td>\
        <td class="tblCell">' +((this.fs==null) ? '--' : this.fs)+ '</td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Velocity</td>\
        <td class="tblCell">' +((this.velo==null) ? '--' : this.velo+' kt')+ '</td>\
        <td class="tblHeader">Heading</td>\
        <td class="tblCell">' +((this.heading==null) ? '--' : this.heading+' deg')+ '</td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Altitude</td>\
        <td class="tblCell">' +((this.alt==null) ? '--' : this.alt+' ft')+ '</td>\
        <td class="tblHeader">Climb rate</td>\
        <td class="tblCell">' +((this.vertRate==null) ? '--' : (this.vertRate>0) ? '+'+this.vertRate+' ft/min' : this.vertRate+' ft/min')+ '</td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Position</td>\
        <td colspan=3 class="tblCell">' +((this.lat==null) ? '--' : this.lat.toFixed(7) + ', ' + this.lon.toFixed(7))+ '</td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Supersonic</td>\
        <td class="tblCell">' +((typeof this.supersonic==="undefined") ? '--' : ((this.supersonic===true) ? 'Yes' : 'No'))+ '</td>\
        <td class="tblHeader"></td>\
        <td class="tblCell"></td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Data src.</td>\
        <td class="tblCell" colspan=3>' +this.lastClientName+ ' -&gt; ' +this.lastSrc+ '</td>\
      </tr>\
      '+((aSquawkMetaStr==null) ? '' : aSquawkMetaStr)+'\
        </tbody></table>\
      </td>\
    </tr>'
  );
  
  // set the row click function to display the row detail and highlight the plane
  $('#'+this.addr+'-row-summary').click(function(){
    /* bugs known:
     * 1) clicking the icon and the table row can get out of sync, this has to do
     * with the lack of access to the vehicles array in the listener function. The
     * array has a flag set for .info.shown which would solve for this bug, but alas
     * no access in this listener function...
     * 
     */

    if ($(this).next().css('display')=='none') {
      // details aren't shown, change the plane's icon color & size
      /* Not yet working - issue in the listener and access to the vehicles array
      // get vehicle name from the row ID
      let vehName = this.id.substring(0,this.id.length-12);
      // call the click listener
      vehicleTableRowClickListener(vehName);
      */
      $(this).next().css('display','table-row'); 
    } else {
      // details are shown, return the plane's icon color & size to normal
      // to do once the issue above is resolved
      $(this).next().css('display','none');
    }
  });
  
};

/***************************************************
 * FUNCTION UPDATES VEHICLE IN THE INFO TABLE
 **************************************************/
Aircraft.prototype.updateTableEntry = function() {
  if (debug) {console.log('Updating table entry for aircraft: '+this.addr+' in table: #table-' + this.domName);}
  let hasPos;
  if (this.lat) {hasPos=true;}else{hasPos=false;}
  // update the summary
  $('#'+this.addr+'-row-summary').html('\
    <td>'+this.parseName()+'</td>\
    <td>'+((this.category==null) ? '--' : this.category)+'</td>\
    <td>' +((this.icaoAACC==null) ? '--' : this.icaoAACC)+ '</td>\
    <td>'+((this.alt==null) ? '--' : this.alt + ' ft')+'</td>\
    <td>'+((this.velo==null) ? '--' : this.velo + ' kt')+'</td>\
    <td>'+((this.heading==null) ? '--' : degreeToCardinal(this.heading))+'</td>\
    <td>'+((hasPos) ? '*' : '--')+'</td>');
  
  // Handle mode A stuff out-of-band.
  if (this.aSquawkMeta != null) {
    var aSquawkMetaStr = '<tr>\
          <td class="tblHeader">Squawk meta</td>\
          <td class="tblCell" colspan=3>'+this.aSquawkMeta+'</td>\
        </tr>';
  }
  
  // update the detail table
  $('#'+this.addr+'-row-detail').find('.infoTable').html('\
      <tr>\
        <td class="tblHeader">Air/Gnd</td>\
        <td class="tblCell">' +((this.vertStat==null) ? '--' : this.vertStat)+ '</td>\
        <td class="tblHeader">Flight status</td>\
        <td class="tblCell">' +((this.fs==null) ? '--' : this.fs)+ '</td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Velocity</td>\
        <td class="tblCell">' +((this.velo==null) ? '--' : this.velo+' kt')+ '</td>\
        <td class="tblHeader">Heading</td>\
        <td class="tblCell">' +((this.heading==null) ? '--' : this.heading+' deg')+ '</td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Altitude</td>\
        <td class="tblCell">' +((this.alt==null) ? '--' : this.alt+' ft')+ '</td>\
        <td class="tblHeader">Climb rate</td>\
        <td class="tblCell">' +((this.vertRate==null) ? '--' : (this.vertRate>0) ? '+'+this.vertRate+' ft/min' : this.vertRate+' ft/min')+ '</td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Position</td>\
        <td colspan=3 class="tblCell">' +((this.lat==null) ? '--' : this.lat.toFixed(7) + ', ' + this.lon.toFixed(7))+ '</td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Supersonic</td>\
        <td class="tblCell">' +((this.supersonic==null) ? '--' : ((this.supersonic===true) ? 'Yes' : 'No'))+ '</td>\
        <td class="tblHeader"></td>\
        <td class="tblCell"></td>\
      </tr>\
      <tr>\
        <td class="tblHeader">Data src.</td>\
        <td class="tblCell" colspan=3>' +this.lastClientName+ ' -&gt; ' +this.lastSrc+ '</td>\
      </tr>'+((aSquawkMetaStr==null) ? '' : aSquawkMetaStr));
};
