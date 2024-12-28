// Excludes first and last column of row (selectable and edit/delete buttons)
$(document).ready(function($) {
    $('tbody').on('click', 'tr td:not(:first-child,:last-child)', function() {
        window.location = $(this).parent().data("href");
    });
});
