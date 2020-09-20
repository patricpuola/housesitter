document.addEventListener('DOMContentLoaded', function(){
    
    image_selects = document.getElementsByClassName('image_select');
    for (i = 0; i < image_selects.length; i++){
        image_selects[i].addEventListener('mouseenter', function(e){
            let image_id = this.getAttribute('data-image-id');
            let listing_id = this.getAttribute('data-listing-id');
            let all_images = document.getElementById('listing_images_'+listing_id).children
            
            for (j = 0; j < all_images.length; j++){
                all_images[j].setAttribute('data-show','false')
            }
            document.getElementById('image_'+image_id).setAttribute('data-show','true');
            
            let all_selectors = document.getElementById('listing_selector_'+listing_id).children;
            for (j = 0; j < all_selectors.length; j++){
                all_selectors[j].innerHTML = "&#9675;";
            }

            this.innerHTML = "&#9679;";
        });
    }
});