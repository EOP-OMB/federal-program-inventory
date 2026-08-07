const defaultConfig = {
  axisFontSize: "20px",
  axisTickPadding: 20,
  endLabelFontSize: "20px",
  endLabelLineHeight: 20,
  endLabelXPadding: -10,
  endLabelYPadding: 10,
  fontFamily: "Inter",
  legendInnerPadding: 15,
  legendItemHeight: 30,
  legendItemLabelFontSize: "20px",
  legendItemLabelPadding: 10,
  legendItemLineX1: 10,
  legendItemLineX2: 40,
  legendItemPointRadius: 7,
  legendItemStrokeWidth: 4,
  legendOuterLeftPadding: 70,
  legendOutlineStrokeColor: "#cdcabd",
  legendOutlineStrokeWidth: 2,
  legendWidth: 250,
  margin: { top: 45, right: 25, bottom: 40, left: 90 },
  obligationsPointRadius: 7,
  obligationsStrokeColor: "#0A0A0A",
  obligationsStrokeWidth: 4,
  outlayFillColor: "#d4af3766",
  outlayFillStrokeWidth: "2.5px",
  outlaysPointRadius: 7,
  outlaysStrokeColor: "#AD854A",
  outlaysStrokeWidth: 4,
  revenueLossFillColor: "#b3c1c866",
  revenueLossFillStrokeWidth: "2.5px",
  revenueLossPointRadius: 7,
  revenueLossStrokeColor: "#7A878E",
  revenueLossStrokeWidth: 4,
  svgMaxWidth: "600px", // font-size can start to dominate the rest of the page
  svgWidth: "100%",
  viewBoxHeight: 500,
  viewBoxWidth: 1000
}

function createOutlaysVsSpendChart(containerId, data, programType, config = defaultConfig) {
  const chartWidth = config.viewBoxWidth - config.margin.left - config.margin.right - config.legendWidth - config.legendOuterLeftPadding;
  const chartHeight = config.viewBoxHeight - config.margin.top - config.margin.bottom;
  const isTaxExpenditure = programType === 'tax_expenditure';
  const hasRevenueLosses = _hasRevenueLosses(data);
  const shouldShowRevenueLossSeries = isTaxExpenditure && hasRevenueLosses;
  const stackedTaxExpenditureTotals = shouldShowRevenueLossSeries ? _buildTaxExpenditureStackedSeries(data) : [];
  const showOutlaysDatapoint = data.outlays.length > 0;
  const showRevenueLossDatapoint = stackedTaxExpenditureTotals.length > 0;
  const showObligationsDatapoint = data.obligations.length === 1;
  const showObligations = !isTaxExpenditure && programType !== 'interest';

  _resetContainer(containerId);
  const svg = _createSvg(containerId, config);

  const { xScale, yScale } = _createScales(data, chartWidth, chartHeight, stackedTaxExpenditureTotals);

  const { outlayFillGenerator, revenueLossFillGenerator, lineGenerator } = _createGenerators(xScale, yScale);

  let outlaysFillArea = null;
  let revenueLossFillArea = null;

  // if the length is 1, this will just draw a faint vertical line
  if (data.outlays.length > 1) {
    outlaysFillArea = _addOutlaysFillArea(svg, data, config, outlayFillGenerator);
  }

  if (stackedTaxExpenditureTotals.length > 1) {
    revenueLossFillArea = _addRevenueLossFillArea(svg, stackedTaxExpenditureTotals, config, revenueLossFillGenerator);
  }

  const { obligationsLine, outlaysLine, revenueLossLine } = _addLines({
    svg,
    data,
    config,
    lineGenerator,
    showObligations,
    stackedTaxExpenditureTotals,
    xScale,
    yScale
  });

  let obligationsPoint = null;
  let outlaysPoint = null;
  let revenueLossPoint = null;

  if (showOutlaysDatapoint) {
    outlaysPoint = _showOutlaysDataPoint(data, svg, xScale, yScale, config);
  }

  if (showObligationsDatapoint && showObligations) {
    obligationsPoint = _showObligationsDataPoint(data, svg, xScale, yScale, config);
  }
  if (showRevenueLossDatapoint) {
    revenueLossPoint = _showRevenueLossDataPoint(stackedTaxExpenditureTotals, svg, xScale, yScale, config);
  }

  _addXAxis(xScale, svg, chartHeight, config);
  _addYAxis(yScale, svg, chartHeight, config);

  _addLegend({
    svg,
    chartWidth,
    config,
    chartHeight,
    showObligationsDatapoint,
    showOutlaysDatapoint,
    showRevenueLossDatapoint,
    obligationsLine,
    outlaysLine,
    revenueLossLine,
    outlaysFillArea,
    revenueLossFillArea,
    obligationsPoint,
    outlaysPoint,
    revenueLossPoint,
    data,
    shouldShowRevenueLossSeries
  });

  _addTooltip(svg, chartWidth, chartHeight, config, xScale, data, yScale, showObligations, programType, stackedTaxExpenditureTotals, shouldShowRevenueLossSeries);

  _addEndValueLabels(svg, data, xScale, yScale, config, stackedTaxExpenditureTotals, shouldShowRevenueLossSeries);
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
  const revenueLossFillGenerator = d3.area()
    .x(d => xScale(d.year))
    .y0(d => yScale(d.outlaysValue))
    .y1(d => yScale(d.totalValue))
    .curve(d3.curveMonotoneX);
  return { outlayFillGenerator, revenueLossFillGenerator, lineGenerator };
}

