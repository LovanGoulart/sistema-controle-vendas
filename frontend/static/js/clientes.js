/* Clientes */
let clienteEditando = null;

document.addEventListener('DOMContentLoaded', carregarClientes);

document.getElementById('formCliente').addEventListener('submit', async function(e) {
    e.preventDefault();

    const dados = {
        nome: document.getElementById('clienteNome').value.trim(),
        email: document.getElementById('clienteEmail').value.trim(),
        telefone: document.getElementById('clienteTelefone').value.trim(),
        endereco: document.getElementById('clienteEndereco').value.trim(),
        cidade: document.getElementById('clienteCidade').value.trim(),
        estado: document.getElementById('clienteEstado').value.trim(),
        latitude: parseFloat(document.getElementById('clienteLat').value) || null,
        longitude: parseFloat(document.getElementById('clienteLng').value) || null
    };

    const url = clienteEditando ? `/api/clientes/${clienteEditando}` : '/api/clientes';
    const method = clienteEditando ? 'PUT' : 'POST';

    try {
        mostrarLoading(true);
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (data.sucesso) {
            mostrarToast(clienteEditando ? 'Cliente atualizado!' : 'Cliente criado!');
            fecharModalCliente();
            carregarClientes();
        } else {
            mostrarToast(data.erro || 'Erro ao salvar', 'error');
        }
    } catch (error) {
        mostrarToast('Erro de conexão', 'error');
    } finally {
        mostrarLoading(false);
    }
});

async function carregarClientes() {
    try {
        const busca = document.getElementById('buscaClientes').value;
        const url = busca ? `/api/clientes?q=${encodeURIComponent(busca)}` : '/api/clientes';

        const response = await fetch(url);
        const data = await response.json();

        const tbody = document.getElementById('corpoTabelaClientes');

        if (!data.sucesso || data.clientes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">Nenhum cliente encontrado</td></tr>';
            return;
        }

        tbody.innerHTML = data.clientes.map(c => `
            <tr>
                <td><strong>${c.nome}</strong>${c.email ? '<br><small>' + c.email + '</small>' : ''}</td>
                <td>${c.telefone || '-'}</td>
                <td>${c.cidade ? c.cidade + '/' + c.estado : '-'}</td>
                <td><span class="badge badge-success">${c.num_vendas}</span></td>
                <td>${formatarMoeda(c.total_gasto)}</td>
                <td class="text-success">${formatarMoeda(c.total_lucro)}</td>
                <td>
                    <div class="cell-actions">
                        <button class="btn-icon edit" onclick="editarCliente(${c.id})" title="Editar"><i class="fas fa-edit"></i></button>
                        <button class="btn-icon delete" onclick="excluirCliente(${c.id})" title="Excluir"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `).join('');

    } catch (error) {
        mostrarToast('Erro ao carregar clientes', 'error');
    }
}

function buscarClientes() {
    carregarClientes();
}

function abrirModalCliente() {
    clienteEditando = null;
    document.getElementById('formCliente').reset();
    document.getElementById('tituloModalCliente').innerHTML = '<i class="fas fa-user"></i> Novo Cliente';
    document.getElementById('modalCliente').classList.add('active');
}

function fecharModalCliente() {
    document.getElementById('modalCliente').classList.remove('active');
}

async function editarCliente(id) {
    try {
        const response = await fetch(`/api/clientes/${id}`);
        const data = await response.json();

        if (!data.sucesso) return;

        const c = data.cliente;
        clienteEditando = c.id;
        document.getElementById('clienteNome').value = c.nome;
        document.getElementById('clienteEmail').value = c.email || '';
        document.getElementById('clienteTelefone').value = c.telefone || '';
        document.getElementById('clienteEndereco').value = c.endereco || '';
        document.getElementById('clienteCidade').value = c.cidade || '';
        document.getElementById('clienteEstado').value = c.estado || '';
        document.getElementById('clienteLat').value = c.latitude || '';
        document.getElementById('clienteLng').value = c.longitude || '';

        document.getElementById('tituloModalCliente').innerHTML = '<i class="fas fa-user-edit"></i> Editar Cliente';
        document.getElementById('modalCliente').classList.add('active');
    } catch (error) {
        mostrarToast('Erro ao carregar cliente', 'error');
    }
}

async function excluirCliente(id) {
    if (!confirm('Tem certeza que deseja excluir este cliente?')) return;

    try {
        mostrarLoading(true);
        const response = await fetch(`/api/clientes/${id}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.sucesso) {
            mostrarToast('Cliente excluído!');
            carregarClientes();
        } else {
            mostrarToast(data.erro || 'Erro ao excluir', 'error');
        }
    } catch (error) {
        mostrarToast('Erro de conexão', 'error');
    } finally {
        mostrarLoading(false);
    }
}
