// Utilizza nomi di variabili unici aggiungendo '2' come suffisso per evitare conflitti
const width2 = 300;
const height2 = 300;
const margin2 = 40;

const radius2 = Math.min(width2, height2) / 2 - margin2;

const svg2 = d3.select('.chart2').append('svg')
    .attr('width', width2)
    .attr('height', height2)
    .append('g')
    .attr('transform', `translate(${width2 / 2}, ${height2 / 2})`);

const color2 = d3.scaleOrdinal()
    .domain(["Huddle Yes", "Huddle No"])
    .range(["#FF6C00", "#01224D"]);

const pie2 = d3.pie()
    .sort(null)
    .value(d => d.value);

const arc2 = d3.arc()
    .innerRadius(radius2 * 0.5)
    .outerRadius(radius2 * 0.8);

// Converti l'oggetto dati in un array di dati per d3.pie() utilizzando Object.entries()
const data_ready2 = pie2(Object.entries(huddle_sumup_data).map(([key, value]) => ({ key, value: +value })));

// Costruisci i segmenti del donut chart
svg2.selectAll('allSlices')
    .data(data_ready2)
    .enter()
    .append('path')
    .attr('d', arc2)
    .attr('fill', d => color2(d.data.key))
    .attr('stroke', 'white')
    .style('stroke-width', '2px')

    
