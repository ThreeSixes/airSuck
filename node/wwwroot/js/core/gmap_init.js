"use strict";// overcome current Chrome and Firefox issues with ECMA6 stuff like classes
/***********************************************************
 * Airsuck Google Maps system setup
 * v. 0.1
 *
 * Licensed under GPL V3
 * https://github.com/ThreeSixes/airSuck
 *
 * Deps: jQuery, GoogleMaps JS API loaded
 **********************************************************/

/***************************************************
 * INITIALIZE MAPS
 * Only google at the moment
 **************************************************/
// Initialize the Google map.
function initMap() {
  if(debug){console.log("Maps loading...");}
  
  // Attempt to detect user location if turned on
  if (useLocation) {
    //attempt to determine location
    $.ajax( { url: '//freegeoip.net/json/', type: 'POST', dataType: 'jsonp',
      success: function(location) {
        // update the lat and lng if we can detect them
        defaultLng = location.longitude;
        defaultLat = location.latitude;
        if(debug){console.log("Got lat/lng: " + defaultLat + ", " + defaultLng);}
      }
    } );
  }
  
  // Set up the map object.
  map = new google.maps.Map(document.getElementById('map'), {
    zoom: defaultZoom,
    center: {lat: defaultLat, lng: defaultLng},
    mapTypeControlOptions: {
      style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
      mapTypeIds: [google.maps.MapTypeId.TERRAIN, google.maps.MapTypeId.SATELLITE]
      },
    mapTypeControl: false
  });
  
  // Set default map to terrain.
  map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
 
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
  var customMap = document.createElement('option');
  customMap.className = 'mapStyleSelector';
  customMap.value = customStyleName;
  customMap.innerHTML = customStyleName;
  
  // Add the style options to the main style control container
  styleControlContainer.appendChild(styleSelectBox);
  styleSelectBox.appendChild(terrainMap);
  styleSelectBox.appendChild(satelliteMap);
  styleSelectBox.appendChild(customMap);
  
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
        case customStyleName:
          // load the terrain map and add a custom style
          map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
          map.set('styles',customStyle);
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
  map.set('styles',customStyle);
  // Set the selectbox to monochrome
  styleSelectBox.options[2].selected = true;
  
  // The map loaded.
  mapLoaded = true;
}
