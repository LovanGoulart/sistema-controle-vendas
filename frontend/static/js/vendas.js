/* Vendas */
let itensVenda = [];
let produtosDisponiveis = [];
let clientesDisponiveis = [];

document.addEventListener('DOMContentLoaded', async function() {
    await carregarClientesSelect();
    await carregarProdutosSelect();
});

async function carregarClientesSelect() {
    try {
        const response = await fetch('/api/clientes');
        const data = await response.json();

        if (data.sucesso) {
            clientesDisponiveis = data.clientes;
            const select = document.getElementById('selectCliente');
            select.innerHTML = '<option value="">Selecione um cliente...</option>' +
                data.clientes.map(c => `<option value="${c.id}">${c.nome} ${c.cidade ? '(' + c.cidade + ')' : ''}</option>`).join('');
        }
    } catch (error) {
        mostrarToast('Erro ao carregar clientes', 'error');
    }
}

async function carregarProdutosSelect() {
    try {
        const response = await fetch('/api/produtos');
        const data = await response.json();

        if (data.sucesso) {
            produtosDisponiveis = data.produtos;
            const select = document.getElementById('selectProduto');
            select.innerHTML = '<option value="">Selecione um produto...</option>' +
                data.produtos.map(p => `<option value="${p.id}">${p.nome} - ${formatarMoeda(p.preco_venda)} (estoque: ${p.quantidade_estoque})</option>`).join('');
        }
    } catch (error) {
        mostrarToast('Erro ao carregar produtos', 'error');
    }
}

function adicionarItem() {
    const produtoId = parseInt(document.getElementById('selectProduto').value);
    const qtd = parseInt(document.getElementById('qtdProduto').value) || 1;

    if (!produtoId) {
        mostrarToast('Selecione um produto', 'error');
        return;
    }

    const produto = produtosDisponiveis.find(p => p.id === produtoId);
    if (!produto) return;

    if (produto.quantidade_estoque < qtd) {
        mostrarToast(`Estoque insuficiente. Disponível: ${produto.quantidade_estoque}`, 'error');
        return;
    }

    const itemExistente = itensVenda.find(i => i.produto_id === produtoId);
    if (itemExistente) {
        itemExistente.quantidade += qtd;
        itemExistente.subtotal = itemExistente.quantidade * itemExistente.preco_unitario;
        itemExistente.lucro_item = itemExistente.quantidade * (itemExistente.preco_unitario - itemExistente.custo_unitario);
    } else {
        itensVenda.push({
            produto_id: produtoId,
            produto_nome: produto.nome,
            quantidade: qtd,
            preco_unitario: produto.preco_venda,
            custo_unitario: produto.preco_custo,
            subtotal: qtd * produto.preco_venda,
            lucro_item: qtd * (produto.preco_venda - produto.preco_custo)
        });
    }

    document.getElementById('selectProduto').value = '';
    document.getElementById('qtdProduto').value = 1;
    renderizarItens();
    atualizarResumo();
}

function renderizarItens() {
    const container = document.getElementById('itensVenda');

    if (itensVenda.length === 0) {
        container.innerHTML = `
            <div class="empty-items">
                <i class="fas fa-shopping-basket"></i>
                <p>Nenhum item adicionado</p>
            </div>`;
        return;
    }

    container.innerHTML = itensVenda.map((item, index) => `
        <div class="item-venda">
            <div class="item-info">
                <div class="item-name">${item.produto_nome}</div>
                <div class="item-detail">${formatarMoeda(item.preco_unitario)} cada · Custo: ${formatarMoeda(item.custo_unitario)} · Lucro: ${formatarMoeda(item.preco_unitario - item.custo_unitario)}</div>
            </div>
            <div class="item-qtd">
                <button class="btn-icon" onclick="alterarQtd(${index}, -1)"><i class="fas fa-minus"></i></button>
                <input type="number" value="${item.quantidade}" min="1" onchange="atualizarQtd(${index}, this.value)">
                <button class="btn-icon" onclick="alterarQtd(${index}, 1)"><i class="fas fa-plus"></i></button>
            </div>
            <div class="item-subtotal">${formatarMoeda(item.subtotal)}</div>
            <button class="item-remove" onclick="removerItem(${index})"><i class="fas fa-times"></i></button>
        </div>
    `).join('');
}

