!function() {
    let username = localStorage.getItem("username")
    if (username == null) {
        while (username == null || username.replace(/ /g, '') === '')
            username = prompt("inserisci il tuo nome")
        localStorage.setItem("username", username)
    }


    const socket = io(document.location.host)
    socket.on('receive', appendMessage);
    socket.on('error', (message) => alert(message))

    const input = document.getElementById('message')
    const container = document.getElementById('room')

    input.addEventListener('keypress', (event) => {
        if (event.keyCode === 13) {
            if (input.value.replace(/ /g, '').length === 0) return;
            event.preventDefault();
            socket.emit('message', {'from': username, 'value':input.value})
            input.value = '';
        }
    });
    window.addEventListener('load', async _ => {
        // let response = await fetch('/get');
        // let data = await response.json();
        // data.forEach(appendMessage)
        container.scrollTop = container.scrollHeight;
    });

    function messageToNode(message) {
        let span = document.createElement('div');
        let b = document.createElement('b');
        b.append(document.createTextNode(message['from']+': '));
        span.append(b)
        span.append(document.createTextNode(message['value']));
        return span;
    }

    function appendMessage(message) {
        container.append(messageToNode(message));
        container.scrollTop = container.scrollHeight;
    }
}();