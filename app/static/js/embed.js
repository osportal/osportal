document.querySelectorAll( 'div[data-oembed-url]' ).forEach( element => {
    // Discard the static media preview from the database (empty the <div data-oembed-url="...">).
    while ( element.firstChild ) {
        element.removeChild( element.firstChild );
    }

    // Create the <a href="..." class="embedly-card"></a> element that Embedly uses
    // to discover the media.
    const anchor = document.createElement( 'a' );

    anchor.setAttribute( 'href', element.dataset.oembedUrl );
    anchor.className = 'embedly-card';

    element.appendChild( anchor );
} );
document.querySelectorAll( 'oembed[url]' ).forEach( element => {
    // Create the <a href="..." class="embedly-card"></a> element that Embedly uses
    // to discover the media.
    const anchor = document.createElement( 'a' );

    anchor.setAttribute( 'href', element.getAttribute( 'url' ) );
    anchor.className = 'embedly-card';

    element.appendChild( anchor );
} );
