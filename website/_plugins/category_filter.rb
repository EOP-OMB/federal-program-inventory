module CategoryFilter
  def parse_category(category)
    return {"main" => "", "sub" => ""} if category.nil? || !category.is_a?(String)

    main_cat = category.strip
    sub_cat = ""
    if category.include?(' - ')
      parts = category.split(' - ', 2)
      main_cat = parts[0].strip
      sub_cat = parts[1].strip
    end

    {"main" => main_cat, "sub" => sub_cat}
  end

  def whole_number_with_comma(value)
    return '' if value.nil?

    str = value.to_s.strip
    return str if str.empty?

    str.sub(/\A(-?\d+)(\.\d+)?\z/) do
      "#{$1.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}#{$2}"
    end
  end
end

Liquid::Template.register_filter(CategoryFilter)