
var mySessionId;
var map;
var userLocation;
var fuzzyUserLocation;
var markersMap = {};
var markerImage;
var advanced = true;
var infoWindowZIndex = 100;
var shareAccurateLocation = false;

var isLowResolution = window.screen.width < 768;
var defaultZoom = isLowResolution ? 2 : 3;
var minZoom = isLowResolution ? 1 : 3;

var locationOptions = {
  enableHighAccuracy: true,
  timeout: 10000,
  maximumAge: 10000
};

var entityMap = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': '&quot;',
  "#": "&#35;",
  "'": '&#39;',
  "/": '&#x2F;',
  "卐": 'I am a dick ',
  "卍": 'I am a dick '
};

function initialize() {

  var defaultLatLng = new google.maps.LatLng(0.1, 0.1); // Add the coordinates

  markerImage = {
    url: 'images/blue_marker.png',
    scaledSize: new google.maps.Size(30, 30)
  };

  disabledMarkerImage = {
    url: 'images/grey_marker.png',
    scaledSize: new google.maps.Size(30, 30)
  };

  var mapOptions = {
    center: defaultLatLng,
    zoom: defaultZoom, // The initial zoom level when your map loads (0-20)
    minZoom: minZoom, // Minimum zoom level allowed (0-20)
    maxZoom: 18, // Maximum soom level allowed (0-20)
    zoomControl: false, // Set to true if using zoomControlOptions below, or false to remove all zoom controls.
    mapTypeId: google.maps.MapTypeId.ROADMAP, // Set the type of Map
    scrollwheel: true, // Enable Mouse Scroll zooming
    // All of the below are set to true by default, so simply remove if set to true:
    panControl: false, // Set to false to disable
    mapTypeControl: false, // Disable Map/Satellite switch
    scaleControl: false, // Set to false to hide scale
    streetViewControl: false, // Set to disable to hide street view
    overviewMapControl: false, // Set to false to remove overview control
    rotateControl: false // Set to false to disable rotate control
  };
  var mapDiv = document.getElementById('map-canvas');
  map = new google.maps.Map(mapDiv, mapOptions);

  initialiseEventBus();

  //navigator.geolocation.getCurrentPosition(onFirstPosition, onPositionError, locationOptions);

  onFirstPosition({
     "coords": {
       latitude: parseFloat(0.1),
       longitude: parseFloat(0.1)
     }
   });
}

function onFirstPosition(position) {
  setUserLocation(position.coords.latitude, position.coords.longitude);
  map.panTo(userLocation);
  var message = {};
  message.lat = position.coords.latitude;
  message.lng = position.coords.longitude;
  message.text = "I just connected to the map!"

  client.publish("pgochat/chat", JSON.stringify(message));
}

function onPositionUpdate(position) {
  if (markersMap[mySessionId]) { //update user marker position
    setUserLocation(position.coords.latitude, position.coords.longitude);
    var userMarker = markersMap[mySessionId].marker;
    userMarker.setPosition(shareAccurateLocation ? userLocation : fuzzyUserLocation);
  }
}

function onPositionError(err) {
  // try fallback location provider ipinfo.io or generate random location
  // $.getJSON("http://ipinfo.io", onFallbackLocationProviderResponse, useRandomLocation);
  onFirstPosition({
    "coords": {
      latitude: parseFloat(0.1),
      longitude: parseFloat(0.1)
    }
  });
}

function onFallbackLocationProviderResponse(ipinfo) {
  console.log("Found location [" + ipinfo.loc + "] by ipinfo.io");
  var latLong = ipinfo.loc.split(",");
  onFirstPosition({
    "coords": {
      latitude: parseFloat(latLong[0]),
      longitude: parseFloat(latLong[1])
    }
  });
}

function useRandomLocation(err) {
  Materialize.toast('User location problem, using random location :P', 7000);
  // These ranges cover only the center of the map
  var lat = (90 * Math.random() - 22.5).toFixed(3);
  var lng = (180 * Math.random() - 90).toFixed(3);
  onFirstPosition({
    "coords": {
      latitude: parseFloat(lat),
      longitude: parseFloat(lng)
    }
  });
}

