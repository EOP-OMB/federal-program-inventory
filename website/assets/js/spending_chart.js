const spendingChartDefaultConfig = {
  axisAlignementBaseline: "middle",
  axisFont: "Inter",
  axisFontSize: "18px",
  axisTextAnchor: "end",
  barPadding: 0.3,
  diagonalPatternSquareSide: 10,
  diagonalStrokeColor: "white",
  diagonalStrokeWidth: 2,
  inflationToggleClass: 'spending-chart-toggle',
  labelColor: "#0A0A0A",
  labelFinalColor: "#0A0A0A",
  labelFontSize: "16px",
  labelMinimumBarSize: 25,
  labelRelativeLocation: 5,
  labelRelativeLocationNegative: 22,
  labelTextAnchor: "middle",
  margin: { top: 30, right: 40, bottom: 40, left: 70 },
  obligationLineColor: "#0A0A0A",
  obligationLineWidth: 3,
  outlayBarColor: "#d4af37cc",
  outlayBarFinalColor: "#d4af37cc",
  outlayBarFinalFill: "url(#outlays-diagonal-stripe)",
  projectedLineColor: "#0A0A0A",
  projectedLineDashArray: "8,8",
  projectedLineWidth: 4,
  projectionLegendEntry: 'projection-legend-entry',
  projectionLegendEntryHeading: 'projection-legend-entry-heading',
  revenueLossBarColor: "#b3c1c8",
  revenueLossBarFinalColor: "#b3c1c8",
  revenueLossBarFinalFill: "url(#rev-losses-diagonal-stripe)",
  revenueLossLegendEntry: 'revenue-loss-legend-entry',
  revenueLossLegendEntryCurrentYear: 'revenue-loss-legend-entry-cy',
  svgMaxWidth: "1600px",
  svgWidth: "100%",
  tickMarkLabelX: -10,
  tickMarkX1: -5,
  tickMarkX2: 0,
  tooltipDashArray: "4,4",
  tooltipLineColor: "#999",
  tooltipLineWidth: 1,
  tooltipOpacity: 0,
  viewBoxHeight: 500,
  viewBoxWidth: 1000,
  xAxisColor: "#0A0A0A",
  xAxisLength: 890,
  xAxisMinSpaceAvailable: 30,
  xAxisWidth: 2,
  xAxisZeroLineWidth: 2,
  yAxisColor: "#0A0A0A",
  yAxisMinimumPercentageLesserSide: 0.2,
  yAxisWidth: 2
};

function createSpendingChart(containerId, data, programType, config = spendingChartDefaultConfig) {
  const chartWidth = config.viewBoxWidth - config.margin.left - config.margin.right;
  const chartHeight = config.viewBoxHeight - config.margin.top - config.margin.bottom;
  const showObligations = programType !== 'tax_expenditure' && programType !== 'interest'

  _resetSpendingContainer(containerId);
  const svg = _createSpendingSvg(containerId, config);

  const { xScale, yScale } = _createSpendingScales(data, chartWidth, chartHeight, config);

  _addOutlayBars(svg, data.outlays, xScale, yScale, config);
  _addRevenueLossBars(svg, data.revenueLosses, data.outlays, xScale, yScale, config);

  _addSpendingYAxis(svg, yScale, chartHeight, config);
  _addSpendingXAxis(svg, xScale, yScale, chartHeight, config);

  _addBarLabels(svg, data.barLabels, data.obligations, xScale, yScale, config);

  if (showObligations) {
    _addObligationLines(svg, data.obligations, xScale, yScale, config);
  }

  _addProjectedLine(svg, data.projectedOutlays, xScale, yScale, config);

  _addSpendingTooltip(svg, chartWidth, chartHeight, config, xScale, yScale, data, showObligations, programType);
}

function _resetSpendingContainer(containerId) {
  d3.select(containerId).selectAll("*").remove();
}

