document.addEventListener('DOMContentLoaded', function() {

  var data = Object.keys(survey_count_data).map(function(key) {
      return { date: d3.timeParse("%Y-%m")(key), value: survey_count_data[key] };
  });

  var margin = {top: 30, right: 30, bottom: 50, left: 30},
      width = 460 - margin.left - margin.right,
      height = 250 - margin.top - margin.bottom;

  var svg = d3.select(".chart")
    .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

      var x = d3.scaleTime()
      .domain(d3.extent(data, function(d) { return d.date; }))
      .range([ 0, width ]);
    
// Add the x Axis
var gX = svg.append("g")
.attr("transform", "translate(0," + height + ")")
.call(d3.axisBottom(x).tickFormat(d3.timeFormat("%Y-%m")));

gX.select(".domain").remove(); //remove X axis line

// Labels on x axis
gX.selectAll("text")
.style("text-anchor", "end")
.attr("dx", "-.8em")
.attr("dy", ".15em")
.attr("transform", "rotate(-45)");

// Remove tick lines
gX.selectAll(".tick line").remove();
  var y = d3.scaleLinear()
    .domain([0, d3.max(data, function(d) { return +d.value; })])
    .range([ height, 0 ]);
  
// Add the y Axis
var gY = svg.append("g")
  .call(d3.axisLeft(y));

gY.select(".domain").remove(); //remove Y axis line

// Remove tick lines
gY.selectAll(".tick line").remove();
  var y = d3.scaleLinear()
    .domain([0, d3.max(data, function(d) { return +d.value; })])
    .range([ height, 0 ]);

// Add the y Axis for grid
var yAxis = svg.append("g")
.call(d3.axisLeft(y)
  .tickSize(-width)
  .tickFormat("")
  .tickValues(y.ticks().slice(1)) // Remove the first tick (zero) from the array of ticks
)
.attr("class", "grid")

// Style for the grid behind the chart
yAxis.selectAll(".tick line")
.style("stroke", "#f3f3f3")

// Remove left axis line
yAxis.select('.domain').remove();

// Add graph area      
svg.append("path")
  .datum(data)
  .attr("fill", "#B6D2D0")
  .attr("stroke", "none")
  .attr("class", "area")
  .attr("d", d3.area()
  .x(function(d) { return x(d.date) })
  .y0(height)
  .y1(function(d) { return y(d.value) })
  );

// Value labels on the data points, at first hidden
var valueLabels = svg.selectAll(".text")
.data(data)
.enter()
.append("text")
.attr("class", "value-label")
.attr("x", function(d) { return x(d.date); })
.attr("y", function(d) { return y(d.value) - 20; })
.style("text-anchor", "middle")
.style("font-size", "12px")
.style("opacity", 0) // initially hidden
.text(function(d) { return d.value; });

// Mouse hover
svg.selectAll(".area")
.on("mouseover", function() {
valueLabels.style("opacity", 1);
})
.on("mouseout", function() {
valueLabels.style("opacity", 0);
});

// Font style
svg.selectAll("text")
 .style("font-family", '"Roc-Grotesk", sans-serif')
 .style("font-style", "normal")
 .style("font-weight", "400");
});


