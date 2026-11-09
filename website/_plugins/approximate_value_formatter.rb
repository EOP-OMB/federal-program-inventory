module ApproximateValueFormatter
  # Round a positive count down to the previous multiple of `bucket` and append "+".
  # Zero stays "0". When the rounded value is 0, the exact count is shown instead.
  # An exact multiple steps down one bucket (2450 / 50 -> 2400+).
  # Homepage front matter may include commas and a trailing space.
  def approximate_count(value, bucket)
    return '' if value.nil?

    raw = value.to_s.strip
    return raw if raw.empty?

    digits = raw.delete(',')
    return raw unless digits.match?(/\A\d+\z/)

    count = digits.to_i
    return '0' if count.zero?

    step = bucket.to_i
    return raw if step <= 0

    approximated = ((count - 1) / step) * step

    # if the approximated value is 0, show the exact count (so we don't show "0+")
    return whole_number_with_comma(count) if approximated.zero?

    "#{whole_number_with_comma(approximated)}+"
  end
end

Liquid::Template.register_filter(ApproximateValueFormatter)