/* Login */
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, senha })
        });

        const data = await response.json();

        if (data.sucesso) {
            window.location.href = '/dashboard';
        } else {
            mostrarToast(data.erro || 'Erro no login', 'error');
        }
    } catch (error) {
        mostrarToast('Erro de conexão', 'error');
    }
});

function togglePassword() {
    const input = document.getElementById('senha');
    const btn = document.querySelector('.toggle-password i');
    if (input.type === 'password') {
        input.type = 'text';
        btn.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        btn.className = 'fas fa-eye';
    }
}

function mostrarToast(mensagem, tipo = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = mensagem;
    toast.className = 'toast ' + tipo + ' show';
    setTimeout(() => toast.classList.remove('show'), 3000);
}
