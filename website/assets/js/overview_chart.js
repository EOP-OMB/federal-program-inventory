const defaultConfig = {
  svgMaxWidth: "600px", // font-size can start to dominate the rest of the page
  margin: { top: 15, right: 25, bottom: 30, left: 25 },
  viewBoxWidth: 1000,
  viewBoxHeight: 500,
  legendWidth: 185,
  svgWidth: "100%",
  axisFontSize: "20px",
  outlayFillColor: "#E4DBA9",
  outlayFillStrokeWidth: "2.5px",
  outlaysStrokeColor: "#A4995B",
  outlaysStrokeWidth: 4,
  outlaysPointRadius: 7,
  obligationsStrokeColor: "#0A0A0A",
  obligationsStrokeWidth: 4,
  obligationsPointRadius: 7,
  legendItemHeight: 30,
  legendInnerPadding: 15,
  legendOuterLeftPadding: 10,
  legendOutlineStrokeColor: "#D6D3D1",
  legendOutlineStrokeWidth: 2,
  legendItemLineX1: 10,
  legendItemLineX2: 40,
  legendItemStrokeWidth: 4,
  legendItemPointRadius: 7,
  legendItemLabelPadding: 10,
  legendItemLabelFontSize: "20px"
}

function createOutlaysVsSpendChart(containerId, data, config = defaultConfig) {
  const chartWidth = config.viewBoxWidth - config.margin.left - config.margin.right - config.legendWidth;
  const chartHeight = config.viewBoxHeight - config.margin.top - config.margin.bottom;
  const showOutlaysDatapoint = data.outlays.length > 0;
  const showObligationsDatapoint = data.obligations.length === 1;

  _resetContainer(containerId);
  const svg = _createSvg(containerId, config);

  const { xScale, yScale } = _createScales(data, chartWidth, chartHeight);

  const { outlayFillGenerator, lineGenerator } = _createGenerators(xScale, yScale);

  let outlaysFillArea = null;

  // if the length is 1, this will just draw a faint vertical line
  if (data.outlays.length > 1) {
    outlaysFillArea = _addOutlaysFillArea(svg, data, config, outlayFillGenerator);
  }

  const { obligationsLine, outlaysLine } = _addLines(svg, data, config, lineGenerator);

  let obligationsPoint = null;
  let outlaysPoint = null;

  if (showOutlaysDatapoint) {
    outlaysPoint = _showOutlaysDataPoint(data, svg, xScale, yScale, config);
  }

  if (showObligationsDatapoint) {
    obligationsPoint = _showObligationsDataPoint(data, svg, xScale, yScale, config);
  }

  _addXAxis(xScale, svg, chartHeight, config);

  _addLegend(svg, chartWidth, config, chartHeight, showObligationsDatapoint, showOutlaysDatapoint, obligationsLine, outlaysLine, outlaysFillArea, obligationsPoint, outlaysPoint, data);

  _addTooltip(svg, chartWidth, chartHeight, config, xScale, data, yScale);
}

function _tryParsingRawData(chartElement) {
  let rawData = [];
  try {
    if (chartElement) {
      rawData = JSON.parse(chartElement.getAttribute('data-outlays'));
    }
  } catch (error) { }
  return rawData;
}

function _resetContainer(containerId) {
  d3.select(containerId).selectAll("*").remove();
}

function _createGenerators(xScale, yScale) {
  const lineGenerator = d3.line()
    .x(d => xScale(d.year))
    .y(d => yScale(d.value))
    .curve(d3.curveMonotoneX);
  const outlayFillGenerator = d3.area()
    .x(d => xScale(d.year))
    .y0(yScale(0))
    .y1(d => yScale(d.value))
    .curve(d3.curveMonotoneX);
  return { outlayFillGenerator, lineGenerator };
}

