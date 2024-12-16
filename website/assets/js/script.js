// Helper function to compress filter arrays
function compressFilters(filters) {
    // Initialize mapping for codes
    const mapping = new Map();
    let counter = 0;

    // Helper to get or create code
    const getCode = (title) => {
      if (!mapping.has(title)) {
        mapping.set(title, counter.toString(36));
        counter++;
      }
      return mapping.get(title);
    };

    // Compress the filters
    const compressed = {
      codes: {}, // Will store our title-to-code mapping
      a: [], // Agency codes
      c: [], // Category codes
      t: [], // Assistance type codes
      p: [], // Applicant type codes
    };

    // Process agency filters
    if (filters.agency && filters.agency.length > 0) {
      filters.agency.forEach((filter) => {
        const code = getCode(filter.title || filter);
        compressed.codes[code] = filter.title || filter;

        if (filter.type === "sub-agency") {
          const parentCode = getCode(filter.parentTitle);
          compressed.codes[parentCode] = filter.parentTitle;
          compressed.a.push(`s${parentCode}:${code}`);
        } else {
          compressed.a.push(`p${code}${filter.selectAll ? "*" : ""}`);
        }
      });
    }

    // Process category filters
    if (filters.category && filters.category.length > 0) {
      filters.category.forEach((filter) => {
        const code = getCode(filter.title || filter);
        compressed.codes[code] = filter.title || filter;

        if (filter.type === "sub-category") {
          const parentCode = getCode(filter.parentTitle);
          compressed.codes[parentCode] = filter.parentTitle;
          compressed.c.push(`s${parentCode}:${code}`);
        } else {
          compressed.c.push(`p${code}${filter.selectAll ? "*" : ""}`);
        }
      });
    }

    // Process assistance types
    if (filters.assistance && filters.assistance.length > 0) {
      filters.assistance.forEach((filter) => {
        const code = getCode(filter.title || filter);
        compressed.codes[code] = filter.title || filter;
        compressed.t.push(code);
      });
    }

    // Process applicant types
    if (filters.applicant && filters.applicant.length > 0) {
      filters.applicant.forEach((filter) => {
        const code = getCode(filter.title || filter);
        compressed.codes[code] = filter.title || filter;
        compressed.p.push(code);
      });
    }

    return compressed;
  }

  function createBarChart(data, {
    container = '#myChart',
    xLabel = '',
    yLabel = '',
    valueFormatter = (d) => d,
    xAxisFormatter = (d) => d3.format(",")(d),
    onClickHandler = null,
    maxWidth = 180
  }) {
    // Clear existing chart
    d3.select(container).selectAll("*").remove();
  
    // Set up dimensions
    const margin = { top: 20, right: 30, bottom: 60, left: 250 };
    const width = 1000 - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom;
  
    // Create SVG
    const svg = d3.select(container)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
  
    // Create scales
    const y = d3.scaleBand()
      .domain(data.map(d => d.title))
      .range([0, height])
      .padding(0.3);  // Reverted to original padding
  
    const x = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value)])
      .range([0, width]);
  
    // Create axes
    const xAxis = d3.axisBottom(x)
      .ticks(5)
      .tickFormat(xAxisFormatter);
  
    const yAxis = d3.axisLeft(y);
  
    // Add X axis
    svg.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis);
  
    // Add X axis label
    svg.append("text")
      .attr("class", "x-label")
      .attr("text-anchor", "middle")
      .attr("x", width / 2)
      .attr("y", height + margin.bottom - 10)
      .text(xLabel);
  
    // Add Y axis with clickable labels
    const yAxisGroup = svg.append("g")
      .attr("class", "y-axis")
      .call(yAxis);
  
    // Improved text wrapping for y-axis labels
    yAxisGroup.selectAll(".tick text")
      .style("cursor", "pointer")
      .call(function(text) {
        text.each(function() {
          const text = d3.select(this);
          const words = text.text().match(/\S+\s*/g) || []; // Keep spaces with words
          
          text.text(null);
          
          let line = [];
          let currentLine = text.append("tspan")
            .attr("x", -10)
            .attr("dy", "0em");
          
          words.forEach((word, i) => {
            line.push(word);
            currentLine.text(line.join(""));
            
            if (currentLine.node().getComputedTextLength() > maxWidth && line.length > 1) {
              line.pop();
              currentLine.text(line.join(""));
              
              line = [word];
              currentLine = text.append("tspan")
                .attr("x", -10)
                .attr("dy", "1.2em")
                .text(word);
            }
          });
        });
      })
      .on("click", (event, d) => {
        const item = data.find(item => item.title === d);
        if (item && onClickHandler) {
          onClickHandler(item);
        }
      });

    // Create bar groups
    const barGroups = svg.selectAll(".bar-group")
      .data(data)
      .enter()
      .append("g")
      .attr("class", "bar-group")
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        if (onClickHandler) {
          onClickHandler(d);
        }
      });
  
    // Create visible bars
    barGroups.append("rect")
      .attr("class", "bar")
      .attr("y", d => y(d.title))
      .attr("height", y.bandwidth())
      .attr("x", 0)
      .attr("width", d => x(d.value))
      .attr("fill", "rgb(17, 93, 115)");
  
    // Add tooltips
    const tooltip = d3.select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("opacity", 0)
      .style("position", "absolute")
      .style("background-color", "white")
      .style("border", "1px solid #ddd")
      .style("padding", "10px")
      .style("pointer-events", "none");
  
    barGroups.on("mouseover", (event, d) => {
      tooltip.transition()
        .duration(200)
        .style("opacity", .9);
      tooltip.html(valueFormatter(d.value))
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", () => {
      tooltip.transition()
        .duration(500)
        .style("opacity", 0);
    });
  
    // Add hover effect
    barGroups.selectAll(".bar")
      .on("mouseover", function() {
        d3.select(this).attr("fill", "rgb(14, 78, 96)");
      })
      .on("mouseout", function() {
        d3.select(this).attr("fill", "rgb(17, 93, 115)");
      });
}

function getFormattingInfo(data) {
  // Get the maximum value
  const maxValue = Math.max(...data.map(item => item.value));
  
  // Determine the appropriate divisor and suffix based on max value
  if (maxValue >= 1000000000000) {
    return { divisor: 1000000000000, suffix: 'T' };
  } else if (maxValue >= 1000000000) {
    return { divisor: 1000000000, suffix: 'B' };
  } else if (maxValue >= 1000000) {
    return { divisor: 1000000, suffix: 'M' };
  } else if (maxValue >= 1000) {
    return { divisor: 1000, suffix: 'K' };
  }
  return { divisor: 1, suffix: '' };
}

function formatAxisValues(value, divisor, suffix) {
  const scaled = value / divisor;
    // Check if the scaled value is a whole number
    return Number.isInteger(scaled) ? 
      `$${scaled}${suffix}` : 
      `$${scaled.toFixed(1)}${suffix}`;
}