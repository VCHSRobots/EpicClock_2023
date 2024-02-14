var overlay = null;

function refreshTime() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/refresh_time", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    showLoading(true);

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4){
            showLoading(false);
        }
        if (xhr.readyState == 4 && xhr.status == 200) {
            var data = JSON.parse(xhr.responseText);

            document.getElementById("h").style.color = data.digit_color;
            document.getElementById("m").style.color = data.digit_color;
            document.getElementById("colon").style.color = data.colon_color;
            document.getElementById("s").style.color = data.seconds_color;
            document.getElementById("am").style.color = data.ampm_color;
            
            document.getElementById("digitColorPicker").value = data.digit_color;
            document.getElementById("messageColor").value = data.digit_color;
            document.getElementById("colonColorPicker").value = data.colon_color;
            document.getElementById("secondsColorPicker").value = data.seconds_color;
            document.getElementById("ampmColorPicker").value = data.ampm_color;
            document.getElementById("brightnessPicker").value = data.brightness;

            document.getElementById("h").innerText = data.h;
            document.getElementById("m").innerText = data.m;
            document.getElementById("s").innerText = data.s;
            document.getElementById("am").innerText = data.am;
            
            renderSecondsBar(parseInt(data.s))
            
        }
    };

    xhr.send();
}

function renderSecondsBar(currentSecond){
    var percentage =  currentSecond / 60 * 100;

    var secondsIndicatorLine = document.getElementById("secondsIndicatorLine");
    secondsIndicatorLine.style.width = percentage + "%";
    secondsIndicatorLine.style.backgroundColor = document.getElementById("s").style.color;
}

function submitForm() {
    var digit_color = document.getElementById("digitColorPicker").value;
    var colon_color = document.getElementById("colonColorPicker").value;
    var seconds_color = document.getElementById("secondsColorPicker").value;
    var ampm_color = document.getElementById("ampmColorPicker").value;
    var brightness = document.getElementById("brightnessPicker").value;

    var xhr = new XMLHttpRequest();
    var queryParams = "digit_color=" + digit_color.slice(1) +
        "&colon_color=" + colon_color.slice(1) +
        "&seconds_color=" + seconds_color.slice(1) +
        "&ampm_color=" + ampm_color.slice(1) +
        "&brightness=" + brightness;

    xhr.open("POST", "/submit?" + queryParams, true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var data = JSON.parse(xhr.responseText);

            document.getElementById("h").style.color = data.digit_color;
            document.getElementById("m").style.color = data.digit_color;
            document.getElementById("colon").style.color = data.colon_color;
            document.getElementById("s").style.color = data.seconds_color;
            document.getElementById("am").style.color = data.ampm_color;
            document.getElementById("brightnessPicker").value = data.brightness;

            document.getElementById("h").innerText = data.h;
            document.getElementById("m").innerText = data.m;
            document.getElementById("s").innerText = data.s;
            document.getElementById("am").innerText = data.am;
            
            renderSecondsBar(parseInt(data.s))
        }
    };

    xhr.send("digit_color=" + digit_color.slice(1) +
        "&colon_color=" + colon_color.slice(1) +
        "&seconds_color=" + seconds_color.slice(1) +
        "&ampm_color=" + ampm_color.slice(1) +
        "&brightness=" + brightness);

    return false;
}

function showLoading(onOff) {
    var body = document.body;

    if (onOff) {
        overlay = document.createElement("div");
        overlay.className = "overlay";
        body.appendChild(overlay);
    } else {
        body.removeChild(overlay);
    }
}

function sendMessage() {
    showLoading(true);

    var send_message_color = document.getElementById("messageColor").value;
    var message_text = document.getElementById("sendMessageText").value;
    
    // Retrieve the selected text size option
    var text_size_radio_buttons = document.getElementsByName("textSize");
    var selected_text_size = "";
    for (var i = 0; i < text_size_radio_buttons.length; i++) {
        if (text_size_radio_buttons[i].checked) {
            selected_text_size = text_size_radio_buttons[i].value;
            break;
        }
    }
    
    var xhr = new XMLHttpRequest();
    var queryParams = "message_color=" + send_message_color.slice(1) +
                      "&message=" + encodeURIComponent(message_text) +
                      "&text_size=" + selected_text_size; 

    xhr.open("POST", "/send_message?" + queryParams, true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4) {
            showLoading(false);
            if (xhr.status == 200) {
                // Handle the response here if needed
            }
        }
    };

    xhr.send(queryParams);

    return false;
}

function playRainbow() {
    showLoading(true);
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/play_rainbow", true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4){
            showLoading(false);
        }
    };
    xhr.send();
}

function toggleSecondsStyle() {
    showLoading(true);
    var xhr = new XMLHttpRequest(); // Fix the typo here
    xhr.open("POST", "seconds_style", true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4){
            showLoading(false);
        }
    };
    xhr.send();
}

function updateBrightnessLabel() {
    var sliderValue = parseFloat(document.getElementById("brightnessPicker").value);
    var brightness = Math.pow(10, sliderValue) / 10;
    submitForm();
}

function getDeviceInfo(){
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/get_device_info", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    showLoading(true);

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4){
            showLoading(false);
        }
        if (xhr.readyState == 4 && xhr.status == 200) {
            document.getElementById("deviceInfoResult").value = xhr.responseText;
        }
    };

    xhr.send();
}

function getTimeCheckRecords() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/get_time_check_records", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    showLoading(true);

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4){
            showLoading(false);
        }
        if (xhr.readyState == 4 && xhr.status == 200) {
            document.getElementById("timeCheckRecordsResult").value = xhr.responseText;
        }
    };

    xhr.send();
}

function getPowerRecords() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/get_power_records", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    showLoading(true);

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4){
            showLoading(false);
        }
        if (xhr.readyState == 4 && xhr.status == 200) {
            document.getElementById("powerRecordsResult").value = xhr.responseText;
        }
    };

    xhr.send();
}

function getErrorRecords() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/get_error_log", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    showLoading(true);

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4){
            showLoading(false);
        }
        if (xhr.readyState == 4 && xhr.status == 200) {
            document.getElementById("errorRecordsResult").value = xhr.responseText;
        }
    };

    xhr.send();
}

document.getElementById("digitColorPicker").addEventListener("input", submitForm);
document.getElementById("colonColorPicker").addEventListener("input", submitForm);
document.getElementById("secondsColorPicker").addEventListener("input", submitForm);
document.getElementById("ampmColorPicker").addEventListener("input", submitForm);
document.getElementById("brightnessPicker").addEventListener("input", updateBrightnessLabel);

window.onload = function() {
    refreshTime();
};

