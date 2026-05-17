/* Dashboard */
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('currentDate').textContent = new Date().toLocaleDateString('pt-BR', { 
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
    });
    carregarDashboard();
});

async function carregarDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        const data = await response.json();

        if (!data.sucesso) {
            mostrarToast('Erro ao carregar dashboard', 'error');
            return;
        }

        const r = data.resumo;
        document.getElementById('vendasHoje').textContent = formatarMoeda(r.vendas_hoje);
        document.getElementById('lucroHoje').textContent = formatarMoeda(r.lucro_hoje);
        document.getElementById('numVendasHoje').textContent = r.num_vendas_hoje + ' vendas';
        document.getElementById('vendasMes').textContent = formatarMoeda(r.vendas_mes);
        document.getElementById('numVendasMes').textContent = r.num_vendas_mes + ' vendas';
        document.getElementById('estoqueBaixo').textContent = r.estoque_baixo;

        // Top Clientes
        const topClientesEl = document.getElementById('topClientes');
        topClientesEl.innerHTML = data.top_clientes.map((c, i) => `
            <div class="top-item">
                <div class="top-rank ${i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : 'other'}">${i + 1}</div>
                <div class="top-info">
                    <div class="top-name">${c.nome}</div>
                    <div class="top-detail">${c.num_vendas || 0} vendas · Ticket médio ${formatarMoeda((c.total_gasto || 0) / (c.num_vendas || 1))}</div>
                </div>
                <div class="top-value">${formatarMoeda(c.lucro_total)}</div>
            </div>
        `).join('');

        // Top Produtos
        const topProdutosEl = document.getElementById('topProdutos');
        topProdutosEl.innerHTML = data.top_produtos.map((p, i) => `
            <div class="top-item">
                <div class="top-rank ${i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : 'other'}">${i + 1}</div>
                <div class="top-info">
                    <div class="top-name">${p.nome}</div>
                    <div class="top-detail">${p.qtd_vendida} unidades vendidas</div>
                </div>
                <div class="top-value">${formatarMoeda(p.lucro_total)}</div>
            </div>
        `).join('');

        // Mapa simplificado
        const mapaEl = document.getElementById('mapaClientes');
        const cidades = {};
        // Simulação de dados por cidade
        const cidadesExemplo = [
            { nome: 'São Paulo', uf: 'SP', count: 3 },
            { nome: 'Rio de Janeiro', uf: 'RJ', count: 1 },
            { nome: 'Belo Horizonte', uf: 'MG', count: 1 },
            { nome: 'Curitiba', uf: 'PR', count: 1 },
            { nome: 'Porto Alegre', uf: 'RS', count: 1 },
            { nome: 'Salvador', uf: 'BA', count: 1 },
            { nome: 'Recife', uf: 'PE', count: 1 },
        ];
        mapaEl.innerHTML = '<div class="map-dots">' + cidadesExemplo.map(c => `
            <div class="map-dot">
                <i class="fas fa-map-marker-alt"></i>
                <span class="city">${c.nome}</span>
                <span class="count">${c.count} cliente${c.count > 1 ? 's' : ''}</span>
            </div>
        `).join('') + '</div>';

        // Gráfico
        const ctx = document.getElementById('chartVendas').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.vendas_7dias.map(d => d.dia),
                datasets: [
                    {
                        label: 'Total Vendas',
                        data: data.vendas_7dias.map(d => d.total),
                        backgroundColor: '#3bf7a6',
                        borderRadius: 6,
                        borderSkipped: false
                    },
                    {
                        label: 'Lucro',
                        data: data.vendas_7dias.map(d => d.lucro),
                        backgroundColor: '#0c0d0d',
                        borderRadius: 6,
                        borderSkipped: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return ctx.dataset.label + ': ' + formatarMoeda(ctx.raw);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(v) { return 'R$ ' + v.toLocaleString('pt-BR'); }
                        }
                    }
                }
            }
        });

    } catch (error) {
        mostrarToast('Erro ao carregar dashboard', 'error');
        console.error(error);
    }
}