function setUserLocation(lat, lng) {
  userLocation = new google.maps.LatLng(lat, lng);
  fuzzyUserLocation = new google.maps.LatLng(Math.round(lat * 100) / 100, Math.round(lng * 100) / 100);
}

function createMessage(text) {
  return {
    lat: shareAccurateLocation ? userLocation.lat() : fuzzyUserLocation.lat(),
    lng: shareAccurateLocation ? userLocation.lng() : fuzzyUserLocation.lng(),
    text: text
  };
}

function setupMarkerAndInfoWindow(msgSessionId, content, position, map, icoOn, icoOff) {
    var infoWindow = new google.maps.InfoWindow({
      content: content,
      maxWidth: 400,
      disableAutoPan: true,
      zIndex: infoWindowZIndex
    });
    infoWindowZIndex++;

    var marker = new google.maps.Marker({
      position: position,
      map: map,
      draggable: false,
      icon: icoOn,
      title: "Click to mute/un-mute User " + msgSessionId
    });

    marker.addListener('click', function () {
      if (markersMap[msgSessionId].disabled) {
        markersMap[msgSessionId].disabled = false;
        marker.setIcon(icoOn);
      } else {
        markersMap[msgSessionId].disabled = true;
        marker.setIcon(icoOff);
        infoWindow.close();
      }
    });

    return {
      marker: marker,
      infoWindow: infoWindow
    };
}

