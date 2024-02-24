// Get the modal
var modal = document.getElementById("imageModal");

// Get the image and insert it inside the modal - use its "alt" text as a caption
var img = document.getElementById("profileImg");
var modalImg = document.getElementById("img01");
var captionText = document.getElementById("caption");
img.onclick = function(){
  	modal.style.display = "block";
  	modalImg.src = this.src;
  	captionText.innerHTML = this.alt;
	// when modal is open if a user clicks anywhere outside the img it will close
  	modal.addEventListener('click',function(event){
		if (event.target.id != "img01"){
  			modal.style.display="none";
			}
  	});
}

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() { 
	modal.style.display = "none";
}
