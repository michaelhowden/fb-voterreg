$(function() {
    function receiveMessage(event) {
        if (event.origin != "widget.internetvotes.org") {
            return;
        }
        window.location.assign("/pledge?from_widget=true")
    }

    if (window.addEventListener) {
        window.addEventListener("message", receiveMessage, false);
    } else if (window.attachEvent) {
        window.attachEvent("message", receiveMessage);
    }
});