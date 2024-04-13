 // Imposta le dimensioni del grafico
 const margin = { top: 20, right: 20, bottom: 20, left: 0 };
 const width = 400;
 const height = 200;
 
 // Crea un SVG
 const svg = d3.select('.chart')
     .append('svg')
     .attr('width', width + margin.left + margin.right)
     .attr('height', height + margin.top + margin.bottom)
     .append('g')
     .attr('transform', `translate(${margin.left},${margin.top})`);


function createAreaChart(data) {
    // Convert keys to dates and values to numbers
    const parseDate = d3.timeParse("%Y-%m");

    const formattedData = Object.entries(data).map(([key, value]) => ({
        date: parseDate(key),
        value: +value
    }));

    // Crea l'asse x
    const x = d3.scaleTime()
        .domain(d3.extent(formattedData, d => d.date))
        .range([0, width]);

    // Crea la funzione di area
    const area = d3.area()
        .x(d => x(d.date))
        .y0(height)
        .y1(d => d.value); // Utilizzo diretto del valore senza y

    // Aggiungi l'area al grafico
    svg.append('path')
        .datum(formattedData)
        .attr('class', 'area')
        .attr('d', area);

    // Aggiungi l'asse x
    svg.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%Y")));
}

createAreaChart(survey_count_data)