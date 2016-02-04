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
 * VEHICLE EXPIRATION LOOP
 **************************************************/
// Expire vehicles.
function expireVehicles() {
  if(debug=='all'){console.log("Expiration check running");}
  let key;
  for (key in vehicles) {
    // Get the state of the vehicle and take appropriate action
    // Don't run the check on nulled objects because JS ECMAScript 6 doesn't allow delete...
    if (vehicles[key]!=null) {
      switch (vehicles[key].checkExpiration()) {
          case 'Halflife':
            if(debug=='all') {console.log('Halflife determined for vehicle: '+vehicles[key].parseName());}
            vehicles[key].setHalflife();
            break;
          case 'Expired':
            if(debug=='all') {console.log('Expiration determined for vehicle: '+vehicles[key].parseName());}
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
}

/***************************************************
 * CLICK LISTENERS
 **************************************************/

function vehicleMarkerRightClickListener(vehName) {
  // Listener called from messages.js for access to vehicles array
  // Check to see if the path is visible and reverse the visiblity
  if (vehicles[vehName].pathPoly.getVisible() == true) {
    vehicles[vehName].pathPoly.setVisible(false);
  } else {
    vehicles[vehName].pathPoly.setVisible(true);
  }
}

function vehicleMarkerClickListener(vehName) {
  // Listener called from messages.js for access to vehicles array
  
  // Info window functions, check if open and toggle
  if (vehicles[vehName].info.shown) {
    // Close it.
    vehicles[vehName].info.close();
    vehicles[vehName].info.setContent("");
    vehicles[vehName].info.shown = false;
    // Hide the sidebar details
    $('#'+vehicles[vehName].addr+'-row-detail').toggle();
  } else {
    // Set data in case we don't have it, open it, and flag it as open.
    vehicles[vehName].info.setContent(vehicles[vehName].setInfoWindow());
    vehicles[vehName].info.open(map, vehicles[vehName].marker);
    vehicles[vehName].info.shown = true;
    // Show the sidebar details
    $('#'+vehicles[vehName].addr+'-row-detail').toggle();
  }
}

function vehicleTableRowClickListener(vehName) {
    // check the string for validity
    if (vehName == 'undefined') {
        if(debug=='all'){console.log('Error: ID passed to vehicleTableRowClickListener is invalid.');}
        return false;
    } else if (vehName.substring(0,2) != 'veh') {
        vehName = 'veh'+vehName;//missing veh at the beginning, add
    }
    if(debug=='all'){console.log('Changing marker for: '+vehName);}
    vehicles[vehName].setMarkerSelected();
}

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
      if(debug=='all'){console.log('degreeToBearing: error in calculating bearing');}
      return null;
      break;
  }
};

/***************************************************
 * VEHICLE PROTOTYPE
 **************************************************/

class Vehicle {
  constructor(msgJSON,protocol){
    if(debug=='all'){console.log('Vehicle constructor executed for vehicle: ' + msgJSON.addr + ', Using protocol: ' + protocol);}
    this.addr = msgJSON.addr;
    this.protocol = protocol;// communications protocol used (AIS,SSR)
    this.lastPos = "none";
    this.lastUpdate = new Date().getTime();
    this.active = true;// set true if the vehicle is currently active
    this.selected = false;// records whether the vehicle has been selected in the sidebar or by clicking the icon
    this.maxAge = 1000;// default vehicle expiration time in milliseconds since last contact
    this.marker = new google.maps.Marker();// blank marker object to hold graphics data and later the marker object
    // gMap icon stuff
    this.marker.active = true;// set true if the vehicle is currently active
    this.marker.selected = false;// records whether the vehicle has been selected in the sidebar or by clicking the icon
    this.marker.dirIcoPath = "m 0,0 -20,50 20,-20 20,20 -20,-50"; // Path we want to use for ADS-B targets we have direction data for.
    this.marker.dirIcoScale = 0.15; // Current scale of the path
    this.marker.dirIcoDefaultScale = 0.15; // Default scale of the path
    this.marker.ndIcoPath = "m 15,15 a 15,15 0 1 1 -30,0 15,15 0 1 1 30,0 z"; // Path we want to sue for ADS-B targets we don't have direction data for.
    this.marker.ndIcoScale = 0.24; // Current scale of the path.
    this.marker.ndIcoDefaultScale = 0.24; // Default scale of the path.
    this.marker.vehColorActive = "#ff0000"; // Color of active vehicle icons (hex)
    this.marker.vehColorInactive = "#660000"; // Color of nonresponsive vehicle icons (hex)
    this.marker.vehColorSelected = "#00ffff"; // Color of the vehicle icon when selected
    this.marker.$super = this;// reference to access the parent vehicle from marker event listeners
    // infoWindow stuff
    this.info = new google.maps.InfoWindow(); // Placeholder for the google maps info window
    this.info.$super = this;// reference to access the parent vehicle from marker event listeners
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
Vehicle.prototype.setIcon = function() {
  let newIcon;
  // If we have heading data for the vehicle
  if (this.heading != 'undefined') {
    // create a GMaps symbol icon
    newIcon = {
      path:this.marker.dirIcoPath,
      scale:this.marker.dirIcoScale,
      strokeWeight: 1.5,
      rotation: this.heading,
      strokeColor:(this.marker.selected == true) ? this.marker.vehColorSelected : ((this.marker.active == true) ? this.marker.vehColorActive : this.marker.vehColorInactive)
    };
    
  } else {
    // create a GMaps symbol icon with no rotation / heading data
    newIcon = {
      path:this.marker.ndIcoPath,
      scale:this.marker.ndIcoScale,
      strokeWeight: 1.5,
      strokeColor:(this.marker.selected == true) ? this.marker.vehColorSelected : ((this.marker.active == true) ? this.marker.vehColorActive : this.marekr.vehColorInactive)
    };
  }
  // And return it.
  return newIcon;
};

/***************************************************
 * FUNCTION ADDS A GMAPS MARKER TO THE VEHICLE
 **************************************************/
Vehicle.prototype.setMarker = function() {
  // Set marker map aspects, retain existing data in the marker
  this.marker.setPosition(new google.maps.LatLng(this.lat, this.lon));
  this.marker.setIcon(this.setIcon());
  //this.marker.rotation=this.heading;
  this.marker.setMap(map);
  this.marker.vehName = this.addr;
  
  // Create our info window
  this.setInfoWindow();
  
  // Trying listener again
  this.marker.addListener('mouseover',function(){
    // mouse over marker, use selected color
    this.$super.setMarkerHover();
    this.$super.movePosition();
    // select the table entry
    $('#'+this.$super.addr+'-row-summary').addClass('selected');
  });
  this.marker.addListener('mouseout',function(){
    // mouse exiting marker, unselect marker
    // need pre-check for being selected in sidebar
    this.$super.setMarkerUnselected();
    this.$super.movePosition();
    // deselect the table entry
    $('#'+this.$super.addr+'-row-summary').removeClass('selected');
  });
  
}

/***************************************************
 * FUNCTION CREATES VEHICLE ICONS FOR GMAPS
 * SPECIFICALLY ENLARGES THE ICON WHEN SELECTED
 **************************************************/
Vehicle.prototype.setMarkerSelected = function() {
  // set the selected flag
  this.marker.selected = true;
  // enlarge the icon
  this.marker.dirIcoScale = this.marker.dirIcoScale*1.5;
  this.marker.ndIcoScale = this.marker.ndIcoScale*1.5;
  
  // use the move function to update the icon
  this.movePosition();
}
Vehicle.prototype.setMarkerHover = function() {
  // set the selected flag
  this.marker.selected = true;
  // use the move function to update the icon
  this.movePosition();
}
Vehicle.prototype.setMarkerUnselected = function() {
  // set the selected flag
  this.marker.selected = false;
  // shrink the icon
  this.marker.dirIcoScale = this.marker.dirIcoDefaultScale;
  this.marker.ndIcoScale = this.marker.ndIcoDefaultScale;

  // use the move function to update the icon
  this.movePosition();
}

/***************************************************
 * FUNCTION MOVES THE VEHICLE MARKER AND INFO POSITIONS
 **************************************************/
Vehicle.prototype.movePosition = function() {
    if(debug=='all'){
      console.log('...movePosition called...');
    }
    
    // Figure out where we are in 2D space
    let thisPos = this.lat + "," + this.lon;
    
    // Update the path object with the new position
    // copy the path object
    let pathObject = this.pathPoly.getPath();
    // update with the new path
    pathObject.push(new google.maps.LatLng(this.lat, this.lon));
    // push back to the polyline
    this.pathPoly.setPath(pathObject);
    // set the polyline color
    this.pathPoly.setOptions({strokeColor: this.stkColor});
    
    // Update the marker
    // Modify the icon to have the correct rotation, and to indicate there is bearing data.
    this.marker.setIcon(this.setIcon());
    // Update the infowindow
    this.setInfoWindow();
    // Move the marker.
    this.marker.setPosition(new google.maps.LatLng(this.lat, this.lon));
    
    // Record the new position for testing on next update
    this.lastPos = thisPos;
};

/***************************************************
 * FUNCTION ADDS A GMAPS INFO WINDOW TO THE VEHICLE
 **************************************************/
Vehicle.prototype.setInfoWindow = function() {  
  // Set info window properties
  this.info.setPosition(new google.maps.LatLng(this.lat, this.lon));
  this.info.setContent(this.parseName());
  
  // Add listener to set infowindow content
  google.maps.event.addListener(this.marker, "click", function()
  {
    if(debug=='dev'){
      console.log('Setting InfoWindow data for: '+this.$super.addr);
    }
    this.$super.info.setContent(this.$super.parseName());
  });
  // Add listener to close the info window
  google.maps.event.addListener(this.info, "closeclick", function()
  {
    if(debug=='dev'){
      console.log('InfoWindow closed for: '+this.$super.addr);
    }
    $('#'+this.$super.addr+'-row-detail').css('display','none');
  });
  
};

/***************************************************
 * FUNCTIONS UPDATE THE VEHICLE INFO AND TABLE ENTRY
 * updateTableEntry function to be overridden by
 * custom vehicle types
 **************************************************/
Vehicle.prototype.updateTableEntry = function(){
  if(debug=='all'){console.log('Error: Function updateTableEntry not set for protocol: '+this.protocol);}
  return;
};

Vehicle.prototype.update = function(msgJSON){
  // update data in the object
  $.extend(true, this, msgJSON);
  // if not set to active, reactivate
  if (this.marker.active == false) {this.marker.active=true;}
  // update the last update parameter
  this.lastUpdate = Date.now();
  // update the vehicle entry in its' table
  this.updateTableEntry();
  // move the maps position
  this.movePosition();
};

/***************************************************
 * SUPPORT ZERO-FILLING NUMBERS. THIS CAN OR SHOULD
 * BE MOVED EVENTUALLY TO A BETTER PLACE.
 **************************************************/
Vehicle.prototype.zerofill = function(number, numberOfDigits){
  // Set return value.
  var retVal = number.toString();
  // Figure out the length of the number in digits.
  var numLen = retVal.length;
  
  // Figure out the minimum size of the number.
  if (numLen < numberOfDigits) {
    // Add zeros.
    for (var i = 0;  i < (numberOfDigits - numLen); i++) {
      // Prepend a string zero.
      retVal = "0" + retVal;
    }
  }
  
  return retVal;
};

/***************************************************
 * VEHICLE DESTRUCTOR
 **************************************************/
Vehicle.prototype.destroy = function(){
  if(debug=='all'){console.log('Destroying vehicle: ' + this.parseName());}
  
  // Remove table entries
  $('#'+this.addr+'-row-summary').remove();
  $('#'+this.addr+'-row-detail').remove();
  
  // Default destructor processes
  if(this.info != null){this.info.close();}// close the gMap info window
  this.pathPoly.setMap(null);// turn off the path
  this.marker.setMap(null);// remove the icon from the map
  //vehicles[this.addr] = null;// invalidate this object, can't fully delete since its gone in ECMAScript 6...
};

/***************************************************
 * FUNCTION SETS THE ICON TO HALFLIFE, SETS INACTIVE
 **************************************************/
Vehicle.prototype.setHalflife = function(){
  // Deactivate vehicle and change the icon for it.
  this.marker.active = false;
  if(this.marker!=null){this.marker.setIcon(this.setIcon());}
};

/***************************************************
 * FUNCTION DETERMINES IF A VEHICLE SHOULD BE
 * SET TO HALFLIFE, EXPIRED, OR REMAIN ACTIVE
 **************************************************/
Vehicle.prototype.checkExpiration = function(){
  // Compute the time delta
  let vehDelta = Date.now() - this.lastUpdate;
  // Return Active, Halflife, or Expired
  if (vehDelta >= this.maxAge) {
    return('Expired');
  } else if ((vehDelta >= (this.maxAge/2)) && (this.marker.active == true)) {
    return('Halflife');
  } else {
    return('Active');
  }
};

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