function _addTooltip(svg, chartWidth, chartHeight, config, xScale, data, yScale) {
  const tooltip = d3.select("body").append("div")
    .attr("class", "outlays-chart-tooltip");

  // Create invisible overlay for mouse tracking
  const overlay = svg.append("rect")
    .attr("width", chartWidth)
    .attr("height", chartHeight)
    .attr("fill", "none")
    .attr("pointer-events", "all");

  const hoverLine = svg.append("line")
    .attr("stroke", "#999")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "4,4")
    .style("opacity", 0);

  const hoverCircleOutlays = svg.append("circle")
    .attr("r", config.outlaysPointRadius)
    .attr("fill", config.outlaysStrokeColor)
    .style("opacity", 0);

  const hoverCircleObligations = svg.append("circle")
    .attr("r", config.obligationsPointRadius)
    .attr("fill", config.obligationsStrokeColor)
    .style("opacity", 0);

  overlay.on("mousemove", function (event) {
    const [mouseX] = d3.pointer(event, this);
    const year = xScale.invert(mouseX);
    const nearestYear = Math.round(year);

    const outlayPoint = data.outlays.find(d => d.year === nearestYear);
    const obligationPoint = data.obligations.find(d => d.year === nearestYear);

    if (outlayPoint || obligationPoint) {
      const x = xScale(nearestYear);

      hoverLine
        .attr("x1", x)
        .attr("x2", x)
        .attr("y1", 0)
        .attr("y2", chartHeight)
        .style("opacity", 1);

      let tooltipContent = `<strong>Year: ${nearestYear}</strong><br/>`;

      if (obligationPoint) {
        const y = yScale(obligationPoint.value);
        hoverCircleObligations
          .attr("cx", x)
          .attr("cy", y)
          .style("opacity", 1);
        tooltipContent += `Obligations: ${formatDollarAmount(obligationPoint.value)}<br/>`;
      } else {
        hoverCircleObligations.style("opacity", 0);
      }

      if (outlayPoint) {
        const y = yScale(outlayPoint.value);
        hoverCircleOutlays
          .attr("cx", x)
          .attr("cy", y)
          .style("opacity", 1);
        tooltipContent += `Outlays: ${formatDollarAmount(outlayPoint.value)}`;
      } else {
        hoverCircleOutlays.style("opacity", 0);
      }

      tooltip
        .html(tooltipContent)
        .style("left", (event.pageX + 15) + "px")
        .style("top", (event.pageY - 15) + "px")
        .style("opacity", 0.95);
    }
  })
    .on("mouseout", function () {
      hoverLine.style("opacity", 0);
      hoverCircleOutlays.style("opacity", 0);
      hoverCircleObligations.style("opacity", 0);
      tooltip.style("opacity", 0);
    });
}

function _addLegend(svg, chartWidth, config, chartHeight, showObligationsDatapoint, showOutlaysDatapoint, obligationsLine, outlaysLine, outlaysFillArea, obligationsPoint, outlaysPoint, data) {
  const legend = svg.append("g")
    .attr("class", "legend")
    .attr("transform", `translate(${chartWidth + config.legendOuterLeftPadding}, ${chartHeight / 2})`)
    .attr("pointer-events", "all");
  const legendItems = [];

  if (data.outlays.length > 0) {
    legendItems.push({ label: "Outlays", color: config.outlaysStrokeColor, style: "solid", hasPoint: showOutlaysDatapoint, line: outlaysLine, point: outlaysPoint });
  }

  if (data.obligations.length > 0) {
    legendItems.push({ label: "Obligations", color: config.obligationsStrokeColor, style: "solid", hasPoint: showObligationsDatapoint, line: obligationsLine, point: obligationsPoint });
  }

  const legendBoxHeight = legendItems.length * config.legendItemHeight + 2 * config.legendInnerPadding;

  legend.append("rect")
    .attr("x", 0)
    .attr("y", -legendBoxHeight / 2)
    .attr("width", config.legendWidth)
    .attr("height", legendBoxHeight)
    .attr("fill", "none")
    .attr("stroke", config.legendOutlineStrokeColor)
    .attr("stroke-width", config.legendOutlineStrokeWidth);

  legendItems.forEach((item, i) => {
    const yOffset = -legendBoxHeight / 2 + config.legendInnerPadding + i * config.legendItemHeight + config.legendItemHeight / 2;

    // Create a group for the entire legend item to make it easier to add hover effects
    const legendItemGroup = legend.append("g")
      .attr("class", "legend-item")
      .style("cursor", "pointer");

    // Add invisible rect for better hover area
    legendItemGroup.append("rect")
      .attr("x", 0)
      .attr("y", yOffset - config.legendItemHeight / 2)
      .attr("width", config.legendWidth)
      .attr("height", config.legendItemHeight)
      .attr("fill", "transparent");

    legendItemGroup.append("line")
      .attr("x1", config.legendItemLineX1)
      .attr("x2", config.legendItemLineX2)
      .attr("y1", yOffset)
      .attr("y2", yOffset)
      .attr("stroke", item.color)
      .attr("stroke-width", config.legendItemStrokeWidth);

    if (item.hasPoint) {
      legendItemGroup.append("circle")
        .attr("cx", config.legendItemLineX2)
        .attr("cy", yOffset)
        .attr("r", config.legendItemPointRadius)
        .attr("fill", item.color);
    }

    legendItemGroup.append("text")
      .attr("x", config.legendItemLineX2 + config.legendItemLabelPadding)
      .attr("y", yOffset)
      .attr("font-size", config.legendItemLabelFontSize)
      .attr("alignment-baseline", "middle")
      .text(item.label);

    // Add hover effects
    legendItemGroup
      .on("mouseenter", function() {
        if (item.line) {
          item.line.attr("data-original-stroke-width", item.line.attr("stroke-width"));

          // Increase stroke width and bring to front
          item.line
            .attr("stroke-width", config[item.label === "Obligations" ? "obligationsStrokeWidth" : "outlaysStrokeWidth"] * 2)
            .raise();

          if (item.point) {
            item.point.raise();
          }
        }
      })
      .on("mouseleave", function() {
        if (item.line) {
          const originalWidth = item.line.attr("data-original-stroke-width");
          item.line.attr("stroke-width", originalWidth);
        }

        // lower obligations to original place
        if (item.label === "Obligations") {
          // line should still be drawn over fill area
          item.line.lower();

          if (outlaysFillArea !== null) {
            outlaysFillArea.lower();
          }

          if (item.point) {
            item.point.raise();
          }
        }
      });
  });
}

