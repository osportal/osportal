$("#manager,#user,#role,#head,#ltype,#country,#site,#public_holiday_group,#entt,#authoriser,#db_name,#reg_user_country,#reg_user_role").select2({
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
$("#approvers,#members,#department,#absence_types,#permissions").select2({
    multiple: true,
    tags: true,
    width: '100%'
});
