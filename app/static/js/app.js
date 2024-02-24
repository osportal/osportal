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


function calculate_days_for_user(endpoint, etype_endpoint){
    const etype = fetch(etype_endpoint, 
        {method: "GET", headers: {"Content-Type": "application/json", } }).then((response) => response.json())

    const execute = () => { 
        etype.then((etype_value) => { 
            console.log(etype_value);
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
                    console.log(data.status);
                    // for invalid date format e.g. too many digits for year
                    if (data.status === 400){
                        document.getElementById('calculate-days-val').innerHTML = data.message;
                    }
                } else {
                    // check max days for event type max days length
                    if (parseFloat(data) > parseFloat(etype_value.max_days)){
                        document.getElementById('calculate-days-val').innerHTML = "Exceeds the maximum length of days you can request in one occurrence"
                    } 
                    // if selected event type is deductable, validate allowance
                    else if (etype_value.deduct === 'True'){
                        /* data and allowance vars are strings, 
                        therefore must be converted in order to compare */
                        if (parseFloat(data) > parseFloat(allowance)){
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
                    // else etype_value.deduct == False
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

function hideCalendar(){
    $("#calendar-container").toggle();
}


function checkAuthoriserExists(target){
    /* if array is not empty 
    if (authoriser === 'None' || authoriser == ''){
        const message = 'You do not have an authoriser assigned. Contact administrator for help.';
        flash_message(message);
    }
    else if (allowance === 'None' || allowance <= 0){
    	const message = 'You do not have any leave allowance. Contact administrator for help.';
        flash_message(message);
    }
    else {*/
        $(target).modal('show');
    //}
}
