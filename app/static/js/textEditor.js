ClassicEditor
    .create( document.querySelector( '#ckeditor' ),{
        extraPlugins: [ MentionCustomization ],
        mention: {
            dropdownLimit: 5,
            feeds: [
                {
                    marker: '@',
                    feed: getFeedItems,
                    itemRenderer: customItemRenderer,
                    minimumCharacters: 0
                }
            ]
        },
        mediaEmbed: {
               previewsInData:true
        },
    })
    .then(editor => {
        window.editor = editor;
    })
    .catch( error => {
        console.error( error.stack );
    } );


function SetMentionData(editor, obj_id, obj_username){
    //editor.setData('<a class="mention" data-mention="@{obj.user.username}" data-user-id="{obj.user.id}" href="/user/testuser">@{obj.user.username}</a>&nbsp;');
    document.getElementById('editor-form').scrollIntoView({top: -600});
    editor.setData('<a class="mention" data-mention="' + `${obj_username}` + '" data-user-id="' + `${obj_id}` + '" href="/user/' + `${obj_id}`+ '">@' + `${obj_username}` + '</a>&nbsp;');
    editor.focus();
    editor.model.change( writer => {
        writer.setSelection( writer.createPositionAt( editor.model.document.getRoot(), 'end' ) );
    });
}

function MentionCustomization( editor ) {
    // The upcast converter will convert view <a class="mention" href="" data-user-id="">
    // elements to the model 'mention' text attribute.
    editor.conversion.for( 'upcast' ).elementToAttribute( {
        view: {
            name: 'a',
            key: 'data-mention',
            classes: 'mention',
            attributes: {
                href: true,
                'data-user-id': true
            }
        },
        model: {
            key: 'mention',
            value: viewItem => {
                // The mention feature expects that the mention attribute value
                // in the model is a plain object with a set of additional attributes.
                // In order to create a proper object use the toMentionAttribute() helper method:
                const mentionAttribute = editor.plugins.get( 'Mention' ).toMentionAttribute( viewItem, {
                    // Add any other properties that you need.
                    link: viewItem.getAttribute( 'href' ),
                    userId: viewItem.getAttribute( 'data-user-id' )
                } );

                return mentionAttribute;
            }
        },
        converterPriority: 'high'
    } );

    // Downcast the model 'mention' text attribute to a view <a> element.
    editor.conversion.for( 'downcast' ).attributeToElement( {
        model: 'mention',
        view: ( modelAttributeValue, { writer } ) => {
            // Do not convert empty attributes (lack of value means no mention).
            if ( !modelAttributeValue ) {
                return;
            }

            return writer.createAttributeElement( 'a', {
                class: 'mention',
                'data-mention': modelAttributeValue.id,
                'data-user-id': modelAttributeValue.userId,
                'href': modelAttributeValue.link
            }, {
                // Make mention attribute to be wrapped by other attribute elements.
                priority: 20,
                // Prevent merging mentions together.
                id: modelAttributeValue.uid
            } );
        },
        converterPriority: 'high'
    } );
}

function customItemRenderer( item ) {
    const itemElement = document.createElement( 'span' );

    itemElement.classList.add( 'custom-item' );
    itemElement.id = `mention-list-item-id-${ item.userId }`;
    itemElement.textContent = `${ item.name } `;

    const usernameElement = document.createElement( 'span' );

    usernameElement.classList.add( 'custom-item-username' );
    usernameElement.textContent = item.id;

    itemElement.appendChild( usernameElement );

    return itemElement;
}

function getFeedItems( queryText ) {
// As an example of an asynchronous action, return a promise
// that resolves after a 100ms timeout.
// This can be a server request or any sort of delayed action.
    return new Promise( resolve => {
        setTimeout( () => {
            $.ajax({
                url: endpoint, 
                type: 'GET', 
                success: function(data){
                    modifyData(data)
                }
            })
                    // Filter out the full list of all items to only those matching the query text.
                    //.filter( isItemMatching )
                    // Return 10 items max - needed for generic queries when the list may contain hundreds of elements.
                    //.slice( 0, 10 );
            function isItemMatching( item ) {
              // Make the search case-insensitive.
              const searchString = queryText.toLowerCase();

              // Include an item in the search results if the name or username includes the current user input.
              return (
                  item.name.toLowerCase().includes( searchString ) ||
                  item.id.toLowerCase().includes( searchString )
              );
            }
            function modifyData(itemsToDisplay){
                itemsToDisplay = itemsToDisplay.filter(isItemMatching);
                //itemsToDisplay = itemsToDisplay.slice(0,5);
                resolve( itemsToDisplay );
                }
            
        }, 100 );
    } );
}

function getMentions(){
    editor = window.editor;
    var form = document.getElementById('editor-form');
    
    // create a range spanning the whole document
    const range = editor.model.createRangeIn(editor.model.document.getRoot());
    
    const mentions = [];
    var input;
    
    //iterate through the whole tree in that range (TreeWalker)
    for (const treeWalker of range.getWalker({ignoreElementEnd: true})) {
    
        if (treeWalker.type === 'text') {
            //the item property represents TextProxy which is not instance of node
            const node = treeWalker.item.textNode;
    
            if (node.hasAttribute('mention')) {
                const mention = node.getAttribute('mention');
                if (mention) {
                    mentions.push(mention.userId)
                }
            }
        }
    
    }
    // make sure user mentions array has data before setting it
    if (mentions.length > 0) { 
        input = document.createElement('input');
        input.setAttribute('name', 'user-mentions');
        input.setAttribute('value', mentions);
        input.setAttribute('type', 'hidden');
        form.appendChild(input);
    }
    form.submit();
}
