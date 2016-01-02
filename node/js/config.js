/***********************************************************
 * Airsuck JS configuration
 * v. 0.1
 *
 * Licensed under GPL V3
 * https://github.com/ThreeSixes/airSuck
 * 
 * Centralize configuration for airsuck javascript
 *
 * Deps: none, **required for all airsuck JS functions
 **********************************************************/

/***************************************************
 * DEBUG
 **************************************************/
var debug = true; // Do we want to have debugging data onscreen and in the console?

/***************************************************
 * VEHICLE CONFIGURATION
 **************************************************/
// Ships
var dirShip = "m 0,0 -20,50 40,0 -20,-50"; // Path we want to use for AIS targets that we have direction data for.
var dirShipScl = 0.15; // Scale of the path.
var ndShip = "m 0,0 -20,20 20,20 20,-20 -20,-20"; // Path we want to use for AIS targets that we don't have direction data for.
var ndShipScl = 0.21; // Scale of the path.
var shipActive = "#0000ff"; // Color of active ship icons (hex)
var shipInactive = "#000066"; // Color of nonresponsive ship icons (hex)
var shipAge = 5 * (60 * 1000); // How long to retain a ship after losing contact (miliseconds)

// Aircraft
var dirAircraft = "m 0,0 -20,50 20,-20 20,20 -20,-50"; // Path we want to use for ADS-B targets we have direction data for.
var dirAircraftScl = 0.15; // Scale of the path.
var ndAircraft = "m 15,15 a 15,15 0 1 1 -30,0 15,15 0 1 1 30,0 z"; // Path we want to sue for ADS-B targets we don't have direction data for.
var ndAircraftScl = 0.24; // Scale of the path.
var aircraftActive = "#ff0000"; // Color of active aircraft icons (hex)
var aircraftInactive = "#660000"; // Color of nonresponsive aircraft icons (hex)
var aircraftAge = 2 * (60 * 1000); // How long to retain a ship after losing contact (miliseconds)

// General
var vehExpireCheckInterval = 1 * 1000; // Frequency to check for expired vehicles (miliseconds)
var vehicleTypes = []; // Array for registering vehicle types (AIS, SSR)
var vehicles = []; // Main array holding vehicles - replacing vehData array with vehicle objects

/***************************************************
 * VEHICLE PATH ALTITUDE COLORING
 **************************************************/
var minimumAltitude = 0; // Altitude to set as the lowest color for the ramp (X,000 feet)
var maximumAltitude = 45; // Altitude to set as the highest color for the ramp (X,000 feet)
var spectrum = ['aqua','yellow','fuchsia','red']; // Colors defining the ramp, low at position [0], high at [3]

/***************************************************
 * MAPS GENERAL CONFIGURATION
 **************************************************/
var useLocation = true; // Whether to attempt to determine the user's location via browser
var defaultLat = 45.555080; // Default latitude if useLocation=false or detection fails
var defaultLng = -122.115890; // Default longitude if useLocation=false or detection fails
var defaultZoom = 9; // Default zoom level of the map

/***************************************************
 * MAPS STYLES
 **************************************************/
// vehicle path style:
var pathStrokeOpacity = 0.8;
var pathStrokeWeight = 2.0;
var pathzIndex = 1000;

// custom map style:
var customStyleName = "Monochrome"; // Name of the custom style for the view toggle
var customStyle = [
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
      { "color": "#ffffff" }
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