function _addTooltip(svg, chartWidth, chartHeight, config, xScale, data, yScale, showObligations, programType, stackedTaxExpenditureTotals, shouldShowRevenueLossSeries) {
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

  const hoverCircleRevenueLosses = svg.append("circle")
    .attr("r", config.revenueLossPointRadius)
    .attr("fill", config.revenueLossStrokeColor)
    .style("opacity", 0);

  const revenueLossLookup = new Map((data.revenueLosses || []).map(d => [d.year, d]));
  const stackedLookup = new Map(stackedTaxExpenditureTotals.map(d => [d.year, d]));

  overlay.on("mousemove", function (event) {
    const [mouseX] = d3.pointer(event, this);
    const year = xScale.invert(mouseX);
    const nearestYear = Math.round(year);

    const outlayPoint = data.outlays.find(d => d.year === nearestYear);
    const obligationPoint = data.obligations.find(d => d.year === nearestYear);
    const revenueLossPoint = revenueLossLookup.get(nearestYear);
    const stackedPoint = stackedLookup.get(nearestYear);

    if (outlayPoint || obligationPoint) {
      const x = xScale(nearestYear);

      hoverLine
        .attr("x1", x)
        .attr("x2", x)
        .attr("y1", 0)
        .attr("y2", chartHeight)
        .style("opacity", 1);

      const tooltipEntries = [];

      if (obligationPoint && showObligations) {
        const y = yScale(obligationPoint.value);
        hoverCircleObligations
          .attr("cx", x)
          .attr("cy", y)
          .style("opacity", 1);
        const obligationsDataSource = resolveProgramDataSource({
          programType,
          dataType: 'obligations',
          year: nearestYear,
          data
        });
        tooltipEntries.push({
          label: 'Obligations',
          valueText: formatDollarAmount(obligationPoint.value),
          dataSource: obligationsDataSource
        });
      } else {
        hoverCircleObligations.style("opacity", 0);
      }

      if (outlayPoint) {
        const y = yScale(outlayPoint.value);
        hoverCircleOutlays
          .attr("cx", x)
          .attr("cy", y)
          .style("opacity", 1);
        const outlaysDataSource = resolveProgramDataSource({
          programType,
          dataType: 'outlays',
          year: nearestYear,
          data
        });
        tooltipEntries.push({
          label: 'Outlays',
          valueText: formatDollarAmount(outlayPoint.value),
          dataSource: outlaysDataSource
        });
      } else {
        hoverCircleOutlays.style("opacity", 0);
      }

      if (shouldShowRevenueLossSeries && revenueLossPoint && stackedPoint) {
        hoverCircleRevenueLosses
          .attr("cx", x)
          .attr("cy", yScale(stackedPoint.totalValue))
          .style("opacity", 1);

        const revenueLossesDataSource = resolveProgramDataSource({
          programType,
          dataType: 'revenue_losses',
          year: nearestYear,
          data
        });
        tooltipEntries.push({
          label: 'Revenue Losses',
          valueText: formatDollarAmount(revenueLossPoint.value),
          dataSource: revenueLossesDataSource
        });
      } else {
        hoverCircleRevenueLosses.style("opacity", 0);
      }

      const tooltipContent = formatProgramTooltipLinesWithSharedDataSource(`Year: ${nearestYear}`, tooltipEntries);

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
      hoverCircleRevenueLosses.style("opacity", 0);
      tooltip.style("opacity", 0);
    });
}

function _addLegend({
  svg,
  chartWidth,
  config,
  chartHeight,
  showObligationsDatapoint,
  showOutlaysDatapoint,
  showRevenueLossDatapoint,
  obligationsLine,
  outlaysLine,
  revenueLossLine,
  outlaysFillArea,
  revenueLossFillArea,
  obligationsPoint,
  outlaysPoint,
  revenueLossPoint,
  data,
  shouldShowRevenueLossSeries
}) {
  const legend = svg.append("g")
    .attr("class", "legend")
    .attr("transform", `translate(${chartWidth + config.legendOuterLeftPadding}, ${chartHeight / 2})`)
    .attr("pointer-events", "all");
  const legendItems = [];

  if (data.outlays.length > 0) {
    legendItems.push({ label: "Outlays", color: config.outlaysStrokeColor, hasPoint: showOutlaysDatapoint, line: outlaysLine, point: outlaysPoint, strokeWidthKey: "outlaysStrokeWidth" });
  }

  if (shouldShowRevenueLossSeries) {
    legendItems.push({ label: "Revenue Losses", color: config.revenueLossStrokeColor, hasPoint: showRevenueLossDatapoint, line: revenueLossLine, point: revenueLossPoint, strokeWidthKey: "revenueLossStrokeWidth" });
  }

  if (data.obligations.length > 0 && obligationsLine !== null) {
    legendItems.push({ label: "Obligations", color: config.obligationsStrokeColor, hasPoint: showObligationsDatapoint, line: obligationsLine, point: obligationsPoint, strokeWidthKey: "obligationsStrokeWidth" });
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
            .attr("stroke-width", config[item.strokeWidthKey] * 2)
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
          if (revenueLossFillArea !== null) {
            revenueLossFillArea.raise();
          }

          if (item.point) {
            item.point.raise();
          }

          d3.selectAll(".x-axis").raise();
          d3.selectAll(".y-axis").raise();
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

function _showRevenueLossDataPoint(stackedTaxExpenditureTotals, svg, xScale, yScale, config) {
  const lastStackedPoint = stackedTaxExpenditureTotals[stackedTaxExpenditureTotals.length - 1];
  return svg.append("circle")
    .attr("cx", xScale(lastStackedPoint.year))
    .attr("cy", yScale(lastStackedPoint.totalValue))
    .attr("r", config.revenueLossPointRadius)
    .attr("fill", config.revenueLossStrokeColor);
}

function _addLines({ svg, data, config, lineGenerator, showObligations, stackedTaxExpenditureTotals, xScale, yScale }) {
  let obligationsLine = null;
  let revenueLossLine = null;
  if (showObligations) {
    obligationsLine = svg.append("path")
      .datum(data.obligations)
      .attr("fill", "none")
      .attr("stroke", config.obligationsStrokeColor)
      .attr("stroke-width", config.obligationsStrokeWidth)
      .attr("d", lineGenerator);
  }

  const outlaysLine = svg.append("path")
    .datum(data.outlays)
    .attr("fill", "none")
    .attr("stroke", config.outlaysStrokeColor)
    .attr("stroke-width", config.outlaysStrokeWidth)
    .attr("d", lineGenerator);

  if (stackedTaxExpenditureTotals.length > 0) {
    revenueLossLine = svg.append("path")
      .datum(stackedTaxExpenditureTotals)
      .attr("fill", "none")
      .attr("stroke", config.revenueLossStrokeColor)
      .attr("stroke-width", config.revenueLossStrokeWidth)
      .attr("d", d3.line()
        .x(d => xScale(d.year))
        .y(d => yScale(d.totalValue))
        .curve(d3.curveMonotoneX));
  }
  return { obligationsLine, outlaysLine, revenueLossLine };
}

function _addEndValueLabels(svg, data, xScale, yScale, config, stackedTaxExpenditureTotals, shouldShowRevenueLossSeries) {
  const lastOutlaysPoint = data.outlays?.[data.outlays.length - 1];
  const lastObligationsPoint = data.obligations?.[data.obligations.length - 1];
  const lastStackedPoint = stackedTaxExpenditureTotals?.[stackedTaxExpenditureTotals.length - 1];

  const labelDefs = [
    lastOutlaysPoint
      ? { point: lastOutlaysPoint, color: config.outlaysStrokeColor }
      : null,
    lastObligationsPoint
      ? { point: lastObligationsPoint, color: config.obligationsStrokeColor }
      : null,
    (shouldShowRevenueLossSeries && lastStackedPoint)
      ? { point: { year: lastStackedPoint.year, value: lastStackedPoint.totalValue }, color: config.revenueLossStrokeColor }
      : null,
  ].filter(Boolean);

  let lastLabelY = null;
  labelDefs.forEach(({ point, color }) => {
    let currentLabelY = yScale(point.value) - config.endLabelYPadding;
    if (lastLabelY && Math.abs(lastLabelY - currentLabelY) < config.endLabelLineHeight) {
      // shift label to avoid overlap
      const direction = (lastLabelY >= currentLabelY ? -1 : 1);
      currentLabelY = lastLabelY + direction * config.endLabelLineHeight;
    }

    svg.append("text")
      .attr("x", xScale(point.year) - config.endLabelXPadding)
      .attr("y", currentLabelY)
      .attr("text-anchor", "start")
      .attr("font-size", config.endLabelFontSize)
      .attr("font-family", config.fontFamily)
      .attr("fill", color)
      .attr("pointer-events", "none")
      .text(formatDollarAmount(point.value));
    lastLabelY = currentLabelY;
  });
}

function _addOutlaysFillArea(svg, data, config, outlayFillGenerator) {
  return svg.append("path")
    .datum(data.outlays)
    .attr("fill", config.outlayFillColor)
    .attr("stroke", config.outlayFillColor)
    .attr("stroke-width", config.outlayFillStrokeWidth)
    .attr("d", outlayFillGenerator);
}

function _addRevenueLossFillArea(svg, stackedTaxExpenditureTotals, config, revenueLossFillGenerator) {
  return svg.append("path")
    .datum(stackedTaxExpenditureTotals)
    .attr("fill", config.revenueLossFillColor)
    .attr("stroke", config.revenueLossFillColor)
    .attr("stroke-width", config.revenueLossFillStrokeWidth)
    .attr("d", revenueLossFillGenerator);
}

function _addXAxis(xScale, svg, chartHeight, config) {
  const xAxis = d3.axisBottom(xScale)
    .tickFormat((d, i, ticks) => { return d; })
    .tickValues([xScale.domain()[0], xScale.domain()[1]])
    .tickPadding(config.axisTickPadding);
  svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${chartHeight})`)
    .call(xAxis)
    .selectAll("text")
    .style("font-size", config.axisFontSize)
    .style("font-family", config.fontFamily);
}

function _addYAxis(yScale, svg, chartHeight, config) {
  const yAxis = d3.axisLeft(yScale)
    .tickFormat((d, i, ticks) => { return formatDollarAmount(d); })
    .tickValues([yScale.domain()[0], yScale.domain()[1]])
    .tickPadding(config.axisTickPadding);
  svg.append("g")
    .attr("class", "y-axis")
    .attr("transform", `translate(0,0)`)
    .call(yAxis)
    .selectAll("text")
    .style("font-size", config.axisFontSize)
    .style("font-family", config.fontFamily);
}

function _createScales(data, chartWidth, chartHeight, stackedTaxExpenditureTotals = []) {
  const combinedSeries = [...data.outlays, ...data.obligations, ...stackedTaxExpenditureTotals.map(d => ({ year: d.year, value: d.totalValue }))];
  const xScaleMin = Math.min(...combinedSeries.map(item => item.year));
  const xScaleMax = Math.max(...combinedSeries.map(item => item.year));
  const yScaleMin = Math.min(...combinedSeries.map(item => item.value));
  const yScaleMax = Math.max(...combinedSeries.map(item => item.value));
  const xScale = d3.scaleLinear()
    .domain([xScaleMin, xScaleMax])
    .range([0, chartWidth]);
  const yScale = d3.scaleLinear()
    .domain([Math.min(yScaleMin, 0), Math.max(yScaleMax, 0)])
    .range([chartHeight, 0]);
  return { xScale, yScale };
}

function _hasRevenueLosses(data) {
  return Array.isArray(data.revenueLosses) && data.revenueLosses.some(d => d.value !== null && d.value !== 0);
}

function _buildTaxExpenditureStackedSeries(data) {
  const revenueLossLookup = new Map((data.revenueLosses || []).map(d => [d.year, d.value]));
  return (data.outlays || []).map(outlayPoint => {
    const revenueLossValue = revenueLossLookup.get(outlayPoint.year) || 0;
    return {
      year: outlayPoint.year,
      outlaysValue: outlayPoint.value,
      totalValue: outlayPoint.value + revenueLossValue
    };
  });
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
  const programType = chartElement ? chartElement.getAttribute('data-program-type') : null;
  const formattedData = standardizeDataForD3(rawData, programType !== 'tax_expenditure');

  if (formattedData.obligations.length > 0 || formattedData.outlays.length > 0) {
    createOutlaysVsSpendChart('#' + id, formattedData, programType);
  } else {
    document.getElementById(chartHeaderId)?.classList.add('hide');
    document.getElementById(noChartId)?.classList.remove('hide');
  }
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { createOutlaysVsSpendChart, defaultConfig };
}