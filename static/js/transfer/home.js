// This JavaScript file is responsible for handling the modal for entering the access token
// and redirecting the user to the appropriate URL with the token as a query parameter.
// It also handles the modal's open and close functionality.
// Open modal when the button is clicked
document.getElementById("openModalButton").onclick = function() {
    openModal();
};
// Close modal when the close button is clicked
function openModal() {
    document.getElementById("tokenModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("tokenModal").style.display = "none";
}

function submitToken() {
    const token = document.getElementById("accessTokenInput").value;
    if (token.trim() !== "") {
        const url = "/transfers/docs?access_token=" + encodeURIComponent(token);
        window.location.href = url;
    } else {
        alert("Please enter a valid token.");
    }
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById("tokenModal");
    if (event.target === modal) {
        closeModal();
    }
};