function _showObligationsDataPoint(data, svg, xScale, yScale, config) {
  const lastObligationsPoint = data.obligations[data.obligations.length - 1];
  return svg.append("circle")
    .attr("cx", xScale(lastObligationsPoint.year))
    .attr("cy", yScale(lastObligationsPoint.value))
    .attr("r", config.obligationsPointRadius)
    .attr("fill", config.obligationsStrokeColor);
}

function _showOutlaysDataPoint(data, svg, xScale, yScale, config) {
  const lastOutlaysPoint = data.outlays[data.outlays.length - 1];
  return svg.append("circle")
    .attr("cx", xScale(lastOutlaysPoint.year))
    .attr("cy", yScale(lastOutlaysPoint.value))
    .attr("r", config.outlaysPointRadius)
    .attr("fill", config.outlaysStrokeColor);
}

function _addLines(svg, data, config, lineGenerator) {
  const obligationsLine = svg.append("path")
    .datum(data.obligations)
    .attr("fill", "none")
    .attr("stroke", config.obligationsStrokeColor)
    .attr("stroke-width", config.obligationsStrokeWidth)
    .attr("d", lineGenerator);
  const outlaysLine = svg.append("path")
    .datum(data.outlays)
    .attr("fill", "none")
    .attr("stroke", config.outlaysStrokeColor)
    .attr("stroke-width", config.outlaysStrokeWidth)
    .attr("d", lineGenerator);
  return { obligationsLine, outlaysLine };
}

function _addOutlaysFillArea(svg, data, config, outlayFillGenerator) {
  return svg.append("path")
    .datum(data.outlays)
    .attr("fill", config.outlayFillColor)
    .attr("stroke", config.outlayFillColor)
    .attr("stroke-width", config.outlayFillStrokeWidth)
    .attr("d", outlayFillGenerator);
}

function _addXAxis(xScale, svg, chartHeight, config) {
  const xAxis = d3.axisBottom(xScale)
    .tickFormat((d, i, ticks) => { return d; })
    .tickValues([xScale.domain()[0], xScale.domain()[1]]);
  svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${chartHeight})`)
    .call(xAxis)
    .selectAll("text")
    .style("font-size", config.axisFontSize)
    .style("font-family", "Inter");
}

function _createScales(data, chartWidth, chartHeight) {
  const combinedSeries = [...data.outlays, ...data.obligations];
  const xScaleMin = Math.min(...combinedSeries.map(item => item.year));
  const xScaleMax = Math.max(...combinedSeries.map(item => item.year));
  const yScaleMax = Math.max(...combinedSeries.map(item => item.value));
  const xScale = d3.scaleLinear()
    .domain([xScaleMin, xScaleMax])
    .range([0, chartWidth]);
  const yScale = d3.scaleLinear()
    .domain([0, yScaleMax])
    .range([chartHeight, 0]);
  return { xScale, yScale };
}

function _createSvg(containerId, config) {
  return d3.select(containerId)
    .append("svg")
    .attr("width", config.svgWidth)
    .attr("viewBox", `0 0 ${config.viewBoxWidth} ${config.viewBoxHeight}`)
    .attr("style", `max-width: ${config.svgMaxWidth}`)
    .append("g")
    .attr("transform", `translate(${config.margin.left},${config.margin.top})`);
}

document.addEventListener('DOMContentLoaded', function() {
  const id = 'chart';
  const chartHeaderId = 'chart-header';
  const noChartId = 'no-chart';
  const chartElement = document.getElementById(id);
  const rawData = _tryParsingRawData(chartElement);
  const formattedData = standardizeOutlaysAndObligationsForD3(rawData);

  if (formattedData.obligations.length > 0 || formattedData.outlays.length > 0) {
    createOutlaysVsSpendChart('#' + id, formattedData);
  } else {
    document.getElementById(chartHeaderId)?.classList.add('hide');
    document.getElementById(noChartId)?.classList.remove('hide');
  }
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { createOutlaysVsSpendChart, defaultConfig };
}