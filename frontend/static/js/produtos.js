/* Produtos */
let produtoEditando = null;

document.addEventListener('DOMContentLoaded', function() {
    carregarProdutos();
    carregarCategorias();
});

document.getElementById('formProduto').addEventListener('submit', async function(e) {
    e.preventDefault();

    const dados = {
        nome: document.getElementById('produtoNome').value.trim(),
        descricao: document.getElementById('produtoDescricao').value.trim(),
        categoria: document.getElementById('produtoCategoria').value.trim(),
        preco_custo: parseFloat(document.getElementById('produtoCusto').value) || 0,
        preco_venda: parseFloat(document.getElementById('produtoVenda').value) || 0,
        quantidade_estoque: parseInt(document.getElementById('produtoEstoque').value) || 0
    };

    const url = produtoEditando ? `/api/produtos/${produtoEditando}` : '/api/produtos';
    const method = produtoEditando ? 'PUT' : 'POST';

    try {
        mostrarLoading(true);
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (data.sucesso) {
            mostrarToast(produtoEditando ? 'Produto atualizado!' : 'Produto criado!');
            fecharModalProduto();
            carregarProdutos();
            carregarCategorias();
        } else {
            mostrarToast(data.erro || 'Erro ao salvar', 'error');
        }
    } catch (error) {
        mostrarToast('Erro de conexão', 'error');
    } finally {
        mostrarLoading(false);
    }
});

async function carregarProdutos() {
    try {
        const busca = document.getElementById('buscaProdutos').value;
        const categoria = document.getElementById('filtroCategoria').value;
        let url = '/api/produtos?';
        if (busca) url += `q=${encodeURIComponent(busca)}&`;
        if (categoria) url += `categoria=${encodeURIComponent(categoria)}`;

        const response = await fetch(url);
        const data = await response.json();

        const tbody = document.getElementById('corpoTabelaProdutos');

        if (!data.sucesso || data.produtos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading-cell">Nenhum produto encontrado</td></tr>';
            return;
        }

        tbody.innerHTML = data.produtos.map(p => `
            <tr>
                <td>
                    <strong>${p.nome}</strong>
                    ${p.descricao ? '<br><small>' + p.descricao + '</small>' : ''}
                </td>
                <td><span class="badge badge-info">${p.categoria || '-'}</span></td>
                <td>${formatarMoeda(p.preco_custo)}</td>
                <td>${formatarMoeda(p.preco_venda)}</td>
                <td class="text-success">${formatarMoeda(p.lucro_unitario)}</td>
                <td>${p.margem_lucro.toFixed(1)}%</td>
                <td>
                    <span class="badge ${p.quantidade_estoque < 10 ? 'badge-danger' : 'badge-success'}">
                        ${p.quantidade_estoque}
                    </span>
                </td>
                <td>
                    <div class="cell-actions">
                        <button class="btn-icon edit" onclick="editarProduto(${p.id})" title="Editar"><i class="fas fa-edit"></i></button>
                        <button class="btn-icon delete" onclick="excluirProduto(${p.id})" title="Excluir"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `).join('');

    } catch (error) {
        mostrarToast('Erro ao carregar produtos', 'error');
    }
}

async function carregarCategorias() {
    try {
        const response = await fetch('/api/produtos/categorias');
        const data = await response.json();

        if (data.sucesso) {
            const select = document.getElementById('filtroCategoria');
            const atual = select.value;
            select.innerHTML = '<option value="">Todas as Categorias</option>' +
                data.categorias.map(c => `<option value="${c}">${c}</option>`).join('');
            select.value = atual;
        }
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

function buscarProdutos() {
    carregarProdutos();
}

function abrirModalProduto() {
    produtoEditando = null;
    document.getElementById('formProduto').reset();
    document.getElementById('tituloModalProduto').innerHTML = '<i class="fas fa-box"></i> Novo Produto';
    document.getElementById('modalProduto').classList.add('active');
}

function fecharModalProduto() {
    document.getElementById('modalProduto').classList.remove('active');
}

async function editarProduto(id) {
    try {
        // Buscar da lista atual (simplificado)
        const response = await fetch('/api/produtos');
        const data = await response.json();
        const p = data.produtos.find(pr => pr.id === id);
        if (!p) return;

        produtoEditando = p.id;
        document.getElementById('produtoNome').value = p.nome;
        document.getElementById('produtoDescricao').value = p.descricao || '';
        document.getElementById('produtoCategoria').value = p.categoria || '';
        document.getElementById('produtoCusto').value = p.preco_custo;
        document.getElementById('produtoVenda').value = p.preco_venda;
        document.getElementById('produtoEstoque').value = p.quantidade_estoque;

        document.getElementById('tituloModalProduto').innerHTML = '<i class="fas fa-box-open"></i> Editar Produto';
        document.getElementById('modalProduto').classList.add('active');
    } catch (error) {
        mostrarToast('Erro ao carregar produto', 'error');
    }
}

async function excluirProduto(id) {
    if (!confirm('Tem certeza que deseja inativar este produto?')) return;

    try {
        mostrarLoading(true);
        const response = await fetch(`/api/produtos/${id}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.sucesso) {
            mostrarToast('Produto inativado!');
            carregarProdutos();
        } else {
            mostrarToast(data.erro || 'Erro ao excluir', 'error');
        }
    } catch (error) {
        mostrarToast('Erro de conexão', 'error');
    } finally {
        mostrarLoading(false);
    }
}
