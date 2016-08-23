
var eb;
var retryCount = 10;

// Support dynamic topic registration by #word
var urlHashTopic = location.hash ? location.hash.substring(1).toLowerCase() : null;
var topic = urlHashTopic ? urlHashTopic : "pgomapcatch/chat";

function initialiseEventBus(){
  window.client = mqtt.connect('ws://test.mosca.io'); // you add a ws:// url here
  client.subscribe("pgomapcatch/#");

  client.on("message", function(topic, payload) {
    //alert([topic, payload].join(": "));
    console.log('Topic is '+topic)

    Materialize.toast(payload, 4000);
    if(topic === 'pgomapcatch/chat'){
      console.log('Chatting event')
      displayChatMessageOnMap(payload)
    } else {

        //@ro: let's grab the message and split that shit. (simple for now, maybe we could just parse the json instead)
        var pLoadR = payload.toString();
        var pLoadR2 = pLoadR.split(",");
        var olat = pLoadR2[0]
        var olong = pLoadR2[1]
      var sessid = pLoadR2[2]

      displayMessageOnMap(payload, olat, olong, sessid);
    }
  });

  client.publish("pgochat/join", "I just connected to the map!");
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
        window.client.publish(address, JSON.stringify(json.text));
        console.log(json);
    }
}

$( document ).ready(function() {
    if(!Modernizr.websockets || !Modernizr.geolocation){
        Materialize.toast('Browser not supported :(', 10000);
    }

    $("#side-nav-button").sideNav();

    var input = $("#input");
    input.keyup(function (e) {
        if (e.keyCode == 13) {
            sendMessage('pgomapcatch/chat', input);
        }
    });
    input.focus();

    $("#send-button").click(function(){
        sendMessage('pgomapcatch/chat', input);
    });

    $("#notification_lever").change(function() {
        advanced = !advanced;
        Materialize.toast(advanced ? 'Notifications On' : 'Notifications Off', 3000);
    });

    $("#accurate_location_lever").change(function() {
        shareAccurateLocation = !shareAccurateLocation;
        Materialize.toast(shareAccurateLocation ? 'Sharing Your Accurate Location' : 'Sharing Your Fuzzy Location', 3000);
    });

    if (topic != "main"){
        Materialize.toast("Private chat map - "+topic, 5000);
    }

    Materialize.toast("New: Click a user dot to mute it!", 7000);
});
