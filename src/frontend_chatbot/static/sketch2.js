var width = 220,
    height = 220,
    margin = 20;

var radius = Math.min(width, height) / 2 - margin;

// Append the svg object to the div class "chart2"
var svg = d3.select(".chart2")
  .append("svg")
    .attr("width", width)
    .attr("height", height)
  .append("g")
    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

// Set the color scale
var color = d3.scaleOrdinal()
  .domain(Object.keys(huddle_sumup_data))
  .range(["#B6D2D0", "#4E7286"]);

// Compute the position of each group on the pie
var pie = d3.pie()
  .value(function(d) { return d.value; });

var data_ready = pie(Object.entries(huddle_sumup_data).map(([label, value]) => ({ label, value })));

// Shape helper to build arcs
var arc = d3.arc()
  .innerRadius(radius * 0.5)         // This is the size of the donut hole
  .outerRadius(radius * 0.9);

// Build the pie chart
var paths = svg.selectAll('whatever')
  .data(data_ready)
  .enter()
  .append('path')
  .attr('d', arc)
  .attr('fill', function(d) { return(color(d.data.label)); })
  .attr("stroke", "white")
  .style("stroke-width", "2px");

// Add the percentages in the middle of each slice
paths
  .on("mouseover", function() {
    // Show data in hover
    svg.selectAll('.percentage-text')
      .data(data_ready)
      .enter()
      .append('text')
      .attr('class', 'percentage-text')
      .text(function(d) { return d.data.value + "%"; })
      .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .style("font-family", '"Roc-Grotesk", sans-serif')
      .style("font-style", "normal")
      .style("font-weight", "400");
  })
  .on("mouseout", function() {
    // Hide data on mouseout
    svg.selectAll('.percentage-text').remove();
  });



