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
var debug = 'dev'; // Do we want to have debugging data onscreen and in the console? false, all, dev

/***************************************************
 * CUSTOM VEHICLES TO INCLUDE - from the js/vehicles directory
 **************************************************/
var loadCustomVehicles = ['airSSR.js','airAIS.js'];//order determines the sidebar arrangement

/***************************************************
 * VEHICLE ARRAYS AND RELATED
 **************************************************/
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
var map; // Make the map global

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
    "featureType": "water",
    "elementType": "labels.text.stroke",
    "stylers": [
      { "visibility": "off" }
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
