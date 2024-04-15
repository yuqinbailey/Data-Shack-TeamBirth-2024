// Data for the donut chart
var huddle_sumup_data = [{"label": "Huddle Yes", "value": 90}, {"label": "Huddle No", "value": 10}];

// Set the dimensions and margins of the chart
var width = 320, // Smaller width
    height = 450, // Increased height for the margin at the bottom
    marginTop = 20, // Reduced top margin
    marginBottom = 200, // Increased bottom margin
    marginLeft = 20,
    marginRight = 20,
    radius = Math.min(width, height - marginBottom) / 2 - marginTop; // Adjusted for the new height

// Append the svg object to the div class "chart2"
var svg = d3.select(".chart2")
  .append("svg")
    .attr("width", width)
    .attr("height", height)
  .append("g")
    .attr("transform", "translate(" + (width / 2) + "," + (radius + marginTop) + ")");

// Set the color scale
var color = d3.scaleOrdinal()
  .domain(huddle_sumup_data.map(function(d) { return d.label; }))
  .range(["#B6D2D0", "#4E7286"]);

// Compute the position of each group on the pie
var pie = d3.pie()
  .value(function(d) { return d.value; });

var data_ready = pie(huddle_sumup_data);

// Shape helper to build arcs
var arc = d3.arc()
  .innerRadius(radius * 0.5) // This is the size of the donut hole
  .outerRadius(radius * 0.8); // Smaller outer radius

// Build the pie chart
svg
  .selectAll('whatever')
  .data(data_ready)
  .enter()
  .append('path')
  .attr('d', arc)
  .attr('fill', function(d) { return(color(d.data.label)); })
  .attr("stroke", "white")
  .style("stroke-width", "2px")
  .style("opacity", 0.7);

// Add the percentages in the middle of each slice
svg.selectAll('whatever')
  .data(data_ready)
  .enter()
  .append('text')
  .text(function(d) { return d.data.value + "%"; })
  .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
  .style("text-anchor", "middle")
  .style("font-size", "14px")
  .style("font-family", '"Roc-Grotesk", sans-serif')
  .style("font-style", "normal")
  .style("font-weight", "400");

// Define a group for the legend, positioned at the bottom
var legend = svg.append("g")
  .attr("transform", "translate(" + (-radius) + "," + (radius + marginBottom / 2) + ")");

// Calculate the length of the longest label for spacing
var legendSpacing = d3.max(huddle_sumup_data, function(d) { 
  return d.label.length; 
}) * 8; // Adjusted space for each character

// Add circles and text to the legend, placed horizontally
huddle_sumup_data.forEach(function(d, i) {
  legend.append('circle')
    .attr("cy", 0)
    .attr("cx", i * (legendSpacing + 20)) // Space out the legend items
    .attr("r", 6)
    .style("fill", color(d.label));

  legend.append('text')
    .attr("y", 0)
    .attr("x", i * (legendSpacing + 20) + 10) // Position the text right of the circle
    .attr("dy", ".35em")
    .text(d.label)
    .style("font-family", '"Roc-Grotesk", sans-serif')
    .style("font-style", "normal")
    .style("font-weight", "400")
    .style("font-size", "14px")
    .style("alignment-baseline","middle");
});

// Center the legend group horizontally
var legendWidth = legend.node().getBBox().width;
legend.attr("transform", "translate(" + (width/2 - legendWidth/2) + "," + (2 * radius + marginTop) + ")");
