
var eb;
var retryCount = 10;

// Support dynamic topic registration by #word
var urlHashTopic = location.hash ? location.hash.substring(1).toLowerCase() : null;
var topic = urlHashTopic ? urlHashTopic : "main";

function initialiseEventBus(){
  window.client = mqtt.connect('ws://test.mosca.io'); // you add a ws:// url here
  client.subscribe("pgomapcatch/#");

  client.on("message", function(topic, payload) {
    //alert([topic, payload].join(": "));
    //client.end();
    Materialize.toast(payload, 2000);
    displayMessageOnMap(payload);
  });

  client.publish("mqtt/demo", "hello world!");
    /*eb = new vertx.EventBus("http://localhost:8080/chat");

    eb.onopen = function () {
        subscribe(topic);
    };

    eb.onclose = function(){
        if (retryCount) {
            retryCount--;
            console.log('Connection lost, scheduling reconnect');
            setTimeout(initialiseEventBus, 1000);
        } else{
            Materialize.toast('Connection lost, please refresh :( ', 10000);
        }
    };*/
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
        window.client.publish(address, json);
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
            sendMessage(topic, input);
        }
    });
    input.focus();

    $("#send-button").click(function(){
        sendMessage(topic, input);
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
