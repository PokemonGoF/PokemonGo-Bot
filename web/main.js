var map;
var user_data = {};
var inventory = {};
var playerInfo = {};
var pokedex = {};
var bagPokemon = {};
var bagItems = {};
var bagCandy = {};
var emptyDex = [];
var pokemonArray = {};
var i;
var user_index;
var imageExt = ".png";
var trainerSex = ["m","f"]
var numTrainers = [177, 109]

function initMap() {
  // load pokemon data now..
  loadJSON('pokemondata.json', function(data, successData) {
    console.log('Loaded pokemon data..');
    pokemonArray = data;
  }, errorFunc, 'pokemonData');
  for (var i = 0; i < users.length; i++) {
    user_data[users[i]] = {};
  }
  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 50.0830986, lng: 6.7613762},
    zoom: 8
  });
  document.getElementById("switchPan").checked = userFollow;
  document.getElementById("switchZoom").checked = userZoom;
  document.getElementById("imageType").checked = false;
  setTimeout(function(){
    placeTrainer();
    addCatchable();
    // updateInventory();
    setTimeout(function(){
      setInterval(updateTrainer, 1000);
      setInterval(addCatchable, 1000);
    }, 5000);
  }, 5000);
};

$('#switchPan').change(function(){
    if (this.checked) { userFollow = true } else { userFollow = false; }
});

$('#switchZoom').change(function(){
    if (this.checked) { userZoom = true } else { userZoom = false; }
});

$('#imageType').change(function(){
    if (this.checked) { imageExt = ".gif" } else { imageExt = ".png"; }
});

var errorFunc = function(xhr) {
  console.error(xhr);
};

var trainerFunc = function(data, user_index) {
  if (user_data[users[user_index]].hasOwnProperty('marker') === false) {
    console.log("New Marker: Trainer - " + data.lat + ", " + data.lng);
    randomSex = Math.floor(Math.random() * 1)
    user_data[users[user_index]].marker = new google.maps.Marker({
      map: map,
      position: {lat: parseFloat(data.lat), lng: parseFloat(data.lng)},
      icon: "image/trainer/" + trainerSex[randomSex] + Math.floor(Math.random() * numTrainers[randomSex]) + ".png",
      zIndex: 2,
      label: users[user_index]
    });
  } else {
    user_data[users[user_index]].marker.setPosition({lat: parseFloat(data.lat), lng: parseFloat(data.lng)});
  }
  if (users.length == 1 && userZoom == true) {
    map.setZoom(16);
  }
  if (users.length == 1 && userFollow == true) {
    map.panTo({
      lat: parseFloat(data.lat),
      lng: parseFloat(data.lng)
    });
  }
};

function placeTrainer() {
  for (var i = 0; i < users.length; i++) {
    loadJSON('location-'+users[i]+'.json', trainerFunc, errorFunc, i);
  }
}
function updateTrainer() {
  for (var i = 0; i < users.length; i++) {
    loadJSON('location-'+users[i]+'.json', trainerFunc, errorFunc, i);
  }
}

var catchSuccess = function(data, user_index) {
  if (data !== undefined && Object.keys(data).length > 0) {
    if (user_data[users[user_index]].catchables === undefined) {
      user_data[users[user_index]].catchables = {};
    }
    if (data.latitude !== undefined) {
      if (user_data[users[user_index]].catchables.hasOwnProperty(data.spawnpoint_id) === false) {
        poke_name = pokemonArray[data.pokemon_id-1].Name;
        console.log(poke_name + ' found near user ' + users[user_index]);
        user_data[users[user_index]].catchables[data.spawnpoint_id] = new google.maps.Marker({
          map: map,
          position: {lat: parseFloat(data.latitude), lng: parseFloat(data.longitude)},
          icon: "image/pokemon/" + pad_with_zeroes(data.pokemon_id, 3) + imageExt,
          zIndex: 4,
          optimized: false
        });
          if (userZoom == true) {
            map.setZoom(16);
          }
          if (userFollow == true) {
            map.panTo({
              lat: parseFloat(data.latitude),
              lng: parseFloat(data.longitude)
            });
          }
      } else {
        user_data[users[user_index]].catchables[data.spawnpoint_id].setPosition({
          lat: parseFloat(data.latitude),
          lng: parseFloat(data.longitude)
        });
        user_data[users[user_index]].catchables[data.spawnpoint_id].setIcon("image/pokemon/" + pad_with_zeroes(data.pokemon_id, 3) + imageExt);
      }
    }
  } else {
    if (user_data[users[user_index]].catchables !== undefined && Object.keys(user_data[users[user_index]].catchables).length > 0) {
      console.log('No pokemon found near user ' + users[user_index]);
      for (var key in user_data[users[user_index]].catchables) {
        user_data[users[user_index]].catchables[key].setMap(null);
      }
      user_data[users[user_index]].catchables = undefined;
    }
  }
};

function addCatchable() {
  for (var i = 0; i < users.length; i++) {
    loadJSON('catchable-'+users[i]+'.json', catchSuccess, errorFunc, i);
  }
}
// function updateInventory() {
//   loadJSON('info.json',
//     function(data) {
//       inventory = data;
//       playerInfo = filter(inventory, 'player_stats');
//       pokedex = filter(inventory, 'pokedex_entry');
//       bagPokemon = filter(inventory, 'pokemon_data');
//     },
//     function(xhr) { console.error(xhr); }
//   );
// }


function pad_with_zeroes(number, length) {
  var my_string = '' + number;
  while (my_string.length < length) {
      my_string = '0' + my_string;
  }
  return my_string;
}


function filter(arr, search) {
  var filtered = [];
  for(i=0; i < arr.length; i++) {
    if(arr[i].inventory_item_data[search] != undefined) { filtered.push(arr[i]); };
  }
  return filtered;
}
function buildPokedex() {
  var arr = pokedex;
  for(i=0; i < arr.length; i++) {
    if(document.getElementById('p'+i) != null) {
      document.getElementById('p'+i).innerHTML = '<table><tr><td>Number:</td><td>' + arr[i].inventory_item_data.pokedex_entry.pokedex_entry_number + '</td></tr><tr><td>Encountered:</td><td>' + arr[i].inventory_item_data.pokedex_entry.times_encountered + '</td></tr><tr><td>Captured:</td><td>' + arr[i].inventory_item_data.pokedex_entry.times_captured + '</td></tr></table>';
    }
  }
  return emptyDex;
}
function loadJSON(path, success, error, successData) {
  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function() {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        if (success)
          success(JSON.parse(xhr.responseText.replace(/\bNaN\b/g, "null")), successData);
      } else {
        if (error)
        error(xhr);
      }
    }
  };
xhr.open("GET", path, true);
xhr.send();
}