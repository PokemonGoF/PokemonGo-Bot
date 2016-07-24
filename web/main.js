var map;
var user_data = {};
var pokemonArray = {};
var forts = [];
var info_windows = [];
var i;
var user_index;
var trainerSex = ["m","f"];
var numTrainers = [177, 109];
var menu;
var teams = ["TeamLess", "Mystic", "Valor", "Instinct"];
var out;
var out1;
var outArray = [];
var itemsArray = {
    "0": "Unknown",

    "1": "Pokeball",
    "2": "Greatball",
    "3": "Ultraball",
    "4": "Masterball",

    "101": "Potion",
    "102": "Super Potion",
    "103": "Hyper Potion",
    "104": "Max Potion",

    "201": "Revive",
    "202": "Max Revive",

    "301": "Lucky Egg",

    "401": "Incense",
    "402": "Spicy Incense",
    "403": "Cool Incense",
    "404": "Floral Incense",

    "501": "Troy Disk",

    "602": "X Attack",
    "603": "X Defense",
    "604": "X Miracle",

    "701": "Razz Berry",
    "702": "Bluk Berry",
    "703": "Nanab Berry",
    "704": "Wepar Berry",
    "705": "Pinap Berry",

    "801": "Special Camera",

    "901": "Incubator (Unlimited)",
    "902": "Incubator",

    "1001": "Pokemon Storage Upgrade",
    "1002": "Item Storage Upgrade"
}


