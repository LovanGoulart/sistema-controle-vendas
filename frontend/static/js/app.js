/* App Base */
let currentUser = null;

// Verifica autenticação
document.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('/api/usuario/atual');
        const data = await response.json();

        if (!data.autenticado) {
            if (!window.location.pathname.includes('/login') && window.location.pathname !== '/') {
                window.location.href = '/';
            }
            return;
        }

        currentUser = data.usuario;
        const userNameEl = document.getElementById('userName');
        if (userNameEl) userNameEl.textContent = currentUser.nome;
    } catch (e) {
        console.error('Erro ao verificar autenticação:', e);
    }
});

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
}

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (e) {
        console.error('Erro no logout:', e);
    }
}

function mostrarToast(mensagem, tipo = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.innerHTML = '<i class="fas fa-' + (tipo === 'error' ? 'exclamation-circle' : 'check-circle') + '"></i> ' + mensagem;
    toast.className = 'toast ' + tipo + ' show';
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function mostrarLoading(mostrar) {
    const loading = document.getElementById('loading');
    if (loading) loading.classList.toggle('show', mostrar);
}

// Formatadores
function formatarMoeda(valor) {
    return 'R$ ' + parseFloat(valor || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatarData(dataStr) {
    if (!dataStr) return '-';
    const d = new Date(dataStr);
    return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}