function alterarQtd(index, delta) {
    const novaQtd = itensVenda[index].quantidade + delta;
    if (novaQtd < 1) return;
    atualizarQtd(index, novaQtd);
}

function atualizarQtd(index, qtd) {
    qtd = parseInt(qtd);
    if (qtd < 1) qtd = 1;

    const item = itensVenda[index];
    item.quantidade = qtd;
    item.subtotal = qtd * item.preco_unitario;
    item.lucro_item = qtd * (item.preco_unitario - item.custo_unitario);

    renderizarItens();
    atualizarResumo();
}

function removerItem(index) {
    itensVenda.splice(index, 1);
    renderizarItens();
    atualizarResumo();
}

function atualizarResumo() {
    const subtotal = itensVenda.reduce((s, i) => s + i.subtotal, 0);
    const lucro = itensVenda.reduce((s, i) => s + i.lucro_item, 0);

    document.getElementById('subtotalVenda').textContent = formatarMoeda(subtotal);
    document.getElementById('lucroVenda').textContent = formatarMoeda(lucro);
    document.getElementById('totalVenda').textContent = formatarMoeda(subtotal);
}

async function finalizarVenda() {
    const clienteId = parseInt(document.getElementById('selectCliente').value);

    if (!clienteId) {
        mostrarToast('Selecione um cliente', 'error');
        return;
    }

    if (itensVenda.length === 0) {
        mostrarToast('Adicione pelo menos um produto', 'error');
        return;
    }

    const dados = {
        cliente_id: clienteId,
        forma_pagamento: document.getElementById('formaPagamento').value,
        observacoes: document.getElementById('observacoesVenda').value,
        itens: itensVenda.map(i => ({
            produto_id: i.produto_id,
            quantidade: i.quantidade,
            preco_unitario: i.preco_unitario
        }))
    };

    try {
        mostrarLoading(true);
        const response = await fetch('/api/vendas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (data.sucesso) {
            mostrarToast(`Venda #${data.venda.id} finalizada! Total: ${formatarMoeda(data.venda.total)}`);
            itensVenda = [];
            renderizarItens();
            atualizarResumo();
            document.getElementById('selectCliente').value = '';
            document.getElementById('observacoesVenda').value = '';
            await carregarProdutosSelect();
        } else {
            mostrarToast(data.erro || 'Erro ao finalizar venda', 'error');
        }
    } catch (error) {
        mostrarToast('Erro de conexão', 'error');
    } finally {
        mostrarLoading(false);
    }
}

// Modal cliente rápido
document.getElementById('formClienteRapido').addEventListener('submit', async function(e) {
    e.preventDefault();

    const dados = {
        nome: document.getElementById('clienteRapidoNome').value.trim(),
        telefone: document.getElementById('clienteRapidoTelefone').value.trim()
    };

    try {
        const response = await fetch('/api/clientes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (data.sucesso) {
            mostrarToast('Cliente criado!');
            fecharModalClienteRapido();
            await carregarClientesSelect();
            document.getElementById('selectCliente').value = data.cliente.id;
        } else {
            mostrarToast(data.erro || 'Erro ao criar cliente', 'error');
        }
    } catch (error) {
        mostrarToast('Erro de conexão', 'error');
    }
});

function abrirModalClienteRapido() {
    document.getElementById('formClienteRapido').reset();
    document.getElementById('modalClienteRapido').classList.add('active');
}

function fecharModalClienteRapido() {
    document.getElementById('modalClienteRapido').classList.remove('active');
}
