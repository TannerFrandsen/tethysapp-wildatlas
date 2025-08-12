// ---- Utility Functions ----

function formatToLocalISO8601(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    const offsetMinutes = date.getTimezoneOffset();
    const offsetSign = offsetMinutes <= 0 ? '+' : '-';
    const absOffsetMinutes = Math.abs(offsetMinutes);
    const offsetHours = String(Math.floor(absOffsetMinutes / 60)).padStart(2, '0');
    const offsetMins = String(absOffsetMinutes % 60).padStart(2, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${offsetSign}${offsetHours}:${offsetMins}`;
}

// ---- DOM Elements ----
const dateInput = document.getElementById('date_display');
const dateError = document.getElementById('date_error');

const latInput = document.getElementById('latitude');
const latError = document.getElementById('lat_error');

const lonInput = document.getElementById('longitude');
const lonError = document.getElementById('lon_error');

const submitBtn = document.querySelector('button[type="submit"]');

// ---- Validation Functions ----

function validateDate() {
    const value = dateInput.value;
    if (!value) {
        dateError.style.display = 'none';
        return false;
    }
    const date = new Date(value);
    const now = new Date();
    if (date > now) {
        dateError.textContent = 'Date and time cannot be in the future.';
        dateError.style.display = 'block';
        return false;
    }
    dateError.style.display = 'none';
    return true;
}

function validateLat() {
    const value = parseFloat(latInput.value);
    if (isNaN(value) || value < -90 || value > 90) {
        latError.textContent = 'Latitude must be between -90 and 90.';
        latError.style.display = 'block';
        return false;
    }
    latError.style.display = 'none';
    return true;
}

function validateLon() {
    const value = parseFloat(lonInput.value);
    if (isNaN(value) || value < -180 || value > 180) {
        lonError.textContent = 'Longitude must be between -180 and 180.';
        lonError.style.display = 'block';
        return false;
    }
    lonError.style.display = 'none';
    return true;
}

function validateForm() {
    const dateValid = validateDate();
    const latValid = validateLat();
    const lonValid = validateLon();
    const valid = dateValid && latValid && lonValid;
    submitBtn.disabled = !valid;
    return valid;
}

// ---- Event Listeners ----

// Real-time validation
dateInput.addEventListener('input', validateForm);
latInput.addEventListener('input', validateForm);
lonInput.addEventListener('input', validateForm);


// On form submit: final validation and set hidden input
document.getElementById('sightingForm').addEventListener('submit', (e) => {
    if (!validateForm()) {
        e.preventDefault();
        alert('Please fix errors before submitting.');
        return;
    }

    let dateToFormat;
    if (dateInput.value) {
        dateToFormat = new Date(dateInput.value);
    } else {
        dateToFormat = new Date();
    }
    document.getElementById('date_time').value = formatToLocalISO8601(dateToFormat);
});

// ---- Other Functions ----

function setSightingTimeNow() {
    const now = new Date();
    dateInput.value = formatToLocalISO8601(now).slice(0, 16);
    validateForm();
}

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            latInput.value = position.coords.latitude;
            lonInput.value = position.coords.longitude;
            validateForm();
        }, function() {
            alert('Unable to retrieve your location.');
        });
    } else {
        alert('Geolocation is not supported by this browser.');
    }
}

function selectAnimal(animalId, animalName, logoPath) {
    document.getElementById('animalId').value = animalId;
    document.getElementById('selectedAnimalText').innerHTML = `
        <img src="${logoPath}" alt="${animalName} icon" style="width:24px; height:24px; margin-right:8px;">
        ${animalName}
    `;
}

// ---- Initialize ----
document.addEventListener('DOMContentLoaded', () => {
    setSightingTimeNow();
    validateForm();
});