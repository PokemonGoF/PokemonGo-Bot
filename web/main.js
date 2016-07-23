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
    center: {
      lat: 50.0830986,
      lng: 6.7613762
    },
    zoom: 8
  });
  setTimeout(function() {
    placeTrainer();
    addCatchable();
    // updateInventory();
    setTimeout(function() {
      setInterval(updateTrainer, 1000);
      setInterval(addCatchable, 1000);
    }, 5000);
  }, 5000);
}

var errorFunc = function(xhr) {
  console.error(xhr);
};

var forts = []
var info_windows = []
var trainerFunc = function(data, user_index) {
  var z = 0;
  for (var i = 0; i < data.cells.length; i++) {
    cell = data.cells[i];
    for (var x = 0; x < data.cells[i].forts.length; x++) {
      var fort = cell.forts[x];
      if (!forts[fort.id]) {
        forts[fort.id] = new google.maps.Marker({
          map: map,
          position: {
            lat: parseFloat(fort.latitude),
            lng: parseFloat(fort.longitude)
          },
          icon: "image/forts/Pstop.png"
        });
        var contentString = fort.id + ' Type ' + fort.type
        info_windows[fort.id] = new google.maps.InfoWindow({
          content: contentString
        });
        console.log(forts[fort.id])


        google.maps.event.addListener(forts[fort.id], 'click', (function(marker, content, infowindow) {
          return function() {
            infowindow.setContent(content);
            infowindow.open(map, marker);
          };
        })(forts[fort.id], contentString, info_windows[fort.id]));

      }
    }

  }
  if (user_data[users[user_index]].hasOwnProperty('marker') === false) {
    console.log("New Marker: Trainer - " + data.lat + ", " + data.lng);
    user_data[users[user_index]].marker = new google.maps.Marker({
      map: map,
      position: {
        lat: parseFloat(data.lat),
        lng: parseFloat(data.lng)
      },
      icon: "image/trainer-icon.png"
    });
  } else {
    user_data[users[user_index]].marker.setPosition({
      lat: parseFloat(data.lat),
      lng: parseFloat(data.lng)
    });
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
    loadJSON('location-' + users[i] + '.json', trainerFunc, errorFunc, i);
  }
}

function updateTrainer() {
  for (var i = 0; i < users.length; i++) {
    loadJSON('location-' + users[i] + '.json', trainerFunc, errorFunc, i);
  }
}

var catchSuccess = function(data, user_index) {
  if (data !== undefined && Object.keys(data).length > 0) {
    if (user_data[users[user_index]].catchables === undefined) {
      user_data[users[user_index]].catchables = {};
    }
    if (data.latitude !== undefined) {
      if (user_data[users[user_index]].catchables.hasOwnProperty(data.spawnpoint_id) === false) {
        poke_name = pokemonArray[data.pokemon_id - 1].Name;
        console.log(poke_name + ' found near user ' + users[user_index]);
        user_data[users[user_index]].catchables[data.spawnpoint_id] = new google.maps.Marker({
          map: map,
          position: {
            lat: parseFloat(data.latitude),
            lng: parseFloat(data.longitude)
          },
          icon: "image/icons/" + data.pokemon_id + ".png"
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
        user_data[users[user_index]].catchables[data.spawnpoint_id].setIcon("image/icons/" + data.pokemon_id + ".png");
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
    loadJSON('catchable-' + users[i] + '.json', catchSuccess, errorFunc, i);
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
function filter(arr, search) {
  var filtered = [];
  for (i = 0; i < arr.length; i++) {
    if (arr[i].inventory_item_data[search] != undefined) {
      filtered.push(arr[i]);
    };
  }
  return filtered;
}

function buildPokedex() {
  var arr = pokedex;
  for (i = 0; i < arr.length; i++) {
    if (document.getElementById('p' + i) != null) {
      document.getElementById('p' + i).innerHTML = '<table><tr><td>Number:</td><td>' + arr[i].inventory_item_data.pokedex_entry.pokedex_entry_number + '</td></tr><tr><td>Encountered:</td><td>' + arr[i].inventory_item_data.pokedex_entry.times_encountered + '</td></tr><tr><td>Captured:</td><td>' + arr[i].inventory_item_data.pokedex_entry.times_captured + '</td></tr></table>';
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