/* Relatórios */
document.addEventListener('DOMContentLoaded', function() {
    carregarRelatorioClientes();

    // Set datas padrão
    const hoje = new Date();
    const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    document.getElementById('dataInicio').value = inicioMes.toISOString().split('T')[0];
    document.getElementById('dataFim').value = hoje.toISOString().split('T')[0];
});

function mostrarTab(tab) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));

    document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
    event.target.classList.add('active');

    if (tab === 'clientes') carregarRelatorioClientes();
    if (tab === 'produtos') carregarRelatorioProdutos();
}

async function carregarRelatorioClientes() {
    try {
        mostrarLoading(true);
        const response = await fetch('/api/relatorios/lucratividade-clientes');
        const data = await response.json();

        const tbody = document.getElementById('corpoRelatorioClientes');

        if (!data.sucesso || data.clientes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading-cell">Nenhum dado encontrado</td></tr>';
            return;
        }

        tbody.innerHTML = data.clientes.map(c => `
            <tr>
                <td><strong>${c.nome}</strong>${c.email ? '<br><small>' + c.email + '</small>' : ''}</td>
                <td>${c.cidade || '-'}</td>
                <td>${c.num_vendas}</td>
                <td>${formatarMoeda(c.total_gasto)}</td>
                <td class="text-success">${formatarMoeda(c.lucro_total)}</td>
                <td>${formatarMoeda(c.ticket_medio)}</td>
            </tr>
        `).join('');

    } catch (error) {
        mostrarToast('Erro ao carregar relatório', 'error');
    } finally {
        mostrarLoading(false);
    }
}

async function carregarRelatorioProdutos() {
    try {
        mostrarLoading(true);
        const response = await fetch('/api/relatorios/lucratividade-produtos');
        const data = await response.json();

        const tbody = document.getElementById('corpoRelatorioProdutos');

        if (!data.sucesso || data.produtos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">Nenhum dado encontrado</td></tr>';
            return;
        }

        tbody.innerHTML = data.produtos.map(p => `
            <tr>
                <td><strong>${p.nome}</strong></td>
                <td><span class="badge badge-info">${p.categoria || '-'}</span></td>
                <td>${formatarMoeda(p.preco_custo)}</td>
                <td>${formatarMoeda(p.preco_venda)}</td>
                <td>${p.margem_lucro.toFixed(1)}%</td>
                <td>${p.qtd_vendida}</td>
                <td class="text-success">${formatarMoeda(p.lucro_total)}</td>
            </tr>
        `).join('');

    } catch (error) {
        mostrarToast('Erro ao carregar relatório', 'error');
    } finally {
        mostrarLoading(false);
    }
}

async function gerarRelatorioPeriodo() {
    const inicio = document.getElementById('dataInicio').value;
    const fim = document.getElementById('dataFim').value;

    if (!inicio || !fim) {
        mostrarToast('Selecione o período', 'error');
        return;
    }

    try {
        mostrarLoading(true);
        const response = await fetch(`/api/relatorios/vendas-periodo?data_inicio=${inicio}&data_fim=${fim}`);
        const data = await response.json();

        const container = document.getElementById('resultadoPeriodo');

        if (!data.sucesso) {
            container.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${data.erro || 'Erro ao gerar relatório'}</p></div>`;
            return;
        }

        const r = data.resumo;
        container.innerHTML = `
            <div class="resumo-periodo">
                <div class="resumo-card">
                    <div class="label">Período</div>
                    <div class="value">${r.periodo}</div>
                </div>
                <div class="resumo-card">
                    <div class="label">Total Vendas</div>
                    <div class="value">${formatarMoeda(r.total_vendas)}</div>
                </div>
                <div class="resumo-card">
                    <div class="label">Total Lucro</div>
                    <div class="value text-success">${formatarMoeda(r.total_lucro)}</div>
                </div>
                <div class="resumo-card">
                    <div class="label">Nº Vendas</div>
                    <div class="value">${r.num_vendas}</div>
                </div>
                <div class="resumo-card">
                    <div class="label">Ticket Médio</div>
                    <div class="value">${formatarMoeda(r.ticket_medio)}</div>
                </div>
            </div>
            <h4 style="margin: 20px 0 12px; color: var(--gray-700);"><i class="fas fa-credit-card"></i> Por Forma de Pagamento</h4>
            <div class="table-container">
                <table class="data-table">
                    <thead><tr><th>Forma</th><th>Quantidade</th><th>Total</th></tr></thead>
                    <tbody>
                        ${data.por_pagamento.map(p => `
                            <tr>
                                <td><span class="badge badge-info">${p.forma.replace('_', ' ').toUpperCase()}</span></td>
                                <td>${p.quantidade}</td>
                                <td>${formatarMoeda(p.total)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

    } catch (error) {
        mostrarToast('Erro ao gerar relatório', 'error');
    } finally {
        mostrarLoading(false);
    }
}
