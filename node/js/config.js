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
var debug = true;

/***************************************************
 * VEHICLE CONFIGURATION
 **************************************************/
// Ships
var dirShip = "m 0,0 -20,50 40,0 -20,-50"
var dirShipScl = 0.15
var ndShip = "m 0,0 -20,20 20,20 20,-20 -20,-20"
var ndShipScl = 0.21
var shipActive = "#0000ff"//color of active ship icons (hex)
var shipInactive = "#000066"//color of nonresponsive ship icons (hex)
var shipAge = 5 * (60 * 1000);//how long to retain a ship after losing contact (miliseconds)

// Aircraft
var dirAircraft = "m 0,0 -20,50 20,-20 20,20 -20,-50"
var dirAircraftScl = 0.15
var ndAircraft = "m 15,15 a 15,15 0 1 1 -30,0 15,15 0 1 1 30,0 z"
var ndAircraftScl = 0.24
var aircraftActive = "#ff0000"//color of active aircraft icons (hex)
var aircraftInactive = "#660000"//color of nonresponsive aircraft icons (hex)
var aircraftAge = 2 * (60 * 1000);//how long to retain a ship after losing contact (miliseconds)

// General
var vehExpireCheckInterval = 1 * 1000;//frequency to check for expired vehicles (miliseconds)

/***************************************************
 * VEHICLE PATH ALTITUDE COLORING
 **************************************************/
var minimumAltitude = 0;//altitude to set as the lowest color for the ramp (X,000 feet)
var maximumAltitude = 45;//altitude to set as the highest color for the ramp (X,000 feet)
var spectrum = ['aqua','yellow','fuchsia','red'];//colors defining the ramp, low at position [0], high at [3]

/***************************************************
 * MAPS GENERAL CONFIGURATION
 **************************************************/
var useLocation = true;//whether to attempt to determine the user's location
var defaultLat = 45.555080;//default latitude if useLocation=false or detection fails
var defaultLng = -122.115890;//default longitude if useLocation=false or detection fails
var defaultZoom = 9;//default zoom level of the map

/***************************************************
 * MAPS CUSTOM STYLE
 **************************************************/
var customStyleName = "Monochrome";//name of the custom style for the view toggle
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
