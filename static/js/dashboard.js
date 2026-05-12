document.addEventListener('DOMContentLoaded', () => {

    const form = document.getElementById('pricing-form');

    const resultsDiv =
        document.getElementById('results');

    const loadingDiv =
        document.getElementById('loading');

    const errorMessageDiv =
        document.getElementById('error-message');

    const errorText =
        document.getElementById('error-text');

    const userDemandSpan =
        document.getElementById('user-demand');

    const userRevenueSpan =
        document.getElementById('user-revenue');

    const userProfitSpan =
        document.getElementById('user-profit');

    const optimalPriceSpan =
        document.getElementById('optimal-price');

    const optimalDemandSpan =
        document.getElementById('optimal-demand');

    const optimalProfitSpan =
        document.getElementById('optimal-profit');

    const productCategorySelect =
        document.getElementById('product_category');

    const productNameSelect =
        document.getElementById('product_name');

    const forecastRevenue =
        document.getElementById('forecast-revenue');

    const forecastProfit =
        document.getElementById('forecast-profit');

    const recommendedPrice =
        document.getElementById('recommended-price');

    const aiConfidence =
        document.getElementById('ai-confidence');

    const projectedUplift =
        document.getElementById('projected-uplift');

    const marketRisk =
        document.getElementById('market-risk');

    const marketRiskDesc =
        document.getElementById('market-risk-desc');


    const aiInsightsContainer =
        document.getElementById('ai-insights-container');

    const productsByCategory =
        window.productsByCategory || {};

    function updateProductNames() {

        const selectedCategory =
            productCategorySelect.value;

        const products =
            productsByCategory[selectedCategory] || [];

        productNameSelect.innerHTML =
            products.map(
                p => `<option value="${p}">${p}</option>`
            ).join('');
    }

    if (
        productsByCategory &&
        Object.keys(productsByCategory).length > 0
    ) {
        updateProductNames();
    }

    productCategorySelect.addEventListener(
        'change',
        updateProductNames
    );
    /* ==========================
       KPI Counter Animation
    ========================== */

    function animateValue(element, start, end, duration, prefix='') {

        let startTimestamp = null;

        const step = (timestamp) => {

            if (!startTimestamp)
                startTimestamp = timestamp;

            const progress = Math.min(
                (timestamp - startTimestamp) / duration,
                1
            );

            const value =
                progress * (end - start) + start;

            if (element) {

                element.textContent =
                    `${prefix}${value.toFixed(2)}`;
            }

            if (progress < 1) {

                window.requestAnimationFrame(step);
            }
        };

        window.requestAnimationFrame(step);
    }
    let chart = null;

    form.addEventListener('submit', async (e) => {

        e.preventDefault();

        loadingDiv.classList.remove('hidden');

        resultsDiv.classList.add('hidden');

        errorMessageDiv.classList.add('hidden');

        const formData = new FormData(form);

        try {

            const response = await fetch(
                window.location.origin + '/predict',
                {
                    method: 'POST',
                    body: formData
                }
            );

            if (!response.ok) {

                const errorData =
                    await response.json();

                throw new Error(
                    errorData.error || 'Server error.'
                );
            }

            const data = await response.json();

            if (data.success) {

                /* ==========================
                   Main Metrics
                ========================== */

                userDemandSpan.textContent =
                    data.user_prediction.demand;

                userRevenueSpan.textContent =
                    `$${data.user_prediction.revenue.toFixed(2)}`;

                userProfitSpan.textContent =
                    `$${Number(data.user_prediction.profit).toFixed(2)}`;

                optimalPriceSpan.textContent =
                    `$${Number(data.optimal_prediction.optimal_price).toFixed(2)}`;

                optimalDemandSpan.textContent =
                    data.optimal_prediction.optimal_demand;

                optimalProfitSpan.textContent =
                    `$${Number(data.optimal_prediction.max_profit).toFixed(2)}`;

                /* ==========================
                   KPI Cards
                ========================== */

                animateValue(
                    forecastRevenue,
                    0,
                    data.user_prediction.revenue,
                    900,
                    '$'
                );

                animateValue(
                    forecastProfit,
                    0,
                    data.user_prediction.profit,
                    900,
                    '$'
                );

                animateValue(
                    recommendedPrice,
                    0,
                    data.optimal_prediction.optimal_price,
                    900,
                    '$'
                );

                if (aiConfidence) {
                
                    aiConfidence.textContent =
                        `${data.business_metrics.ai_confidence}%`;
                }

                if (projectedUplift) {
                
                    projectedUplift.textContent =
                        `↑ ${data.business_metrics.profit_improvement}% projected uplift`;
                }

                if (marketRisk) {
                
                    marketRisk.textContent =
                        data.business_metrics.market_risk;
                }

                if (marketRisk && marketRiskDesc) {
                
                    if (data.business_metrics.market_risk === 'High') {
                    
                        marketRisk.className =
                            'text-3xl font-bold mt-4 text-red-400';
                    
                        marketRiskDesc.textContent =
                            'High market volatility detected';
                    
                    } else {
                    
                        marketRisk.className =
                            'text-3xl font-bold mt-4 text-yellow-400';
                    
                        marketRiskDesc.textContent =
                            'Competitor pressure detected';
                    }
                }

                /* ==========================
                    Dynamic AI Insights
                ========================== */
                if (data.ai_insights) {
                
                    aiInsightsContainer.innerHTML =
                        data.ai_insights.map(insight => `
                        
                            <div class="bg-gray-800 border border-gray-700 rounded-2xl p-5 text-gray-300">
                        
                                ${insight}
                        
                            </div>
                        
                        `).join('');
                }

                /* ==========================
                   Chart Data
                ========================== */

                const prices =
                    data.plot_data.prices;

                const userPrice =
                    parseFloat(
                        document.getElementById('unit_price').value
                    );

                const optimalPrice =
                    data.optimal_prediction.optimal_price;

                const userPriceIndex =
                    prices.findIndex(
                        p => Math.abs(p - userPrice) < 0.01
                    );

                const optimalPriceIndex =
                    prices.findIndex(
                        p => Math.abs(p - optimalPrice) < 0.01
                    );

                const datasets = [

                    {
                        label: 'Predicted Demand',

                        data: data.plot_data.demand,

                        borderColor: '#60A5FA',

                        backgroundColor:
                            'rgba(96,165,250,0.15)',

                        yAxisID: 'y_demand',

                        tension: 0.45,

                        fill: true,

                        borderWidth: 3
                    },

                    {
                        label: 'Predicted Profit',

                        data: data.plot_data.profit,

                        borderColor: '#34D399',

                        backgroundColor:
                            'rgba(52,211,153,0.15)',

                        yAxisID: 'y_profit',

                        tension: 0.45,

                        fill: true,

                        borderWidth: 3
                    }
                ];

                const scatterPoints = [];

                if (userPriceIndex !== -1) {

                    scatterPoints.push({
                        x: prices[userPriceIndex],
                        y: data.plot_data.profit[userPriceIndex]
                    });
                }

                if (optimalPriceIndex !== -1) {

                    scatterPoints.push({
                        x: prices[optimalPriceIndex],
                        y: data.plot_data.profit[optimalPriceIndex]
                    });
                }

                if (scatterPoints.length > 0) {

                    datasets.push({

                        label: 'Key Prices',

                        data: scatterPoints,

                        pointStyle: 'circle',

                        pointRadius: 8,

                        pointHoverRadius: 12,

                        pointBackgroundColor: [
                            '#EF4444',
                            '#10B981'
                        ],

                        pointBorderColor: '#FFFFFF',

                        pointBorderWidth: 2,

                        showLine: false
                    });
                }

                /* ==========================
                   Chart Rendering
                ========================== */

                if (chart) {

                    chart.data.labels =
                        prices.map(p => p.toFixed(2));

                    chart.data.datasets =
                        datasets;

                    chart.update();

                } else {

                    const ctx =
                        document.getElementById('pricing-chart')
                        .getContext('2d');

                    chart = new Chart(ctx, {

                        type: 'line',

                        data: {

                            labels:
                                prices.map(
                                    p => p.toFixed(2)
                                ),

                            datasets: datasets
                        },

                        options: {

                            responsive: true,

                            maintainAspectRatio: false,

                            interaction: {
                                mode: 'index',
                                intersect: false,
                            },

                            plugins: {

                                legend: {

                                    labels: {
                                        color: '#E5E7EB'
                                    }
                                },

                                title: {

                                    display: true,

                                    text:
                                        'AI Pricing Optimization Curve',

                                    color: '#FFFFFF',

                                    font: {
                                        size: 18
                                    }
                                }
                            },

                            scales: {

                                x: {

                                    ticks: {
                                        color: '#9CA3AF'
                                    },

                                    grid: {
                                        color:
                                            'rgba(255,255,255,0.05)'
                                    }
                                },

                                y_demand: {

                                    type: 'linear',

                                    position: 'left',

                                    ticks: {
                                        color: '#60A5FA'
                                    },

                                    grid: {
                                        color:
                                            'rgba(96,165,250,0.08)'
                                    }
                                },

                                y_profit: {

                                    type: 'linear',

                                    position: 'right',

                                    ticks: {
                                        color: '#34D399'
                                    },

                                    grid: {
                                        drawOnChartArea: false
                                    }
                                }
                            }
                        }
                    });
                }

                loadingDiv.classList.add('hidden');

                resultsDiv.classList.remove('hidden');

            } else {

                throw new Error(
                    data.error || 'Unexpected response.'
                );
            }

        } catch (err) {

            console.error('Error:', err);

            errorText.textContent =
                err.message;

            errorMessageDiv.classList.remove('hidden');

            loadingDiv.classList.add('hidden');
        }
    });
});

/* ==========================
   Lucide Icons
========================== */

lucide.createIcons();