function _createSpendingSvg(containerId, config) {
  const svg = d3.select(containerId)
    .append("svg")
    .attr("width", config.svgWidth)
    .attr("viewBox", `0 0 ${config.viewBoxWidth} ${config.viewBoxHeight}`)
    .attr("style", `max-width: ${config.svgMaxWidth}`)
    .append("g")
    .attr("transform", `translate(${config.margin.left},${config.margin.top})`);

  const defs = svg.append("defs");

  addDiagonalPattern("outlays-diagonal-stripe", config.outlayBarFinalColor);
  addDiagonalPattern("rev-losses-diagonal-stripe", config.revenueLossBarFinalColor);

  return svg;

  function addDiagonalPattern(id, fillColor) {
    const diagonalPattern = defs.append("pattern")
      .attr("id", id)
      .attr("patternUnits", "userSpaceOnUse")
      .attr("width", config.diagonalPatternSquareSide)
      .attr("height", config.diagonalPatternSquareSide);

    diagonalPattern.append("rect")
      .attr("width", config.diagonalPatternSquareSide)
      .attr("height", config.diagonalPatternSquareSide)
      .attr("fill", fillColor);

    diagonalPattern.append("path")
      .attr("d", "M-1,1 l2,-2 M0,10 l10,-10 M9,11 l2,-2") // Stripe shape
      .attr("stroke", config.diagonalStrokeColor)
      .attr("stroke-width", config.diagonalStrokeWidth);
  }
}

function _valueOrZero(value) {
  return value === null || value === undefined ? 0 : value;
}

function _createSpendingScales(data, chartWidth, chartHeight, config) {
  const years = data.outlays.map(d => d.year);

  const revenueLossLookup = new Map(data.revenueLosses.map(d => [d.year, _valueOrZero(d.value)]));

  const stackedOutlayTotals = data.outlays.map(d => _valueOrZero(d.value) + _valueOrZero(revenueLossLookup.get(d.year)));

  const allValues = [
    ...data.outlays.map(d => _valueOrZero(d.value)),
    ...data.revenueLosses.map(d => _valueOrZero(d.value)),
    ...stackedOutlayTotals,
    ...data.obligations.map(d => _valueOrZero(d.value)),
    ...data.projectedOutlays.filter(d => d.value !== null).map(d => d.value)
  ];
  
  let yMax = Math.max(...allValues);
  let yMin = Math.min(Math.min(...allValues), 0);

  const xScale = d3.scaleBand()
    .domain(years)
    .range([0, chartWidth])
    .padding(config.barPadding);

  // this ensures that the smaller side of the axis is always at least
  //   config.yAxisMinimumPercentageLesserSide of the larger side
  if (yMin < 0) {
    if (Math.abs(yMin) < Math.abs(yMax)) {
      if (Math.abs(yMin) / Math.abs(yMax) < config.yAxisMinimumPercentageLesserSide) {
        yMin = -config.yAxisMinimumPercentageLesserSide * yMax;
      }
    } else {
      if (Math.abs(yMax) / Math.abs(yMin) < config.yAxisMinimumPercentageLesserSide) {
        yMax = config.yAxisMinimumPercentageLesserSide * yMax;
      }
    }
  }

  const yScale = d3.scaleLinear()
    .domain([yMin, yMax])
    .range([chartHeight, 0]);

  return { xScale, yScale };
}

function _addSpendingYAxis(svg, yScale, chartHeight, config) {
  const yDomain = yScale.domain();
  
  svg.append("line")
    .attr("x1", 0)
    .attr("x2", 0)
    .attr("y1", yScale(yDomain[0]))
    .attr("y2", yScale(yDomain[1]))
    .attr("stroke", config.yAxisColor)
    .attr("stroke-width", config.yAxisWidth);

  svg.append("line")
    .attr("x1", config.tickMarkX1)
    .attr("x2", config.tickMarkX2)
    .attr("y1", yScale(yDomain[0]))
    .attr("y2", yScale(yDomain[0]))
    .attr("stroke", config.yAxisColor)
    .attr("stroke-width", config.yAxisWidth);

  svg.append("line")
    .attr("x1", config.tickMarkX1)
    .attr("x2", config.tickMarkX2)
    .attr("y1", yScale(yDomain[1]))
    .attr("y2", yScale(yDomain[1]))
    .attr("stroke", config.yAxisColor)
    .attr("stroke-width", config.yAxisWidth);

  svg.append("text")
    .attr("x", config.tickMarkLabelX)
    .attr("y", yScale(yDomain[0]))
    .attr("text-anchor", config.axisTextAnchor)
    .attr("alignment-baseline", config.axisAlignementBaseline)
    .style("font-size", config.axisFontSize)
    .style("font-family", config.axisFont)
    .text(formatDollarAmount(yDomain[0]));

  svg.append("text")
    .attr("x", config.tickMarkLabelX)
    .attr("y", yScale(yDomain[1]))
    .attr("text-anchor", config.axisTextAnchor)
    .attr("alignment-baseline", config.axisAlignementBaseline)
    .style("font-size", config.axisFontSize)
    .style("font-family", config.axisFont)
    .text(formatDollarAmount(yDomain[1]));

  if (yDomain[0] < 0) {
    svg.append("line")
      .attr("x1", 0)
      .attr("x2", config.xAxisLength)
      .attr("y1", yScale(0))
      .attr("y2", yScale(0))
      .attr("stroke", config.xAxisColor)
      .attr("stroke-width", config.xAxisZeroLineWidth);

    // prevent overlap of 0 and negative number
    if (yScale(0) >= config.xAxisMinSpaceAvailable) {
      svg.append("text")
        .attr("x", config.tickMarkLabelX)
        .attr("y", yScale(0))
        .attr("text-anchor", config.axisTextAnchor)
        .attr("alignment-baseline", config.axisAlignementBaseline)
        .style("font-size", config.axisFontSize)
        .style("font-family", config.axisFont)
        .text("$0");
    }
  }
}

