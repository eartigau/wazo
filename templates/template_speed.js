function $(element) 

{
   return document.getElementById(element); 
} 
var speedTest = {};
  speedTest.pics = null;
 speedTest.map = null;
speedTest.markerClusterer = null;
 speedTest.markers = [];
speedTest.infoWindow = null;
  speedTest.init = function() {
  var latlng = new google.maps.LatLng(  {{ latitude }}   ,  {{ longitude }}  );
   var options = {     'zoom': {{ zoom }},
    'center': latlng,
    'mapId': "cac161ea823b19be"
};
  speedTest.map = new google.maps.Map($('map'), options);
  speedTest.pics = data.photos;

    /*
  var useGmm = document.getElementById('usegmm');
  google.maps.event.addDomListener(useGmm, 'click', speedTest.change);   
  var numMarkers = 264; 
  google.maps.event.addDomListener(numMarkers, 'change', speedTest.change); 
*/

  speedTest.infoWindow = new google.maps.InfoWindow();

  speedTest.showMarkers();
 };
  speedTest.showMarkers = function() 
{
  speedTest.markers = [];
    var type = 0; 
/*   if ($('usegmm').checked) {
    type = 0;   } */    

if (speedTest.markerClusterer) {
    speedTest.markerClusterer.clearMarkers();   }  
  var panel = $('markerlist'); 	  panel.innerHTML = '';  
  var numMarkers = {{ number_markers }}; 
/*$('nummarkers').value;*/ 

  for (var i = 0; i < numMarkers; i++) {

    var titleText = speedTest.pics[i].photo_title;
     if (titleText == '') {
      titleText = 'No title';     } 

    var item = document.createElement('DIV');

    var title = document.createElement('A');

     title.href = '#';

    title.className = 'title';

      title.innerHTML = titleText; 

    item.appendChild(title);  

    var latLng = new google.maps.LatLng(speedTest.pics[i].latitude,
        speedTest.pics[i].longitude);  /*

*    var imageUrl = 'http://chart.apis.google.com/chart?cht=mm&chs=24x32&chco=' +
*        'FFFFFF,008CFF,000000&ext=.png'; */ 

    var imageUrl = 'cartoon.png'; 

    var markerImage = new google.maps.MarkerImage(imageUrl,
        new google.maps.Size(32, 32)); 

    var marker = new google.maps.Marker({
       'position': latLng,
      'icon': markerImage    
 }); 

    var fn = speedTest.markerClickFunction(speedTest.pics[i], latLng);
    google.maps.event.addListener(marker, 'click', fn);
    google.maps.event.addDomListener(title, 'click', fn);
    speedTest.markers.push(marker);
   }    window.setTimeout(speedTest.time, 0);
};  speedTest.markerClickFunction = function(pic, latlng) {

  return function(e) {
     e.cancelBubble = true;
     e.returnValue = false;
    if (e.stopPropagation) 
	{
       e.stopPropagation();
      e.preventDefault();
     }     var title = pic.photo_title;
    var url = pic.photo_url;     var fileurl = pic.photo_file_url; 
    var infoHtml = '<div class="info"><h10>' + title +'<br>'+url +'</h10></br></div>';
    speedTest.infoWindow.setContent(infoHtml);
    speedTest.infoWindow.setPosition(latlng);
    speedTest.infoWindow.open(speedTest.map);

   };
 };  

speedTest.change = function() {   speedTest.showMarkers(); }; 

	speedTest.time = function() {
    $('timetaken').innerHTML = '';
    speedTest.markerClusterer = new MarkerClusterer(speedTest.map, speedTest.markers);
  $('timetaken').innerHTML = '' ;

  };  
