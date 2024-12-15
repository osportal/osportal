function flash_message(error){
    const box = `
    <div class="alert alert-danger">${error}</div>
    `;
    document.getElementById('flash-messages').innerHTML = box;
}

function celery_not_running_notification(notification) {
    let no_notifications = document.getElementById("overview-no-notifications");
    let notifications = document.querySelector(".overview-notifications");

    // replace the no notifications notice with ours
    if (no_notifications == null) {
        no_notifications.outerHTML = notification;
    } else {
        notifications.innerHTML = notification;
    }
}


function calculate_days_for_user(endpoint, ltype_endpoint){
    const ltype = fetch(ltype_endpoint, 
        {method: "GET", headers: {"Content-Type": "application/json", } }).then((response) => response.json())

    const execute = () => { 
        ltype.then((ltype_value) => { 
            fetch(endpoint, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                }
            })
            .then((response) => response.json())
            .then((data) => {
                daysStr = data;
                if (data.status){
                    // for invalid date format e.g. too many digits for year
                    if (data.status === 400){
                        document.getElementById('calculate-days-val').innerHTML = data.message;
                    }
                } else {
                    // check max days for leave type max days length
                    if (parseFloat(data) > parseFloat(ltype_value.max_days)){
                        document.getElementById('calculate-days-val').innerHTML = "Exceeds the maximum length of days you can request in one occurrence"
                    } 
                    // if selected leave type is deductable, validate daysLeft
                    else if (ltype_value.deduct === 'True'){
                        /* data and daysLeft vars are strings, 
                        therefore must be converted in order to compare */
                        if (parseFloat(data) > parseFloat(daysLeft)){
                            document.getElementById('calculate-days-val').innerHTML = "You don't have enough allowance for this request";
                        }
                        else if ( (parseFloat(data) === 0) || (parseFloat(data) <= 0) ){
                            // if its 0 days then usually its because the user is not scheduled to work i.e weekend,
                            // public holiday or end date before start date
                            document.getElementById('calculate-days-val').innerHTML = "You are not scheduled to work on the dates that you chose";
                            // don't enable btn if 0 days
                        } else {
                            document.getElementById('calculate-days-val').innerHTML = daysStr;
                            enableSubmitBtn();
                        }
                    }
                    // else ltype_value.deduct == False
                    else {
                        if ( (parseFloat(data) === 0) || (parseFloat(data) <= 0) ){
                            // if its 0 days then usually its because the user is not scheduled to work i.e weekend,
                            // public holiday or end date before start date
                            document.getElementById('calculate-days-val').innerHTML = "You are not scheduled to work betweeen the dates that you chose";
                        } else {
                            document.getElementById('calculate-days-val').innerHTML = daysStr;
                            enableSubmitBtn();
                        }
                    }
                } // end of data status if statement
            })
            .catch((error) => {
                //flash_message(error);
                document.getElementById('calculate-days-val').innerHTML = error;
            });
        }); /* end of deductable.then function */
    }; // end of execute function
    execute();
}

function check_overview_status(endpoint, notification, running, not_running) {
    let celerystatus = document.getElementById("celery-status");
    fetch(endpoint, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        }
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.celery_running) {
                celerystatus.outerHTML = running;
            } else {
                celerystatus.outerHTML = not_running;
                flash_message(notification);
            }
        })
        .catch((error) => {
            flash_message(error);
        });
}

function checkAuthoriserExists(target){
    $(target).modal('show');
}
