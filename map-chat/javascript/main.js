
var eb;
var retryCount = 10;

// Support dynamic topic registration by #word
var urlHashTopic = location.hash ? location.hash.substring(1).toLowerCase() : null;
var topic = urlHashTopic ? urlHashTopic : "pgomapcatch/chat";

function initialiseEventBus(){
  window.client = mqtt.connect('ws://broker.pikabot.org'); // you add a ws:// url here
  client.subscribe("pgo/#");
  client.subscribe("pgochat/chat");

  client.on("message", function (topic, payload) {
    //Materialize.toast(payload, 4000);
    if (topic === 'pgochat/chat') {
	  var objx = $.parseJSON(payload);
	  var message_data = "<b>anonymous" + Math.floor(Math.random()*90000) + "</b>: " + objx.text;
	  displayChatMessageOnMap(payload);
      Materialize.toast(message_data, 5000);
      var msg = JSON.parse(payload);
      console.info('[CHAT]', '(' + msg.lat + ',' + msg.lng + '): ', msg.text);
    } else if (/^pgo\/all\/catchable/i.test(topic)) {
      var pokemon = JSON.parse(payload);
      var path = "./images/p/"
      var icon = path + "0" + pokemon.pokemon_id + ".png"
      var icostr = icon.toString();
      displayMessageOnMap(payload, pokemon.latitude, pokemon.longitude, pokemon.encounter_id, icostr, pokemon.expiration_timestamp_ms, pokemon.pokemon_name);

      console.debug('[CATCHABLE]', pokemon.pokemon_name, '(' + pokemon.latitude + ',' + pokemon.longitude + ')');
    } else {
      console.debug(topic);
    }
  });
}

function sendMessage(topic, input) {
  if (input.val()) {
    publish(topic, input.val());
    input.val('');
  }
}

function publish(address, message) {
  if (window.client) {
    var json = createMessage(message);
    window.client.publish(address, JSON.stringify(json));
    console.log(json);
  }
}

$(document).ready(function () {
  if (!Modernizr.websockets || !Modernizr.geolocation) {
    Materialize.toast('Browser not supported :(', 10000);
  }

  $("#side-nav-button").sideNav();

  var input = $("#input");
  input.keyup(function (e) {
    if (e.keyCode == 13) {
      sendMessage('pgochat/chat', input);
    }
  });
  input.focus();

  $("#send-button").click(function () {
    sendMessage('pgochat/chat', input);
  });

  $("#notification_lever").change(function () {
    advanced = !advanced;
    Materialize.toast(advanced ? 'Notifications On' : 'Notifications Off', 3000);
  });

  $("#accurate_location_lever").change(function () {
    shareAccurateLocation = !shareAccurateLocation;
    Materialize.toast(shareAccurateLocation ? 'Sharing Your Accurate Location' : 'Sharing Your Fuzzy Location', 3000);
  });

  if (topic != "main") {
    Materialize.toast("Private chat map - " + topic, 5000);
  }

  Materialize.toast("New: Click a user dot to mute it!", 7000);
});