function _addSpendingXAxis(svg, xScale, yScale, chartHeight, config) {
  const yDomain = yScale.domain();

  const xAxis = d3.axisBottom(xScale)
    .tickFormat(d => d)
    .tickSizeOuter(0);

  const xAxisElement = svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${chartHeight})`)
    .call(xAxis);

  xAxisElement.selectAll("text")
    .style("font-size", config.axisFontSize)
    .style("font-family", config.axisFont);

  xAxisElement.select(".domain")
    .style("stroke-width", yDomain[0] === 0 ? config.xAxisWidth : 0)
    .style("stroke", config.xAxisColor);
}

function _addOutlayBars(svg, outlays, xScale, yScale, config) {
  svg.selectAll(".outlay-bar")
    .data(outlays)
    .enter()
    .append("rect")
    .attr("class", "outlay-bar")
    .attr("x", d => xScale(d.year))
    .attr("y", d => d.value > 0 ? yScale(d.value) : yScale(0))
    .attr("width", xScale.bandwidth())
    .attr("height", d => Math.abs(yScale(0) - yScale(d.value)))
    .attr("fill", (d, i) => i === outlays.length - 1 ? config.outlayBarFinalFill : config.outlayBarColor);
}

function _addRevenueLossBars(svg, revenueLosses, outlays, xScale, yScale, config) {
  if (!Array.isArray(revenueLosses) || revenueLosses.filter(p => p.value !== 0).length === 0) {
    document.getElementById(config.revenueLossLegendEntry).classList.add('hide');
    document.getElementById(config.revenueLossLegendEntryCurrentYear).classList.add('hide');
    return;
  }

  const outlayLookup = new Map((outlays || []).map(d => [d.year, _valueOrZero(d.value)]));

  svg.selectAll(".revenue-loss-bar")
    .data(revenueLosses)
    .enter()
    .append("rect")
    .attr("class", "revenue-loss-bar")
    .attr("x", d => xScale(d.year))
    .attr("y", (d) => {
      const base = _valueOrZero(outlayLookup.get(d.year));
      const total = base + _valueOrZero(d.value);
      return yScale(Math.max(base, total));
    })
    .attr("width", xScale.bandwidth())
    .attr("height", (d) => {
      const base = _valueOrZero(outlayLookup.get(d.year));
      const total = base + _valueOrZero(d.value);
      return Math.abs(yScale(base) - yScale(total));
    })
    .attr("fill", (d, i) => i === revenueLosses.length - 1 ? config.revenueLossBarFinalFill : config.revenueLossBarColor);
}

function _addBarLabels(svg, outlaysAndRevenueLosses, obligations, xScale, yScale, config) {
  svg.selectAll(".bar-label")
    .data(outlaysAndRevenueLosses)
    .enter()
    .append("text")
    .attr("class", "bar-label")
    .attr("x", d => xScale(d.year) + xScale.bandwidth() / 2)
    // show above / below y axis based on sign of value
    .attr("y", d => yScale(0) +
      (d.value > 0 ? -config.labelRelativeLocation : config.labelRelativeLocationNegative))
    .attr("text-anchor", config.labelTextAnchor)
    .style("font-size", config.labelFontSize)
    .style("font-family", config.axisFont)
    .style("fill", (d, i) => i === outlaysAndRevenueLosses.length - 1 ? config.labelFinalColor : config.labelColor)
    // hide labels for small or covered bars
    .style("opacity", (d, i) => {
      const noOutlays = d.value === null || d.value === 0;

      const barIsSmall = Math.abs(yScale(0) - yScale(d.value)) < config.labelMinimumBarSize;

      const obligationsPosition = yScale(obligations[i].value);

      let obligationsWouldCover = false;
      if (d.value > 0 && obligations[i].value > 0 && yScale(0) - obligationsPosition < config.labelMinimumBarSize) {
        obligationsWouldCover = true;
      }

      if (d.value < 0 && obligations[i].value < 0 && obligationsPosition - yScale(0) < config.labelMinimumBarSize) {
        obligationsWouldCover = true;
      }

      return noOutlays || barIsSmall || obligationsWouldCover ? 0 : 1;
    })
    .text(d => formatDollarAmount(d.value));
}

function _addObligationLines(svg, obligations, xScale, yScale, config) {
  svg.selectAll(".obligation-line")
    .data(obligations.filter(d => d.value !== null))
    .enter()
    .append("line")
    .attr("class", "obligation-line")
    .attr("x1", d => xScale(d.year))
    .attr("x2", d => xScale(d.year) + xScale.bandwidth())
    .attr("y1", d => yScale(d.value))
    .attr("y2", d => yScale(d.value))
    .attr("stroke", config.obligationLineColor)
    .attr("stroke-width", config.obligationLineWidth);
}

function _addProjectedLine(svg, projectedOutlays, xScale, yScale, config) {
  const validProjectedData = projectedOutlays.filter(d => d.value !== null);
  const toggles = document.getElementsByClassName(config.inflationToggleClass);
  
  if (validProjectedData.length < 2) {
    document.getElementById(config.projectionLegendEntry).classList.add('hide');
    document.getElementById(config.projectionLegendEntryHeading).classList.add('hide');

    return;
  }

  const lineGenerator = d3.line()
    .x(d => xScale(d.year) + xScale.bandwidth() / 2)
    .y(d => yScale(d.value))
    .curve(d3.curveMonotoneX);

  const projectionLine = svg.append("path")
    .datum(validProjectedData)
    .attr("class", "projected-line")
    .attr("fill", "none")
    .attr("stroke", config.projectedLineColor)
    .attr("stroke-width", config.projectedLineWidth)
    .attr("stroke-dasharray", config.projectedLineDashArray)
    .attr("d", lineGenerator);

  for (let i = 0; i < toggles.length; i++) {
    toggles[i].addEventListener('change', function() {
      projectionLine.attr('opacity', this.checked ? 1 : 0);
    });
  }
}

function _addSpendingTooltip(svg, chartWidth, chartHeight, config, xScale, yScale, data, showObligations, programType) {
  const tooltip = d3.select("body").append("div")
    .attr("class", "spending-chart-tooltip")
    .property("hidden", true);

  const overlay = svg.append("rect")
    .attr("width", chartWidth)
    .attr("height", chartHeight)
    .attr("fill", "none")
    .attr("pointer-events", "all");

  const hoverLine = svg.append("line")
    .attr("stroke", config.tooltipLineColor)
    .attr("stroke-width", config.tooltipLineWidth)
    .attr("stroke-dasharray", config.tooltipDashArray)
    .style("opacity", config.tooltipOpacity);

  overlay.on("mousemove", function (event) {
    const [mouseX] = d3.pointer(event, this);
    
    const years = xScale.domain();
    let nearestYear = null;
    let minDistance = Infinity;
    
    years.forEach(year => {
      const barCenter = xScale(year) + xScale.bandwidth() / 2;
      const distance = Math.abs(mouseX - barCenter);
      if (distance < minDistance) {
        minDistance = distance;
        nearestYear = year;
      }
    });

    if (nearestYear !== null) {
      const outlayPoint = data.outlays.find(d => d.year === nearestYear);
      const obligationPoint = data.obligations.find(d => d.year === nearestYear);
      const revenueLossPoint = data.revenueLosses.find(d => d.year === nearestYear && d.value !== null);
      const hasRevenueLosses = data.revenueLosses.filter(d => d.value !== null && d.value !== 0).length > 0;

      const x = xScale(nearestYear) + xScale.bandwidth() / 2;

      hoverLine
        .attr("x1", x)
        .attr("x2", x)
        .attr("y1", 0)
        .attr("y2", chartHeight)
        .style("opacity", 1);

      const tooltipEntries = [];

      if (outlayPoint) {
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
      }

      if (hasRevenueLosses && revenueLossPoint) {
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
      }

      if (obligationPoint && showObligations) {
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
      }

      const tooltipContent = formatProgramTooltipLinesWithSharedDataSource(`Year: ${nearestYear}`, tooltipEntries);

      tooltip
        .html(tooltipContent)
        .style("left", (event.pageX + 15) + "px")
        .style("top", (event.pageY - 15) + "px")
        .property("hidden", false);
    }
  })
    .on("mouseout", function () {
      hoverLine.style("opacity", 0);
      tooltip.property("hidden", true);
    });
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

function prepareData(chartElement, spendingData, currentYear, initialYear, baselineInflationYear, config = spendingChartDefaultConfig) {
  const inflationData = JSON.parse(chartElement.getAttribute('data-inflation'));

  if (!Array.isArray(spendingData.outlays)) {
    spendingData.outlays = [];
  }

  if (!Array.isArray(spendingData.obligations)) {
    spendingData.obligations = [];
  }

  if (!Array.isArray(spendingData.revenueLosses)) {
    spendingData.revenueLosses = [];
  }

  const originalBaseline = spendingData.outlays.find(d => d.year === baselineInflationYear && d.value !== null && d.value > 0);
  spendingData.projectedOutlays = [];
  spendingData.barLabels = [];

  if (inflationData && originalBaseline !== undefined) {
    const inflationDataLookup = inflationData.reduce((accumulator, item) => {
      accumulator[item.Year] = item.InflationRatePercentage + item.PopulationGrowthPercentage;
      return accumulator;
    }, {});

    let projectedValue = null;
    // less than, because current year inflation numbers are not available yet
    for (let year = baselineInflationYear; year < currentYear; ++year) {
      if (projectedValue === null) {
        projectedValue = originalBaseline.value;
      } else {
        projectedValue = projectedValue * (1 + inflationDataLookup[year - 1]);
      }
      spendingData.projectedOutlays.push({
        year: year,
        value: projectedValue
      });
    }
  }

  // fix data gaps
  for (let year = initialYear; year <= currentYear; ++year) {
    if (spendingData.outlays.filter(d => d.year === year).length === 0) {
      spendingData.outlays.push({
        year: year,
        value: 0
      })
    }

    if (spendingData.obligations.filter(d => d.year === year).length === 0) {
      spendingData.obligations.push({
        year: year,
        value: 0
      })
    }

    if (spendingData.revenueLosses.filter(d => d.year === year).length === 0) {
      spendingData.revenueLosses.push({
        year: year,
        value: 0
      })
    }
  }

  spendingData.obligations = spendingData.obligations.filter(d => d.year >= initialYear && d.year <= currentYear);
  spendingData.outlays = spendingData.outlays.filter(d => d.year >= initialYear && d.year <= currentYear);
  spendingData.revenueLosses = spendingData.revenueLosses.filter(d => d.year >= initialYear && d.year <= currentYear);

  spendingData.obligations.sort((a,b) => a.year - b.year);
  spendingData.outlays.sort((a,b) => a.year - b.year);
  spendingData.revenueLosses.sort((a,b) => a.year - b.year);

  for (let i = 0; i < spendingData.outlays.length; ++i) {
    spendingData.barLabels.push({
      year: spendingData.outlays[i].year,
      value: spendingData.outlays[i].value + spendingData.revenueLosses[i].value
    })
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const chartId = 'spending-chart';
  const noChartId = 'no-spending-chart';
  const spendingChartCardId = 'spending-chart-card';
  const toggleId = 'projection-toggle';
  const chartElement = document.getElementById(chartId);
  const rawData = _tryParsingRawData(chartElement);
  const spendingData = standardizeDataForD3(rawData, false);

  const hasOutlays = spendingData && spendingData.outlays &&
    spendingData.outlays.filter(d => d.value !== null && d.value !== 0).length > 0;
  const hasObligations = spendingData && spendingData.obligations &&
    spendingData.obligations.filter(d => d.value !== null && d.value !== 0).length > 0;
  const hasRevenueLosses = spendingData && spendingData.revenueLosses &&
    spendingData.revenueLosses.filter(d => d.value !== null && d.value !== 0).length > 0;

  if ((hasOutlays || hasObligations || hasRevenueLosses) && chartElement) {
    const currentYear = parseInt(chartElement.getAttribute('data-current-year'), 10);
    const initialYear = parseInt(chartElement.getAttribute('data-initial-year'), 10);
    const baselineInflationYear = parseInt(chartElement.getAttribute('data-baseline-inflation-year'), 10);
    const programType = chartElement.getAttribute('data-program-type');

    prepareData(chartElement, spendingData, currentYear, initialYear, baselineInflationYear);
    createSpendingChart('#' + chartId, spendingData, programType);

    // toggle off projection by default
    document.getElementById(toggleId)?.click();
  } else {
    document.getElementById(noChartId)?.classList.remove('hide');
    document.getElementById(spendingChartCardId)?.classList.add('hide');
  }
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { createSpendingChart, spendingChartDefaultConfig };
}
