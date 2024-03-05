$("#manager,#user,#role,#ltype,#country,#authoriser,#reg_user_country,#reg_user_role").select2({
    tags: true,
    width: '100%'
});
/*
$("#departments").select2({
    multiple: false,
    tags: true,
    width: '100%'
});
*/
$("#approvers,#members,#department,#permissions").select2({
    multiple: true,
    tags: true,
    width: '100%'
});
