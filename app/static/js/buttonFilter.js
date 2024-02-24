var tableTitle = document.getElementById("tableTitle");
var btnContainer = document.getElementById("myBtnContainer");
var btns = btnContainer.getElementsByClassName("btn");

for (var i = 0; i < btns.length; i++) {
  btns[i].addEventListener("click", function(){
    var current = document.getElementsByClassName("active");
    current[0].className = current[0].className.replace(" active", "");
    this.className += " active";
  });
}

filterSelection("questions");
function filterSelection(type){
    var x, i;
    x = document.getElementsByClassName("filterDiv");
    if(type==="all") tableTitle.innerHTML = "<strong>All</strong>"
    for (i = 0; i < x.length; i++) {
            RemoveClass(x[i], "show");
            if (x[i].className.indexOf(type) > -1) AddClass(x[i], "show");
          }
	if(type==="questions"){
		tableTitle.innerHTML = "<strong>Posts</strong>";
	}
	else if (type==="answers"){
		tableTitle.innerHTML = "<strong>Comments</strong>";
	}

}
function AddClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    if (arr1.indexOf(arr2[i]) == -1) {
      element.className += " " + arr2[i];
    }
  }
}

// Hide elements that are not selected
function RemoveClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    while (arr1.indexOf(arr2[i]) > -1) {
      arr1.splice(arr1.indexOf(arr2[i]), 1);
    }
  }
  element.className = arr1.join(" ");
}
