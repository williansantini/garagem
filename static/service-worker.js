self.addEventListener('push', function(event) {
    const data = event.data.json(); // Os dados que enviamos do Flask

    const title = data.title;
    const options = {
        body: data.body,
        icon: '/static/icon-192.png', // Ícone que aparece na notificação
        badge: '/static/icon-192.png'
    };

    event.waitUntil(self.registration.showNotification(title, options));
});