function initMap() {
  // load pokemon data now..
  loadJSON('pokemondata.json', function(data, successData) {
    console.log('Loaded pokemon data..');
    pokemonArray = data;
  }, errorFunc, 'pokemonData');
  var trainer_options = "";
  for (var i = 0; i < users.length; i++) {
    user_data[users[i]] = {};
    trainer_options += "<option value=\"" + i + "\">" + users[i] + "</option>";
  }
  $("#trainer_users").html(trainer_options);
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
    setTimeout(function(){
      setInterval(addInventory, 1000);
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

var invSuccess = function(data, user_index) {
  user_data[users[user_index]].player_stats = filter(data, 'player_stats');
  user_data[users[user_index]].bag_items = filter(data, 'item');
  user_data[users[user_index]].bag_pokemon = filter(data, 'pokemon_data');
  user_data[users[user_index]].pokedex = filter(data, 'pokedex_entry');
  user_data[users[user_index]].bag_candy = filter(data, 'pokemon_family');
  $(".trainer_card").show();
};

var trainerFunc = function(data, user_index) {
  for (var i = 0; i < data.cells.length; i++) {
    cell = data.cells[i];
    if (data.cells[i].forts != undefined) {
      for (var x = 0; x < data.cells[i].forts.length; x++) {
        var fort = cell.forts[x];
        if (!forts[fort.id]) {
          if (fort.type === 1 ) {
            forts[fort.id] = new google.maps.Marker({
              map: map,
              position: {
                lat: parseFloat(fort.latitude),
                lng: parseFloat(fort.longitude)
              },
              icon: "image/forts/img_pokestop.png"
            });
          } else {
            forts[fort.id] = new google.maps.Marker({
              map: map,
              position: {
                lat: parseFloat(fort.latitude),
                lng: parseFloat(fort.longitude)
              },
              icon: "image/forts/" + teams[fort.owned_by_team] + ".png"
            });
          }
          pokemonGuard = '';
          fortType = 'PokeStop';
          fortTeam = '';
          fortPoints = '';
          if (fort.guard_pokemon_id != undefined) {
            pokemonGuard = 'Guard Pokemon: ' + pokemonArray[fort.guard_pokemon_id-1].Name + '<br>';
            fortType = 'Gym';
            fortTeam = 'Team: ' + teams[fort.owned_by_team] + '<br>';
            fortPoints = 'Points: ' + fort.gym_points;
          }
          var contentString = 'Id: ' + fort.id + '<br>Type: ' + fortType + '<br>' + pokemonGuard + fortPoints;
          info_windows[fort.id] = new google.maps.InfoWindow({
            content: contentString
          });
          google.maps.event.addListener(forts[fort.id], 'click', (function(marker, content, infowindow) {
            return function() {
              infowindow.setContent(content);
              infowindow.open(map, marker);
            };
          })(forts[fort.id], contentString, info_windows[fort.id]));
        }
      }
    }
  }
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
        Materialize.toast(poke_name + ' appeared near trainer: ' + users[user_index], 3000, 'rounded')
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
function addInventory() {
  for (var i = 0; i < users.length; i++) {
    loadJSON('inventory-'+users[i]+'.json', invSuccess, errorFunc, i);
  }
}

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

$(document).ready(function(){
  $('.tooltipped').tooltip({delay: 50});
});

var sideMenu = {
  subTitle: 'Window Title',
  subTitleEl: $('#submenu .card-title'),
  sideContentEl: $('#subcontent'),
  submenuContainerEl: $('#submenu'),
  trainerStatsEl: $('#submenu .trainer_info'),
  selectedUser: 0,
  selectedTab: false,
  hideAllSubs: function() {
    sideMenu.trainerStatsEl.hide();
    sideMenu.selectedTab = false;
    sideMenu.submenuContainerEl.hide();
  },
  toggleWindow: function(tab) {
    if (sideMenu.submenuContainerEl.is(':visible') && sideMenu.selectedTab == tab) {
      // window already visible, hide it.
      sideMenu.hideAllSubs();
    } else {
      // window isn't visible, show it.
      if (tab == 'stats') {
        sideMenu.showStats();
      } else if (tab == 'items') {
        sideMenu.hideAllSubs();
        sideMenu.showItems();
      } else if (tab == 'pokemon') {
        sideMenu.hideAllSubs();
        sideMenu.showPokemon();
      } else if (tab == 'pokedex') {
        sideMenu.hideAllSubs();
        sideMenu.showPokedex();
      }
      sideMenu.submenuContainerEl.show();
    }
  },
  showStats: function(e) {
    sideMenu.subTitleEl.html('Trainer Info');
    var trainer = user_data[users[sideMenu.selectedUser]];
    var trainer_stats = trainer.player_stats[0];

    $('.trainer_info .username').html(users[sideMenu.selectedUser]);
    $('.trainer_info .level').html(trainer_stats.inventory_item_data.player_stats.level);
    $('.trainer_info .experience').html(trainer_stats.inventory_item_data.player_stats.experience);
    $('.trainer_info .exptolevel').html((parseInt(trainer_stats.inventory_item_data.player_stats.level) + 1) + ': ' + (parseInt(trainer_stats.inventory_item_data.player_stats.next_level_xp) - trainer_stats.inventory_item_data.player_stats.experience));
    $('.trainer_info .pokemon_encountered').html(trainer_stats.inventory_item_data.player_stats.pokemons_encountered);
    $('.trainer_info .pokeballs_thrown').html(trainer_stats.inventory_item_data.player_stats.pokeballs_thrown);
    $('.trainer_info .pokemon_caught').html(trainer_stats.inventory_item_data.player_stats.pokemons_captured);
    $('.trainer_info .small_ratata_caught').html(trainer_stats.inventory_item_data.player_stats.small_rattata_caught);
    $('.trainer_info .pokemon_evolved').html(trainer_stats.inventory_item_data.player_stats.evolutions);
    $('.trainer_info .eggs_hatched').html(trainer_stats.inventory_item_data.player_stats.eggs_hatched);
    $('.trainer_info .unique_pokedex_entries').html(trainer_stats.inventory_item_data.player_stats.unique_pokedex_entries);
    $('.trainer_info .pokestops_visited').html(trainer_stats.inventory_item_data.player_stats.poke_stop_visits);
    $('.trainer_info .km_walked').html(parseFloat(trainer_stats.inventory_item_data.player_stats.km_walked).toFixed(2));
    sideMenu.trainerStatsEl.show();
    sideMenu.selectedTab = 'stats';
  },
  showItems: function(e) {
    sideMenu.subTitleEl.html('Items in Bag');
    var trainer = user_data[users[sideMenu.selectedUser]];
    var trainer_bag_items = trainer.bag_items;

    out = '<div class="row items"><div class="col s12"><h5>' + users[sideMenu.selectedUser] + '</h5>';

    for (var i = 0; i < trainer_bag_items.length; i++) {
      out += '<table><tr><td><img src="/image/items/' + trainer_bag_items[i].inventory_item_data.item.item_id + '.png" class="item_img"></td><td>Item: ' + itemsArray[trainer_bag_items[i].inventory_item_data.item.item_id] +
      '<br>Count: ' + trainer_bag_items[i].inventory_item_data.item.count + '</td>';
    }
    out += '</tr></table></div></div>';
    $('#unfinished_toggles').html(out);
    sideMenu.selectedTab = 'items';
  },
  showPokemon: function(e) {
    sideMenu.subTitleEl.html('Pokemon in Bag');
    var trainer = user_data[users[sideMenu.selectedUser]];
    var trainer_pokemon = trainer.bag_pokemon;

    out = '<div class="row items"><div class="col s12"><h5>' + users[sideMenu.selectedUser] + '</h5><table>';
    for (var i = 0; i < trainer_pokemon.length; i++) {
      if (trainer_pokemon[i].inventory_item_data.pokemon_data.is_egg) {
        pkmnNum = "???";
        pkmnImage = "Egg.png";
        pkmnName = "Egg";
      } else {
        pkmnNum = trainer_pokemon[i].inventory_item_data.pokemon_data.pokemon_id;
        pkmnImage = pad_with_zeroes(trainer_pokemon[i].inventory_item_data.pokemon_data.pokemon_id, 3) + '.png';
        pkmnName = pokemonArray[pkmnNum-1].Name;
      }
      the_cp = trainer_pokemon[i].inventory_item_data.pokemon_data.cp ? trainer_pokemon[i].inventory_item_data.pokemon_data.cp : '???';
      out += '<tr><td><img src="/image/pokemon/' + pkmnImage + '" class="png_img"></td><td class="left-align">Name: ' + pkmnName +
      '<br>Number: ' + pkmnNum + '<br>CP: ' + the_cp +'</td></tr>';
    }
    out += '</table></div></div>';
    $('#unfinished_toggles').html(out);
    sideMenu.selectedTab = 'pokemon';
  },
  showPokedex: function(e) {
    sideMenu.subTitleEl.html('Pokedex');
    var trainer = user_data[users[sideMenu.selectedUser]];
    var pokedex = trainer.pokedex;

    out = '<div class="row items"><div class="col s12"><h5>' + users[sideMenu.selectedUser] + '</h5><table>';
    for (var i = 0; i < pokedex.length; i++) {
      pkmnNum = pokedex[i].inventory_item_data.pokedex_entry.pokedex_entry_number;
      pkmnImage = pad_with_zeroes(pokedex[i].inventory_item_data.pokedex_entry.pokedex_entry_number, 3) + '.png';
      pkmnName = pokemonArray[pkmnNum-1].Name;
      out += '<tr><td><img src="/image/pokemon/' + pkmnImage + '" class="png_img"></td><td class="left-align">Name: ' + pkmnName +
      '<br>Number: ' + pkmnNum + '<br>Times Encountered: ' + pokedex[i].inventory_item_data.pokedex_entry.times_encountered +
      '<br>Times Caught: ' + pokedex[i].inventory_item_data.pokedex_entry.times_captured + '</td></tr>';
    }
    out += '</table></div></div>';
    $('#unfinished_toggles').html(out);
    sideMenu.selectedTab = 'pokedex';
  }
};

$("#trainer_users").on('change', function(e) {
  sideMenu.selectedUser = e.target.value;
  sideMenu.hideAllSubs();
});

$('#tInfo').click(function() {
  sideMenu.toggleWindow('stats');
});

$('#tItems').click(function(){
  sideMenu.toggleWindow('items');
});

$('#tPokemon').click(function(){
    sideMenu.toggleWindow('pokemon');
});

$('#tPokedex').click(function(){
    sideMenu.toggleWindow('pokedex');
});
