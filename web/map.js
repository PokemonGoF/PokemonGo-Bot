var map;
var center_lat = 0.0;
var center_lng = 0.0;
var tMarker;
var cMarker;
var tLoc = {}, cachedtLoc = {};
var cLoc = {}, cachedcLoc = {};
var inventory = {};
var playerInfo = {};
var pokedex = {};
var bagPokemon = {};
var bagItems = {};
var bagCandy = {};
var emptyDex = [];
var cInfo = {};
var catchable = {};
var pokemonArray = {};


function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: {
            lat: center_lat,
            lng: center_lng
        },
        zoom: 16,
        fullscreenControl: true,
        streetViewControl: false,
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            position: google.maps.ControlPosition.RIGHT_TOP,
            mapTypeIds: [
                google.maps.MapTypeId.ROADMAP,
                google.maps.MapTypeId.SATELLITE
            ]
        },
    });

    setTimeout(function () {
        placeTrainer();
        addCatchable();
        updateInventory();
        setTimeout(function () {
            setInterval(updateTrainer, 1000);
            setInterval(addCatchable, 1000);
        }, 5000);
    }, 5000);

    console.log("Initializing map.");
}

function placeTrainer() {
    loadJSON('location.json',
        function (data) {
            tLoc = data;
            map.setZoom(16);
            map.panTo({
                lat: parseFloat(tLoc.lat),
                lng: parseFloat(tLoc.lng)
            });
        },
        function (xhr) {
            console.error(xhr);
        }
    );

    console.log("New Marker: Trainer - " + tLoc.lat + ", " + tLoc.lng);
    tMarker = new google.maps.Marker({
        map: map,
        position: {lat: parseFloat(tLoc.lat), lng: parseFloat(tLoc.lng)},
        icon: "image/trainer-icon.png"
    });
}

function updateTrainer() {
    loadJSON('location.json',
        function (data) {
            tLoc = data;
            map.panTo({lat: parseFloat(tLoc.lat), lng: parseFloat(tLoc.lng)});
        },
        function (xhr) {
            console.error(xhr);
        }
    );
    if (tLoc.lat === cachedtLoc.lat && tLoc.lng === cachedtLoc.lng) return;
    cachedtLoc = tLoc;
    console.log("Move Marker: Trainer - " + tLoc.lat + ", " + tLoc.lng);
    tMarker.setPosition({lat: parseFloat(tLoc.lat), lng: parseFloat(tLoc.lng)});
}

function addCatchable() {
    loadJSON('catchable.json',
        function (data) {
            cInfo = data;
        },
        function (xhr) {
            console.error(xhr);
        }
    );
    loadJSON('pokemondata.json',
        function (data) {
            pokemonArray = data;
        },
        function (xhr) {
            console.error(xhr);
        }
    );
    if (cInfo['latitude'] != undefined) {
        if (cMarker == undefined) {
            console.log("New Marker: Catchable Pokemon - " + parseFloat(cInfo['latitude']) + ", " + parseFloat(cInfo['longitude']));
            cMarker = new google.maps.Marker({
                map: map,
                position: {lat: parseFloat(cInfo['latitude']), lng: parseFloat(cInfo['longitude'])},
                icon: "image/icons/" + cInfo['pokemon_id'] + ".png"
            });
        }
        console.log("Update Marker: Catchable Pokemon - " + parseFloat(cInfo['latitude']) + ", " + parseFloat(cInfo['longitude']));
        cMarker.setPosition({lat: parseFloat(cInfo['latitude']), lng: parseFloat(cInfo['longitude'])});
        cMarker.setIcon("image/icons/" + cInfo['pokemon_id'] + ".png");
    }
    if (cInfo['latitude'] == undefined && cMarker != undefined) {
        cMarker.setIcon("image/icons/blank.png");
    }
}

function updateInventory() {
    loadJSON('info.json',
        function (data) {
            inventory = data;
            playerInfo = filter(inventory, 'player_stats');
            pokedex = filter(inventory, 'pokedex_entry');
            bagPokemon = filter(inventory, 'pokemon_data');
        },
        function (xhr) {
            console.error(xhr);
        }
    );
}

function filter(arr, search) {
    var filtered = [];
    for (i = 0; i < arr.length; i++) {
        if (arr[i].inventory_item_data[search] != undefined) {
            filtered.push(arr[i]);
        }
        ;
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

function loadJSON(path, success, error) {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                if (success)
                    success(JSON.parse(xhr.responseText.replace(/\bNaN\b/g, "null")));
            } else {
                if (error)
                    error(xhr);
            }
        }
    };
    xhr.open("GET", path, true);
    xhr.send();
}