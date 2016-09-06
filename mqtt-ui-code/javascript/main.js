
var eb;
var retryCount = 10;

var topic = "/my/private/channel";

function initialiseEventBus(){
  window.client = mqtt.connect('ws://broker.pikabot.org',{
      reconnectPeriod:60*1000
  });
  client.on("connect", function(err,res){
    client.subscribe(topic);
  })
  client.on("disconnect", function(err,res){
    client.unsubscribe(topic);
  })
  client.on("message", function (topic, payload) {
    console.log(payload.toString())
  });
}



$(document).ready(function () {
  initialiseEventBus()
});
