require 'bigdecimal'

module ImproperPaymentRateFormatter
  # Format an improper payment rate for display.
  #
  # +total+ is the improper payment dollar amount (page improper_payments_total,
  # or a row's improper payment amount).
  # A zero or missing total is "0%". Any other amount is rounded to the nearest
  # tenth. A non-zero amount that rounds to 0.0% is shown as "<0.1%".
  def improper_payment_rate(percent, total)
    return '0%' if zero_amount?(total)

    rounded = round_to_tenth(percent)
    return '<0.1%' if rounded.nil? || rounded.zero?

    "#{rounded.to_s('F')}"
  end

  private

  def zero_amount?(total)
    return true if total.nil?

    raw = total.to_s.strip
    return true if raw.empty?

    number = parse_number(raw)
    return false if number.nil?

    number.zero?
  end

  def round_to_tenth(percent)
    number = parse_number(percent)
    return nil if number.nil?

    number.round(1, BigDecimal::ROUND_HALF_UP)
  end

  def parse_number(value)
    raw = value.to_s.strip.delete(',')
    return nil if raw.empty?
    return nil unless raw.match?(/\A-?\d+(\.\d+)?(?:[eE][+-]?\d+)?\z/)

    BigDecimal(raw)
  end
end

Liquid::Template.register_filter(ImproperPaymentRateFormatter)
