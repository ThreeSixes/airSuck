///////////////////////////
// Vehicle type settings //
///////////////////////////

// Ships
var dirShip = "m 0,0 -20,50 40,0 -20,-50"
var dirShipScl = 0.15
var ndShip = "m 0,0 -20,20 20,20 20,-20 -20,-20"
var ndShipScl = 0.21
var shipActive = "#0000ff"
var shipInactive = "#000066"
var shipAge = 5 * (60 * 1000);

// Aircraft
var dirAircraft = "m 0,0 -20,50 20,-20 20,20 -20,-50"
var dirAircraftScl = 0.15
var ndAircraft = "m 15,15 a 15,15 0 1 1 -30,0 15,15 0 1 1 30,0 z"
var ndAircraftScl = 0.24
var aircraftActive = "#ff0000"
var aircraftInactive = "#660000"
var aircraftAge = 2 * (60 * 1000);

/////////////////////////
// Main execution body //
/////////////////////////

// Instanciate Socket.IO
var socket = io();

// Instanciate RainbowVis and set global color ramp by plane height
var polyRamp = new Rainbow();
polyRamp.setNumberRange(0,45);
polyRamp.setSpectrum('aqua', 'yellow', 'fuchsia', 'red');

// Global Google Maps objects are global. :)
var map = null;
var mapLoaded = false;

// Create a generic array to hold our vehicle data.
var vehData = {};

// Find the debugger box.
var debugBox = document.getElementById("debugBx");

// Find the target message box
var msgBox = document.getElementById("message");

// How often we should check for expired vehicles in seconds.
var vehExpireCheckInterval = 1 * 1000;

// Initialize the Google map.
function initMap() {
 console.log("Maps loading...");
  
  // Set up the map object.
  map = new google.maps.Map(document.getElementById('map'), {
    zoom: 9,
    center: {lat: 45.555080, lng: -122.115890},
    mapTypeControlOptions: {
      style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
      mapTypeIds: [google.maps.MapTypeId.TERRAIN, google.maps.MapTypeId.SATELLITE]
      },
    mapTypeControl: false
  });
  
  // Set default map to terrain.
  map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
  
  // Create the monochrome map style
  var monoStyle = [
    {
      "featureType": "landscape.man_made",
      "elementType": "geometry",
      "stylers": [
        { "color": "#808080" },
        { "lightness": 35 }
      ]
    },{
      "featureType": "landscape.natural",
      "elementType": "geometry",
      "stylers": [
        { "color": "#808080" },
        { "lightness": 58 }
      ]
    },{
      "featureType": "poi.park",
      "stylers": [
        { "visibility": "off" }
      ]
    },{
      "featureType": "water",
      "elementType": "geometry",
      "stylers": [
        { "color": "#444444" }
      ]
    },{
      "featureType": "water",
      "elementType": "labels",
      "stylers": [
        { "color": "#e0e0e0" }
      ]
    },{
      "featureType": "road.local",
      "elementType": "geometry",
      "stylers": [
        { "color": "#ffffff" }
      ]
    },{
      "featureType": "road.arterial",
      "elementType": "geometry",
      "stylers": [
        { "color": "#ffffff" }
      ]
    },{
      "featureType": "road.highway",
      "elementType": "geometry",
      "stylers": [
        { "color": "#ffffff" }
      ]
    },{
      "featureType": "road.highway",
      "elementType": "labels",
      "stylers": [
        { "visibility": "off" }
      ]
    },{
      "featureType": "road.arterial",
      "elementType": "labels",
      "stylers": [
        { "visibility": "off" }
      ]
    },{
      "featureType": "poi",
      "elementType": "geometry",
      "stylers": [
        { "color": "#808080" },
        { "lightness": 22 }
      ]
    }
  ];
 
  // Create the map style control div to override the default google maps control
  // DOM elements must be set as JS vars to pass through google maps functions
  // Set up the main style control container
  var styleControlContainer = document.createElement('div');
  styleControlContainer.id = 'mapStyleBox';
  styleControlContainer.className = 'mapControlStyle';
  styleControlContainer.index = 1000;
  
  // Create a select box container
  var styleSelectBox = document.createElement('select');
  styleSelectBox.className = 'mapStyleSelector';
  
  // Set up the map style options
  var terrainMap = document.createElement('option');
  terrainMap.className = 'mapStyleSelector';
  terrainMap.value = 'Terrain';
  terrainMap.innerHTML = 'Terrain';
  var satelliteMap = document.createElement('option');
  satelliteMap.className = 'mapStyleSelector';
  satelliteMap.value = 'Satellite';
  satelliteMap.innerHTML = 'Satellite';
  var monoMap = document.createElement('option');
  monoMap.className = 'mapStyleSelector';
  monoMap.value = 'Monochrome';
  monoMap.innerHTML = 'Monochrome';
  
  // Add the style options to the main style control container
  styleControlContainer.appendChild(styleSelectBox);
  styleSelectBox.appendChild(terrainMap);
  styleSelectBox.appendChild(satelliteMap);
  styleSelectBox.appendChild(monoMap);
  
  // Add a listener to change the map type via the select box
  styleSelectBox.addEventListener('change',function(e){
      switch (this.value) {
        case "Terrain":
          // load the terrain map and clear any style overrides
          map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
          map.set('styles',null);
          break;
        case "Satellite":
          // load the satellite map and clear any style overrides
          map.setMapTypeId(google.maps.MapTypeId.SATELLITE);
          map.set('styles',null);
          break;
        case "Monochrome":
          // load the terrain map and add a custom style
          map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
          map.set('styles',monoStyle);
          break;
        default:
          map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
          map.set('styles',null);
      }
    });
  
  // Load the custom controls through the map controls interface
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(styleControlContainer);
  
  // Set default map to monochrome.
  map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
  map.set('styles',monoStyle);
  // Set the selectbox to monochrome
  styleSelectBox.options[2].selected = true;
  
  // The map loaded.
  mapLoaded = true;
}

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


