var pluralize = function (word, count) {
  if (count === 1) { return word; }

  return word + 's';
};

var bulkSelectors = {
  'selectAll': '#select_all',
  'checkedItems': '.checkbox-item',
  'colheader': '.col-header',
  'selectedRow': 'warning',
  'updateScope': '#scope',
  'bulkActions': '#bulk_actions'
};

$(document).ready(function() {
  // Bulk delete.
    /*
  $('body').on('change', bulkSelectors.checkedItems, function () {
    var checkedSelector = bulkSelectors.checkedItems + ':checked';
    var itemCount = $(checkedSelector).length;
    var pluralizeItem = pluralize('item', itemCount);
    var scopeOptionText = itemCount + ' selected ' + pluralizeItem;

    if ($(this).is(':checked')) {
      $(this).closest('tr').addClass(bulkSelectors.selectedRow);

      $(bulkSelectors.colheader).hide();
      $(bulkSelectors.bulkActions).show();
    }
    else {
      $(this).closest('tr').removeClass(bulkSelectors.selectedRow);

      if (itemCount === 0) {
        $(bulkSelectors.bulkActions).hide();
        $(bulkSelectors.colheader).show();
      }
    }

    $(bulkSelectors.updateScope + ' option:first').text(scopeOptionText);
  });
  */

    $('body').on('change', bulkSelectors.selectAll, function () {
        var checkedStatus = this.checked;
    
        $(bulkSelectors.checkedItems).each(function () {
          $(this).prop('checked', checkedStatus);
          $(this).trigger('change');
        });
    });
    /* Provide modal title for bulk delete by getting value
    from the scope option in the bulkdeleteform */
    $('#bulkDeleteModal').on('click', function(e) {
      let modalLabel = document.getElementById('bulkDeleteLabel');
      const scopeInfo = document.getElementById("scope").textContent; 
      modalLabel.innerHTML = "Delete " + scopeInfo;
    });
    
    /* add an event listener to all forms. If a form is submitted get a list of values
     * from the checkeditems, push them to an array and add them to a hidden element
     * in the selected form. Finally submit the form */
    document.querySelectorAll('.bulkforms').forEach(item => {
        item.addEventListener('submit', event => {
            event.preventDefault();
            appendHiddenInput(item);
      });
    });
    document.getElementById('export-form').addEventListener('submit', function(event) {
        event.preventDefault();
        appendHiddenInput(this);
    });
});

function appendHiddenInput(item){
    // Make sure to remove previous hiddeninputs
    item.querySelectorAll('[name=checked-items]').forEach(e => e.remove());
    var array = []
    var checkboxes = document.querySelectorAll('input[type=checkbox]:checked')
    
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].value === 'on'){
            /* ignore the selected all value */
        } else {
          array.push(checkboxes[i].value)
        }
    }
    if (array.length === 0){
        flashError();
    } else {
        /* if array is not empty */
        console.log(item);
        var hiddenInput = document.createElement('input');
        hiddenInput.setAttribute('type', 'hidden');
        hiddenInput.setAttribute('name', 'checked-items');
        hiddenInput.setAttribute('value', array);
        item.appendChild(hiddenInput)
        item.submit();
    }
}

function flashError(){
    const modal = `
    <div class="modal fade" id="exampleModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="exampleModalLabel">Error</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            You need to select at least one item
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
    `;
    document.getElementById('flash-messages').innerHTML = modal;
}
/* Below function is called from user/index.html onclick. 
 * This function checks at least one user/checkbox has been ticked. 
 * Takes a data-target id.
 * If there is at least one checked item in the array, show the target modal */
function checkArrayLen(target){
        var array = [];
        var checkboxes = document.querySelectorAll('input[type=checkbox]:checked');
        for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].value === 'on'){
                /* ignore the selected all value */
            } else {
                array.push(checkboxes[i].value);
            }
        }
        /* if array is not empty */
        if (array.length === 0){
            flashError();
            $("#exampleModal").modal('show');
        } else {
            modalItems = document.getElementById('modal-checked-items-count');
            if (modalItems) {
                modalItems.innerHTML = array.length;
            }
            $(target).modal('show');
        }
}
