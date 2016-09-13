
var eb;
var retryCount = 10;

// Support dynamic topic registration by #word
var urlHashTopic = location.hash ? location.hash.substring(1).toLowerCase() : null;
var topic = urlHashTopic ? urlHashTopic : "pgomapcatch/chat";

function initialiseEventBus(){
  window.client = mqtt.connect('ws://ws.pikabot.org',{
      reconnectPeriod:20*1000
  });
  client.on("connect", function(err,res){
    client.subscribe("pgomapcatch/#");
    client.subscribe("pgochat/chat");
  })
  client.on("disconnect", function(err,res){
    client.unsubscribe("pgomapcatch/#");
    client.unsubscribe("pgochat/chat");
  })
  client.on("message", function (topic, payload) {
    //Materialize.toast(payload, 4000);
    if (topic === 'pgochat/chat') {
	  var objx = $.parseJSON(payload);
	  var message_data = "<b>anonymous" + Math.floor(Math.random()*90000) + "</b>: " + objx.text;
	  displayChatMessageOnMap(payload);
      Materialize.toast(message_data, 5000);
      var msg = JSON.parse(payload);
      console.info('[CHAT]', '(' + msg.lat + ',' + msg.lng + '): ', msg.text);
    } else if (/^pgomapcatch\/all\/catchable/i.test(topic)) {
      //@ro: let's grab the message and split that shit. (simple for now, maybe we could just parse the json instead)
      var pLoadR = payload.toString();
      var pLoadR2 = pLoadR.split(",");
      var olat = pLoadR2[0]
      var olong = pLoadR2[1]

      var pokemon_id = parseInt(pLoadR2[2])
      if (pokemon_id>0 && pokemon_id< 160){
        var ico = pLoadR2[2]
        var expir = pLoadR2[3]
        var pokenick = pLoadR2[4]
        var sessid = pLoadR2[2]
        var path = "./images/p/"
        console.log('icon is '+ico)
        var icon = path + "0" + ico.replace(" ","") + ".png"
        var icostr = icon.toString();
        displayMessageOnMap(payload, olat, olong, sessid, icostr, expir, pokenick);
        console.debug('[CATCHABLE]', pokenick, '(' + olat + ',' + olong + ')');
      } else {
        var pokemon_id = parseInt(pLoadR2[3])
        if (pokemon_id>0 && pokemon_id< 160){
          var ico = pLoadR2[3]
          var expir = pLoadR2[4]
          var pokenick = pLoadR2[5]
          var sessid = pLoadR2[5]
          var path = "./images/p/"
          console.log('icon is '+ico)
          var icon = path + "0" + ico.replace(" ","") + ".png"
          var icostr = icon.toString();
          displayMessageOnMap(payload, olat, olong, sessid, icostr, expir, pokenick);
          console.debug('[CATCHABLE]', pokenick, '(' + olat + ',' + olong + ')');
        }
      }
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

  /*if (topic != "main") {
    Materialize.toast("Private chat map - " + topic, 5000);
  }*/

  //Materialize.toast("News: Server Over Load since the huge traffic ... ", 7000);
});