// Create info windows for vehicles.
function infoFactory(vehName) {
  var retVal = null;
  
  // Which position type do we have?
  // ADS-B/SSR
  if (vehData[vehName].type == "airSSR") {
    // Build an aircraft identity string.
    var idStr = "";
    var catStr = "--";
    var fsStr = "-";
    var altStr = "--";
    var vertRateStr = "--";
    var vrSign = "";
    var veloStr = "--";
    var headingStr = "--";
    var vertStatStr = "--";
    var posStr = "";
    var supersonicStr = "--";
    
    // If we have a plane/flight ID
    if ("idInfo" in vehData[vehName]) {
      idStr += vehData[vehName].idInfo + " ";
    }
    
    // And if we have a squawk code...
    if ("aSquawk" in vehData[vehName]) {
      idStr += "(" + vehData[vehName].aSquawk + ") ";
    }
    
    // We should always have an ICAO address.
    idStr += "[" + vehData[vehName].addr.toUpperCase() + "]";
    
    // If we have flight status data...
    if ("fs" in vehData[vehName]) {
      fsStr = vehData[vehName].fs;
    }
    
    // If we have category data...
    if ("category" in vehData[vehName]) {
      catStr = vehData[vehName].category;
    }
    
    // If we have altitude data...
    if ("alt" in vehData[vehName]) {
      altStr = vehData[vehName].alt;
    }
    
    // If we have vertical rate data...
    if ("vertRate" in vehData[vehName]) {
      if (vehData[vehName].vertRate > 0) {
        vrSign = "+";
      }
      vertRateStr = vrSign + vehData[vehName].vertRate;
    }
    
    // If we have velocity data...
    if ("velo" in vehData[vehName]) {
      veloStr = vehData[vehName].velo;
    }
    
    // If we have vertical status data...
    if ("vertStat" in vehData[vehName]) {
      vertStatStr = vehData[vehName].vertStat;
    }
    
    // If we have heading data...
    if ("heading" in vehData[vehName]) {
      headingStr = vehData[vehName].heading;
    }
    
    // If we have position data...
    if ("lat" in vehData[vehName]) {
      posStr = vehData[vehName].lat.toFixed(7) + ", " + vehData[vehName].lon.toFixed(7);
    }
    
    // If we have supersonic data...
    if ("supersonic" in vehData[vehName]) {
      if (vehData[vehName].supersonic == 0) {
        supersonicStr = "No";
      } else if (vehData[vehName].supersonic == 1) {
        supersonicStr = "Yes";
      }
    }
    
    // Build our table.
    retVal = "<table class=\"infoTable\">";
    retVal += "<tr><td colspan=4 class=\"vehInfoHeader\">" + idStr + "</td></td></tr>";
    retVal += "<tr><td class=\"tblHeader\">Category</td><td class=\"tblCell\">" + catStr + "</td><td class=\"tblHeader\">Flight status</td><td class=\"tblCell\">" + fsStr + "</td></tr>";
    retVal += "<tr><td class=\"tblHeader\">Velocity</td><td class=\"tblCell\">" + veloStr + " kt</td><td class=\"tblHeader\">Heading</td><td class=\"tblCell\">" + headingStr + " deg</td></tr>";
    retVal += "<tr><td class=\"tblHeader\">Altitude</td><td class=\"tblCell\">" + altStr + " ft</td><td class=\"tblHeader\">Climb rate</td><td class=\"tblCell\">" + vertRateStr + " ft/min</td></tr>";
    retVal += "<tr><td class=\"tblHeader\">Position</td><td colspan=3 class=\"tblCell\">" + posStr + "</td></tr>";
    retVal += "<tr><td class=\"tblHeader\">Air/Gnd</td><td class=\"tblCell\">" + vertStatStr + "</td><td class=\"tblHeader\">Supersonic</td><td class=\"tblCell\">" + supersonicStr + "</td></tr>";
    
    // If we have some sort of emergency...
    if ('emergency' in vehData[vehName]) {
      if ((vehData[vehName].emergency == true) && ("emergencyData" in vehData[vehName])) {
        retVal += "<tr><td class=\"tblEmerg\" colspan=4>** EMERGENCY **</td></tr>";
        retVal += "<td class=\"tblEmerg\" colspan=4>Description - " + vehData[vehName].emergencyData + "</td></tr>";
      }
    }
    
    // If we have Mode A metadata...
    if ("aSquawkMeta" in vehData[vehName]) {
      retVal += "<tr><td class=\"tblHeader\" colspan=4>Metadata</td></tr>";
      retVal += "<td class=\"tblCell\" colspan=4>Mode A - " + vehData[vehName].aSquawkMeta + "</td></tr>";
    }
    
    retVal += "</table>";
  }
  
  // AIS
  else if (vehData[vehName].type == "airAIS") {
    // Build a ship identity string.
    var idStr = "";
    var veloStr = "--";
    var headingStr = "--";
    var courseOverGndStr = "--";
    var navStatStr = "--";
    var callsignStr = "--";
    var draughtStr = "--";
    var etaStr = "--";
    var shipTypeStr = "--";
    var epfdMetaStr = "--";
    var dimStr = "--";
    
    // If we have the vessel name...
    if ("vesselName" in vehData[vehName]) {
      idStr += vehData[vehName].vesselName + " ";
    }
    
    // If we have the vessel name...
    if ("imo" in vehData[vehName]) {
      if (vehData[vehName].imo > 0) {
        idStr += "(" + vehData[vehName].imo + ") ";
      }
    }
    
    // We should always have an MMSI address.
    idStr += "[" + vehData[vehName].addr.toString() + "]";
    
    // If we have velocity data...
    if ("velo" in vehData[vehName]) {
      veloStr = vehData[vehName].velo;
    }
    
    // If we have heading data...
    if ("heading" in vehData[vehName]) {
      if (vehData[vehName].heading != 511) {
        headingStr = vehData[vehName].heading;
      }
    }
    
    // If we have course over ground data...
    if ("courseOverGnd" in vehData[vehName]) {
      cogStr = vehData[vehName].courseOverGnd;
    }
    
    // If we have navigation status data...
    if ("navStat" in vehData[vehName]) {
      if (vehData[vehName].navStat < 15) {
        navStatStr = vehData[vehName].navStat;
        
        // If we have navigation stuatus metadata...
        if ("navStatMeta" in vehData[vehName]) {
          navStatStr = vehData[vehName].navStatMeta + " (" + navStatStr + ")";
        }
      }
    }
    
    // If we have navigation status data...
    if ("callsign" in vehData[vehName]) {
      if (vehData[vehName].callsign != "") {
        callsignStr = vehData[vehName].callsign;
      }
    }
    
    // If we have draught data.
    if ("draught" in vehData[vehName]) {
      draughtStr = vehData[vehName].draught.toString()
    }
    
    // If we have EPFD metadata...
    if ("epfdMeta" in vehData[vehName]) {
      epfdMetaStr = vehData[vehName].epfdMeta;
    }
    
    // If we have position data...
    if ("lat" in vehData[vehName]) {
      posStr = vehData[vehName].lat + ", " + vehData[vehName].lon;
    }
    
    // Figure out our dimensions.
    //if ("dimToBow" in vehData[vehName]) {
    //  shipLen = parseInt(vehData[vehName].dimToBow) + parseInt(vehData[vehName].dimToStern)
    //  shipWidth = parseInt(vehData[vehName].dimToStarboard) + parseInt(vehData[vehName].dimToPort)
    //  dimStr = shipLen.toString() + "x" + shipWidth.toString();
    //}
    
    // Build our table.
    retVal = "<table class=\"infoTable\">";
    retVal += "<tr><td colspan=4 class=\"vehInfoHeader\">" + idStr + "</td></td></tr>";
    retVal += "<tr><td class=\"tblHeader\">Velocity</td><td class=\"tblCell\">" + veloStr + " kt</td><td class=\"tblHeader\">Heading</td><td class=\"tblCell\">" + headingStr + " deg</td></tr>";
    retVal += "<tr><td class=\"tblHeader\">COG</td><td class=\"tblCell\">" + cogStr + " deg</td><td class=\"tblHeader\">Draught</td><td class=\"tblCell\">" + draughtStr + " m</td></tr>";
    retVal += "<tr><td class=\"tblHeader\">Callsign</td><td class=\"tblCell\">" + callsignStr + "</td><td class=\"tblHeader\">Position type</td><td class=\"tblCell\">" + epfdMetaStr + "</td></tr>";
    retVal += "<tr><td class=\"tblHeader\">Position</td><td colspan=3 class=\"tblCell\">" + posStr + "</td></tr>";
    retVal += "<td class=\"tblHeader\">NavStat</td><td colspan=3 class=\"tblCell\">" + navStatStr + "</td></tr>";
    
    // If we have ship type data...
    if ('shipTypeMeta' in vehData[vehName]) {
      if (vehData[vehName].shipTypeMeta != "") {
        retVal += "<td class=\"tblHeader\">Ship type</td><td colspan=3 class=\"tblCell\">" + vehData[vehName].shipTypeMeta + "</td></tr>";
      }
    }
    
    // If we have destination data...
    if ('destination' in vehData[vehName]) {
      if (vehData[vehName].destination != "") {
        retVal += "<td class=\"tblHeader\">Destination</td><td colspan=3 class=\"tblCell\">" + vehData[vehName].destination + "</td></tr>";
      }
    }
    
    // If we have some sort of emergency...
    if ('emergency' in vehData[vehName]) {
      if ((vehData[vehName].emergency == true) && ("emergencyData" in vehData[vehName])) {
        retVal += "<tr><td class=\"tblEmerg\" colspan=4>** EMERGENCY **</td></tr>";
        retVal += "<td class=\"tblEmerg\" colspan=4>Description - " + vehData[vehName].emergencyData + "</td></tr>";
      }
    }
    
    retVal += "</table>";
  }
  
  // Return information to be included in the infoWindow's contents.
  return retVal;
}

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
      debugBox.value = "Goodbye " + debugStr;
      
      // Close an open info window, nuke the marker for the expred vehicle, and nuke the vehicle's object.
      vehData[veh].info.close();
      vehData[veh].marker.setMap(null);
      vehData[veh].pathPoly.setVisible(false);
      vehData[veh] = null;
      delete vehData[veh];
      vehNotNuked = false;
      
    } else if ((vehDelta >= vehHalflife) && (vehData[veh].active == true)) {
      
      // Update debug window
      debugBox.value = "Half life reached for " + debugStr;
      
      // Deactivate vehicle and change the icon for it.
      vehData[veh].active = false;
      vehData[veh].marker.setIcon(iconFactory(veh));
      changed = true;
    } else {
      // If it's marked as inactive the reactivate it.
      if ((vehDelta < vehHalflife) && (vehData[veh].active == false)) {
        
        // Update debug window
        debugBox.value = "Reviving " + debugStr;
        
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


function handleMessage(msg){
  if (!mapLoaded) {
    console.log("Maps not loaded. Discarding aircraft data.");
    return;
  }
  
  // Dump the JSON string to the message box.
  msgBox.value = msg;
  
  // JSONify the JSON string.
  msgJSON = JSON.parse(msg);
  
  // Don't continue processing the keepalive.
  if ('keepalive' in msgJSON) {
    return;
  }
  
  // Vehicle name
  vehName = "veh" + msgJSON.addr.toString();
  
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
        strokeOpacity: 0.8,
        strokeWeight: 2.0,
        visible: false,
        zIndex: 1000,
        path: new google.maps.MVCArray()
      })
    };
    
    // Create objects for the aircraft's marker and current data as well as a flag for position changes, etc.
    $.extend(true, vehData[vehName], msgJSON);
    
    // Create our marker.
    aMarker = new google.maps.Marker({
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
    debugStr = "";
    
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
    debugBox.value = "Hello " + debugStr;
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
      newPos = new google.maps.LatLng(vehData[vehName].lat, vehData[vehName].lon);
      
      // copy the path object
      var pathObject = vehData[vehName].pathPoly.getPath();
      
      // update with the new path
      pathObject.push(newPos);
      
      // push back to the polyline
      vehData[vehName].pathPoly.setPath(pathObject);
      
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

// Start the vehcile expiration routine which should be executed at the specified interval.
window.setInterval(function(){
  // If our map has been loaded then we can start "expiring" vehicles.
  if (mapLoaded) { expireVehicles(); }
}, vehExpireCheckInterval);
