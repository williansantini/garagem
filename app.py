<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Status da Garagem</title>
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#1c1c1e"/>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div id="status-box">
        <h1 id="status-text">Carregando...</h1>
        <p id="status-details"></p>
    </div>

    <div id="feira-aviso" style="display: none;">
        <p><strong>Aviso:</strong> Hoje ou amanhã é dia de feira! Não estacione na Rua Santos ou na Rua Tupi.</p>
    </div>

    <div id="actions">
        <button class="eu-audi" onclick="tryToOccupy('Willian', 'Audi')">Willian (Audi)</button>
        <button class="nicolas-fit" onclick="tryToOccupy('Nicolas', 'Fit')">Nicolas (Fit)</button>
        <button class="angelica-audi" onclick="tryToOccupy('Angelica', 'Audi')">Angelica (Audi)</button>
        <button class="angelica-fit" onclick="tryToOccupy('Angelica', 'Fit')">Angelica (Fit)</button>
        <button class="saida" onclick="openSaidaModal()">Liberei a Garagem</button>
    </div>

    <div id="saida-modal" class="modal-overlay" onclick="closeSaidaModal()"><div class="modal-content" onclick="event.stopPropagation();"><h3>Quem está saindo?</h3><div class="modal-actions"><button class="eu-audi" onclick="confirmarSaida('Willian')">Willian</button><button class="angelica-audi" onclick="confirmarSaida('Angelica')">Angelica</button><button class="nicolas-fit" onclick="confirmarSaida('Nicolas')">Nicolas</button><button class="btn-close" onclick="closeSaidaModal()">Cancelar</button></div></div></div>
    <div id="warning-modal" class="modal-overlay" onclick="closeWarningModal()"><div class="modal-content" onclick="event.stopPropagation();"><h3 id="warning-modal-text">A vaga já está ocupada.</h3><div class="modal-actions"><button id="force-occupy-btn" class="btn-force-occupy">Liberar e Ocupar</button><button class="btn-close" onclick="closeWarningModal()">Voltar</button></div></div></div>
    <div style="margin-top: 20px; text-align: center;"><button id="notifications-btn" style="padding: 15px; font-size: 1em; background-color: var(--surface-color); color: var(--primary-text-color); border: none; border-radius: 12px;">Ativar Notificações</button></div>

    <div id="apod-container" style="display: none;">
        <h4 id="apod-title"></h4>
        <img id="apod-image" src="" alt="Imagem Astronômica do Dia">
        <p id="apod-explanation"></p>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const statusBox = document.getElementById('status-box');
            const statusText = document.getElementById('status-text');
            const statusDetails = document.getElementById('status-details');
            const saidaModal = document.getElementById('saida-modal');
            const warningModal = document.getElementById('warning-modal');
            let currentStatus = {};
            let lastStatusString = "";

            window.updateStatusDisplay = function(data) {
                const newStatusString = JSON.stringify(data);
                if (newStatusString === lastStatusString) return; 
                lastStatusString = newStatusString;

                currentStatus = data;
                statusText.textContent = `GARAGEM ${data.status}`;
                if (data.status === 'OCUPADA') {
                    statusDetails.textContent = `Por ${data.pessoa} com o ${data.carro} desde ${data.timestamp}`;
                    statusBox.className = 'ocupada';
                } else {
                    statusDetails.textContent = `Liberada por último por ${data.pessoa} em ${data.timestamp}`;
                    statusBox.className = 'livre';
                }
            }

            async function sendUpdateToServer(pessoa, carro, acao) {
                await fetch('/api/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pessoa, carro, acao })
                });
                fetchLatestStatus();
            }
            
            window.tryToOccupy = function(novaPessoa, novoCarro) {
                if (currentStatus.status === 'LIVRE' || !currentStatus.status) {
                    sendUpdateToServer(novaPessoa, novoCarro, 'ENTRADA');
                } else {
                    const warningText = document.getElementById('warning-modal-text');
                    warningText.textContent = `Vaga ocupada por ${currentStatus.pessoa}. Deseja continuar?`;
                    const forceButton = document.getElementById('force-occupy-btn');
                    forceButton.onclick = () => forceOccupy(novaPessoa, novoCarro);
                    openWarningModal();
                }
            }
            
            function forceOccupy(novaPessoa, novoCarro) {
                sendUpdateToServer(currentStatus.pessoa, currentStatus.carro, 'SAIDA');
                setTimeout(() => {
                    sendUpdateToServer(novaPessoa, novoCarro, 'ENTRADA');
                }, 250);
                closeWarningModal();
            }
            
            window.openSaidaModal = function() { saidaModal.style.display = 'flex'; }
            window.closeSaidaModal = function() { saidaModal.style.display = 'none'; }
            
            window.confirmarSaida = function(pessoa) {
                sendUpdateToServer(pessoa, 'Qualquer', 'SAIDA');
                closeSaidaModal();
            }

            window.openWarningModal = function() { warningModal.style.display = 'flex'; }
            window.closeWarningModal = function() { warningModal.style.display = 'none'; }

            async function fetchLatestStatus() {
                try {
                    const response = await fetch('/api/status');
                    if (!response.ok) return;
                    const data = await response.json();
                    updateStatusDisplay(data);
                } catch (err) {
                    console.error("Erro ao buscar status:", err);
                }
            }
            
            function verificarDiaDaFeira() {
                const hoje = new Date();
                const diaDaSemana = hoje.getDay(); 
                const horaAtual = hoje.getHours(); 

                if (diaDaSemana === 4 || (diaDaSemana === 5 && horaAtual < 12)) {
                    document.getElementById('feira-aviso').style.display = 'block';
                }
            }
            
            // --- CÓDIGO CORRIGIDO DA FEATURE APOD ---
            async function fetchApod() {
                try {
                    const response = await fetch('/api/apod');
                    if (!response.ok) return;
                    const data = await response.json();
                    
                    if (data.media_type === 'image') {
                        document.getElementById('apod-container').style.display = 'block';
                        document.getElementById('apod-title').textContent = data.title;
                        document.getElementById('apod-image').src = data.url;
                        
                        const explanationP = document.getElementById('apod-explanation');
                        // Limpa o conteúdo anterior e adiciona o texto da explicação com um espaço no final
                        explanationP.textContent = data.explanation + ' '; 
                        
                        // Cria o elemento de link <a>
                        const hdLink = document.createElement('a');
                        hdLink.href = data.hdurl || data.url; // Usa hdurl se existir, senão a url padrão
                        hdLink.textContent = 'Ver em alta resolução.';
                        hdLink.target = '_blank'; // Garante que o link abra em uma nova aba
                        
                        // Adiciona o link ao final do parágrafo da explicação
                        explanationP.appendChild(hdLink);
                    }

                } catch (err) {
                    console.error("Erro ao buscar APOD:", err);
                }
            }
            
            verificarDiaDaFeira();
            fetchLatestStatus();
            fetchApod(); 
            setInterval(fetchLatestStatus, 5000);

            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'visible') fetchLatestStatus();
            });

            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/service-worker.js').catch(err => console.error('Erro SW:', err));
            } else {
                document.getElementById('notifications-btn').style.display = 'none';
            }
        });
    </script>
    <script>
      const notificationsBtn = document.getElementById('notifications-btn');
      function urlBase64ToUint8Array(base64String) {
          const padding = '='.repeat((4 - base64String.length % 4) % 4);
          const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
          const rawData = window.atob(base64);
          const outputArray = new Uint8Array(rawData.length);
          for (let i = 0; i < rawData.length; ++i) { outputArray[i] = rawData.charCodeAt(i); }
          return outputArray;
      }
      async function subscribeUser() {
          try {
              const response = await fetch('/api/vapid_public_key');
              const data = await response.json();
              const convertedVapidKey = urlBase64ToUint8Array(data.public_key);
              const registration = await navigator.serviceWorker.ready;
              const subscription = await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: convertedVapidKey });
              await fetch('/api/subscribe', { method: 'POST', body: JSON.stringify(subscription), headers: { 'Content-Type': 'application/json' } });
              notificationsBtn.textContent = 'Notificações Ativadas!';
              notificationsBtn.disabled = true;
          } catch (error) {
              console.error('Falha ao se inscrever:', error);
              alert('Não foi possível ativar as notificações.');
          }
      }
      notificationsBtn.addEventListener('click', () => {
          if (Notification.permission === 'denied') { alert('As notificações foram bloqueadas nas configurações do navegador.'); return; }
          Notification.requestPermission().then(permission => { if (permission === 'granted') { subscribeUser(); } });
      });
    </script>
</body>
</html>