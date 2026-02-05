module CategoryFilter
  def parse_categories(categories)
    return {"main" => [], "sub" => []} if categories.nil? || !categories.is_a?(Array)
    
    main_categories = []
    sub_categories = []
    
    categories.each do |category|
      if category.include?(' - ')
        parts = category.split(' - ', 2)
        main_cat = parts[0].strip
        sub_cat = parts[1].strip
        
        main_categories << main_cat unless main_categories.include?(main_cat)
        sub_categories << sub_cat
      end
    end
    
    {"main" => main_categories, "sub" => sub_categories}
  end
end

Liquid::Template.register_filter(CategoryFilter)