function displayChatMessageOnMap(raw) {
  var msg = JSON.parse(raw)
  //console.log(msg)
  var newPosition = new google.maps.LatLng(msg.lat, msg.lng);
  var msgSessionId = msg.sessionId;

  // xss prevention hack
  msg.text = html_sanitize(msg.text);

  msg.text = String(msg.text).replace(/[&<>"#'\/卐卍]/g, function (s) {
    return entityMap[s];
  });

  // msg.text = msg.text ? embedTweet(msg.text) : "";
  msg.text = msg.text.replace(/&#35;(\S*)/g, '<a href="http://maps.pikabot.org/#$1" target="_blank">#$1</a>');

  // linkify
  msg.text = msg.text.replace(
    /(\b(https?|ftp|file):&#x2F;&#x2F;[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig,
    "<a target='_blank' href='$1'>$1</a>"
  );

  if (markersMap[msgSessionId]) { // update existing marker
    var existingMarker = markersMap[msgSessionId].marker;
    var existingInfoWindow = markersMap[msgSessionId].infoWindow;
    var existingTimeoutId = markersMap[msgSessionId].timeoutId;

    existingMarker.setPosition(newPosition);
    existingInfoWindow.setContent(msg.text);
    existingInfoWindow.setZIndex(infoWindowZIndex);
    infoWindowZIndex++;
    if (msg.text && !markersMap[msgSessionId].disabled) {
      if (existingTimeoutId) {
        clearTimeout(existingTimeoutId);
      }
      markersMap[msgSessionId].timeoutId = setTimeout(function () { existingInfoWindow.close() }, 10000);
      existingInfoWindow.open(map, existingMarker);
    }
  } else { // new marker
    var markerWindow = setupMarkerAndInfoWindow(msgSessionId,msg.text, newPosition, map, markerImage, disabledMarkerImage);
    var infoWindow = markerWindow.infoWindow;
    var marker = markerWindow.marker;

    if (msg.text !== 'undefined') {
      infoWindow.open(map, marker);
    }

    var timeoutId = setTimeout(function () { infoWindow.close() }, 10000);
    markersMap[msgSessionId] = {
      marker: marker,
      infoWindow: infoWindow,
      timeoutId: timeoutId,
      disabled: false
    }
  }

  if (advanced) {
    runAdvancedOptions(msg);
  }
}

// @ro: to calculate time until expiration
function timeUntil(now, then) {
  var timestampNow = Date.parse(now);
  var timestampThen = Date.parse(then);
  var diff = new Date(timestampThen - timestampNow);

  diff.setSeconds(Math.round(diff.getSeconds() / 30) * 30);

  return diff;
}

function displayMessageOnMap(msg, olat, olong, sessid, icostr, expir, pokenick) {
  // @ro: passing values split from incoming payload into two variables for now (lat and long)
  var newPosition = new google.maps.LatLng(olat, olong);
  var msgSessionId = sessid;
  var expiration = expir;
  var pName = '';
  if(typeof pokenick === 'undefined'){
    var pName = " <i>just appeared! </i></b><br>lat: " + olat + " / long: " + olong;
  } else {
    var pName = "<b>" + pokenick + "</b><i> just appeared! </i></b><br>lat: " + olat + " / long: " + olong;
  }
  // console.log(pName);
  // @ro: just checking the output
  //console.log(olat);
  //console.log(olong);

  // xss prevention hack
  msg.text = html_sanitize(msg.text);

  msg.text = String(msg.text).replace(/[&<>"#'\/卐卍]/g, function (s) {
    return entityMap[s];
  });

  // msg.text = msg.text ? embedTweet(msg.text) : "";
  msg.text = msg.text.replace(/&#35;(\S*)/g, '<a href="http://maps.pikabot.org/#$1" target="_blank">#$1</a>');

  // linkify
  msg.text = msg.text.replace(
    /(\b(https?|ftp|file):&#x2F;&#x2F;[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig,
    "<a target='_blank' href='$1'>$1</a>"
  );

  var icon = { url: icostr, scaledSize: new google.maps.Size(36, 36) };
  var markerMap = setupMarkerAndInfoWindow(msgSessionId, pName, newPosition, map, icon, icon);
  var marker = markerMap.marker;
  var infoWindow = markerMap.infoWindow;

  if (!markersMap[msgSessionId]) { // new marker
    //disable it for now
    //infoWindow.open(map, marker);

    var timeoutId = setTimeout(function () { infoWindow.close() }, 10000);
    markersMap[msgSessionId] = {
      marker: marker,
      infoWindow: infoWindow,
      timeoutId: timeoutId,
      disabled: false
    }
  }

  if (advanced) {
    runAdvancedOptions(msg);
  }
}

function embedTweet(text) {
  var tweetText = "Someone wrote " + text + " on ";
  var tweetUrl = "https:\/\/twitter.com\/share?url=http://maps.pikabot.org/&text=" + tweetText;
  var width = 500, height = 300;
  var left = (screen.width / 2) - (width / 2);
  var top = (screen.height / 2) - (height / 2);
  return " <a href=\"" + tweetUrl + "\"" +
    " onclick=\"window.open('" + tweetUrl + "', 'newwindow'," +
    " 'width=" + width + ", height=" + height + ", top=" + top + ", left=" + left + "'); return false;\">" +
    " <image src='images/twitter_icon_small.png'> <\/a> " + text;
}

function clearMessageFromMap() {
  for (var markerSessionId in markersMap) {
    if (markersMap.hasOwnProperty(markerSessionId)) {
      markersMap[markerSessionId].infoWindow.close();
    }
  }
}

function changeZoom(factor) {
  map.setZoom(map.getZoom() + factor);
}

function runAdvancedOptions(msg) {
  if (msg.sessionId == mySessionId) {
    return;
  }

  if (Notification.permission !== "granted") {
    Notification.requestPermission();
  }

  new Notification('Incoming MapChat', {
    icon: 'favicons/apple-touch-icon-120x120.png',
    body: msg.text ? "Incoming message: " + msg.text : "New user"
  });
}

// This should be displayed when the app is opened from a mobile facebook app WebView (Until a better solution is found)
if (window.navigator.userAgent.indexOf("FBAV") > 0) {
  document.write(
    "<div class=\"center\" style=\"position: fixed; top: 120px; width: 100%;\">" +
    "<div class=\"\">" +
    "<h6>" +
    "This page will not work inside the facebook app, " +
    "please open it in the native browser." +
    "</h6>" +
    "</div>" +
    "</div>"
  );
} else {
  google.maps.event.addDomListener(window, 'load', initialize);
}
