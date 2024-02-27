var deleteUser = document.getElementById('delete-user-confirm');
deleteUser.addEventListener('click', function() {
    var deleteWarningP = document.getElementById('modal-warning-info');
    deleteWarningP.classList.add('p-2');// cannot add whitespace to class
    deleteWarningP.classList.add('bg-warning');
    deleteWarningP.innerHTML = 'We do not recommend deleting users, instead make them inactive.';
});
