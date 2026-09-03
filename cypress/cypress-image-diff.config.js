const config = {
  FAILURE_THRESHOLD: 0.01,
  // pixelmatch: treat anti-aliased fringe pixels more leniently
  COMPARISON_OPTIONS: {
    threshold: 0.1,
    includeAA: true,
  },
};

module.exports = config;
