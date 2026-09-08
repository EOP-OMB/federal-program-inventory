/**
 * Reusable filter-table component for taxonomy, PON, and similar structured tables.
 * Handles category/subcategory filtering, search, sorting, and pagination.
 */

function initializeFilterTable(config = {}) {
  // Configuration with sensible defaults
  const {
    filterPanelsSelector = '#taxonomy-filter-panels',
    categoryCheckboxSelector = '.parent-checkbox',
    subcategoryCheckboxSelector = '.child-checkbox',
    definitionSourceSelector = '#taxonomy-gwo-definition-source',
    itemTableBodySelector = '#taxonomy-gwo-table-body',
    itemTableSelector = '#taxonomy-gwo-table',
    sortHeaderSelector = 'th[data-column="title"]',
    paginationSelector = '#taxonomy-pagination',
    searchInputSelector = '#taxonomy-filter-search',
    clearButtonSelector = '#taxonomy-clear-button',
    itemsPerPage = 10,
    debounceMs = 500,
  } = config;

  // Query all required elements
  const categoryCheckboxes = Array.from(document.querySelectorAll(categoryCheckboxSelector));
  const subcategoryCheckboxes = Array.from(document.querySelectorAll(subcategoryCheckboxSelector));
  const definitionSourceEntries = Array.from(document.querySelectorAll(`${definitionSourceSelector} span`));
  const itemTableBody = document.querySelector(itemTableBodySelector);
  const itemTable = document.querySelector(itemTableSelector);
  const sortHeader = itemTable ? itemTable.querySelector(sortHeaderSelector) : null;
  const pagination = document.querySelector(paginationSelector);
  const paginationList = pagination ? pagination.querySelector('.usa-pagination__list') : null;
  const searchInput = document.querySelector(searchInputSelector);
  const clearButton = document.querySelector(clearButtonSelector);
  const filterPanels = document.querySelector(filterPanelsSelector);

  // Guard: exit early if critical elements are missing
  if (!categoryCheckboxes.length || !itemTableBody) {
    return;
  }

  // Internal state
  const state = {
    currentPage: 1,
    sortOrder: 'asc',
    debounceHandle: null,
    categoryMap: {},
    categorySubcategoryMap: {},
    itemDefinitionMap: {},
    itemPermalinkMap: {},
    itemsWithPrograms: new Set(),
  };

  // Collation for proper alphabetical sorting
  const alphaCollator = new Intl.Collator(undefined, {
    numeric: true,
    sensitivity: 'base',
    ignorePunctuation: true,
  });

  // Normalize text
  const normalizeText = (value) =>
    String(value || '').replace(/\s+/g, ' ').trim();

  // Get unique sorted array
  const uniqueSorted = (arr) =>
    Array.from(new Set(arr.map(normalizeText).filter(Boolean))).sort((a, b) =>
      alphaCollator.compare(a, b)
    );

  // Build maps from definition source
  definitionSourceEntries.forEach((entry) => {
    let itemTitle = entry.dataset.gwo || entry.dataset.pon || entry.dataset.item;
    const definition = entry.dataset.definition;
    const permalink = entry.dataset.permalink;

    if (!itemTitle) return;
    
    itemTitle = normalizeText(itemTitle); // Trim and normalize

    state.itemDefinitionMap[itemTitle] = definition || '';
    // Track items with program assignments based on non-empty permalink
    if (permalink && permalink.trim()) {
      state.itemPermalinkMap[itemTitle] = permalink;
      state.itemsWithPrograms.add(itemTitle);
    }
  });

  // Build category maps from program source
  const programSourceSelector = config.programSourceSelector || '#taxonomy-program-gwo-source';
  const programSourceEntries = Array.from(document.querySelectorAll(`${programSourceSelector} span`));

  programSourceEntries.forEach((entry) => {
    const category = entry.dataset.category;
    const subcategory = entry.dataset.subcategory || '';
    let itemTitle = entry.dataset.gwo || entry.dataset.pon || entry.dataset.item;

    if (!category || !itemTitle) return;
    
    itemTitle = normalizeText(itemTitle); // Trim and normalize

    if (!state.categoryMap[category]) {
      state.categoryMap[category] = new Set();
    }
    state.categoryMap[category].add(itemTitle);
    // Track items with program assignments based on program source
    state.itemsWithPrograms.add(itemTitle);

    const categorySubKey = category + '||' + subcategory;
    if (!state.categorySubcategoryMap[categorySubKey]) {
      state.categorySubcategoryMap[categorySubKey] = new Set();
    }
    state.categorySubcategoryMap[categorySubKey].add(itemTitle);
  });

  // Get all item titles
  const allItemTitles = uniqueSorted(
    definitionSourceEntries.map((entry) => entry.dataset.gwo || entry.dataset.pon || entry.dataset.item)
  );

  // Helper functions
  const getSelectedSubcategories = () =>
    subcategoryCheckboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.dataset.subcategoryTitle);

  const getSelectedCategories = () => {
    const selectedFromParents = categoryCheckboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.dataset.categoryTitle);
    const selectedFromChildren = subcategoryCheckboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.dataset.categoryTitle);

    return uniqueSorted([...selectedFromParents, ...selectedFromChildren]);
  };

  const getSelectedCategoryCount = () => {
    let count = 0;

    // Count all checked subcategories
    count += subcategoryCheckboxes.filter((checkbox) => checkbox.checked).length;

    // Count parent categories only if they have no children
    categoryCheckboxes.forEach((checkbox) => {
      if (checkbox.checked) {
        const childrenId = checkbox.dataset.childrenId;
        const childrenContainer = childrenId ? document.getElementById(childrenId) : null;
        if (!childrenContainer) {
          // Parent has no children, count it as a selectable item
          count++;
        }
      }
    });

    return count;
  };

  const updateFilterCountDisplay = () => {
    const count = getSelectedCategoryCount();
    const countDisplay = document.getElementById('taxonomy-filter-count');
    if (countDisplay) {
      countDisplay.textContent = count > 0 ? `(${count})` : '';
    }
  };

  const syncParentStateFromChildren = (parentCheckbox) => {
    const childrenId = parentCheckbox.dataset.childrenId;
    if (!childrenId) return;

    const childrenContainer = document.getElementById(childrenId);
    if (!childrenContainer) return;

    const children = Array.from(childrenContainer.querySelectorAll('input[data-filter-type="sub-category"]'));
    if (!children.length) {
      parentCheckbox.indeterminate = false;
      return;
    }

    const checkedCount = children.filter((c) => c.checked).length;
    parentCheckbox.checked = checkedCount === children.length;
    parentCheckbox.indeterminate = checkedCount > 0 && checkedCount < children.length;
  };

  const findParentCheckbox = (childCheckbox) => {
    const childrenContainer = childCheckbox.closest('.taxonomy-filter-children');
    if (!childrenContainer) return null;
    return categoryCheckboxes.find((cb) => cb.dataset.childrenId === childrenContainer.id);
  };

  const sortItems = (titles, order) =>
    [...titles].sort((a, b) =>
      order === 'asc' ? alphaCollator.compare(a, b) : alphaCollator.compare(b, a)
    );

  const updateSortIndicators = () => {
    if (!itemTable) return;
    itemTable.querySelectorAll('th[data-sortable]').forEach((header) => {
      header.removeAttribute('aria-sort');
    });
    if (sortHeader) {
      const direction = state.sortOrder === 'asc' ? 'ascending' : 'descending';
      sortHeader.setAttribute('aria-sort', direction);
    }
  };

  const renderRows = (itemTitles) => {
    itemTableBody.innerHTML = '';

    if (!itemTitles.length) {
      const row = document.createElement('tr');
      const cell = document.createElement('td');
      cell.colSpan = 2;
      cell.textContent = 'No items match the selected filters.';
      row.appendChild(cell);
      itemTableBody.appendChild(row);
      return;
    }

    itemTitles.forEach((itemTitle) => {
      const row = document.createElement('tr');
      const titleCell = document.createElement('td');
      const descCell = document.createElement('td');
      const permalink = state.itemPermalinkMap[itemTitle];
      const hasProgram = state.itemsWithPrograms.has(itemTitle);

      if (hasProgram && permalink) {
        const link = document.createElement('a');
        link.href = permalink;
        link.className = 'usa-link';
        link.textContent = itemTitle;
        titleCell.appendChild(link);
      } else {
        titleCell.textContent = itemTitle;
      }

      descCell.textContent = state.itemDefinitionMap[itemTitle] || '';
      row.appendChild(titleCell);
      row.appendChild(descCell);
      itemTableBody.appendChild(row);
    });
  };

  const updatePagination = (page, totalItems) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const start = (page - 1) * itemsPerPage + 1;
    const end = Math.min(page * itemsPerPage, totalItems);

    const resultsStart = document.getElementById('taxonomy-results-start');
    const resultsEnd = document.getElementById('taxonomy-results-end');
    const resultsTotal = document.getElementById('taxonomy-results-total');

    if (resultsStart) resultsStart.textContent = totalItems === 0 ? 0 : start;
    if (resultsEnd) resultsEnd.textContent = totalItems === 0 ? 0 : end;
    if (resultsTotal) resultsTotal.textContent = totalItems;

    if (!paginationList) return;

    const prevButton = paginationList.querySelector('.usa-pagination__arrow:first-child a');
    const nextButton = paginationList.querySelector('.usa-pagination__arrow:last-child a');
    const existingPages = paginationList.querySelectorAll('.usa-pagination__page-no, .usa-pagination__overflow');

    existingPages.forEach((el) => el.remove());

    if (totalItems === 0) {
      paginationList.style.display = 'none';
      return;
    }

    paginationList.style.display = '';

    let pages = [1];
    const rangeStart = Math.max(2, page - 1);
    const rangeEnd = Math.min(totalPages - 1, page + 1);

    if (rangeStart > 2) pages.push('...');
    for (let i = rangeStart; i <= rangeEnd; i++) pages.push(i);
    if (rangeEnd < totalPages - 1) pages.push('...');
    if (totalPages > 1) pages.push(totalPages);

    const nextButtonEl = paginationList.querySelector('.usa-pagination__arrow:last-child');

    pages.forEach((pageItem) => {
      const li = document.createElement('li');
      if (pageItem === '...') {
        li.className = 'usa-pagination__item usa-pagination__overflow';
        li.innerHTML = '<span>…</span>';
      } else {
        li.className = 'usa-pagination__item usa-pagination__page-no';
        const a = document.createElement('a');
        a.href = 'javascript:void(0);';
        a.className = `usa-pagination__button${pageItem === page ? ' usa-current' : ''}`;
        a.setAttribute('aria-label', `Page ${pageItem}`);
        if (pageItem === page) a.setAttribute('aria-current', 'page');
        a.textContent = pageItem;
        li.appendChild(a);
      }
      nextButtonEl ? paginationList.insertBefore(li, nextButtonEl) : paginationList.appendChild(li);
    });

    if (prevButton) {
      prevButton.classList.toggle('usa-pagination__link--disabled', page === 1);
      prevButton.setAttribute('aria-disabled', page === 1);
    }
    if (nextButton) {
      nextButton.classList.toggle('usa-pagination__link--disabled', page === totalPages);
      nextButton.setAttribute('aria-disabled', page === totalPages);
    }
  };

  const renderPagedRows = (itemTitles) => {
    const totalItems = itemTitles.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage));
    state.currentPage = Math.min(state.currentPage, totalPages);

    const start = (state.currentPage - 1) * itemsPerPage;
    const pageTitles = itemTitles.slice(start, start + itemsPerPage);

    renderRows(pageTitles);
    updatePagination(state.currentPage, totalItems);
  };

  const updateTable = (resetPage = false) => {
    if (resetPage) state.currentPage = 1;

    const selectedCategories = getSelectedCategories();

    if (selectedCategories.length === 0) {
      renderPagedRows(sortItems(allItemTitles, state.sortOrder));
      return;
    }

    const selectedSubcategories = getSelectedSubcategories();
    const filteredItems = new Set();

    selectedCategories.forEach((category) => {
      if (selectedSubcategories.length > 0) {
        selectedSubcategories.forEach((subcategory) => {
          const key = category + '||' + subcategory;
          (state.categorySubcategoryMap[key] || new Set()).forEach((item) => filteredItems.add(item));
        });
      } else {
        (state.categoryMap[category] || new Set()).forEach((item) => filteredItems.add(item));
      }
    });

    const orderedTitles = allItemTitles.filter((title) => filteredItems.has(title));
    renderPagedRows(sortItems(orderedTitles, state.sortOrder));
  };

  const clearFilters = () => {
    // Clear all checkboxes
    categoryCheckboxes.forEach((cb) => {
      cb.checked = false;
      cb.indeterminate = false;
    });
    subcategoryCheckboxes.forEach((cb) => {
      cb.checked = false;
    });

    // Clear search input and reset filter visibility
    if (searchInput) {
      searchInput.value = '';
      // Show all filter rows again
      const parentRows = filterPanels ? filterPanels.querySelectorAll('.taxonomy-filter-option-row') : [];
      parentRows.forEach((row) => {
        row.classList.remove('hide');
      });
      
      const childRows = filterPanels ? filterPanels.querySelectorAll('.usa-checkbox') : [];
      childRows.forEach((row) => {
        row.classList.remove('hide');
      });
      
      // Reset all toggles to collapsed state
      const toggles = filterPanels ? filterPanels.querySelectorAll('.taxonomy-children-toggle') : [];
      toggles.forEach((toggle) => {
        const contentId = toggle.getAttribute('data-content-id');
        if (!contentId) return;
        const container = document.getElementById(contentId);
        toggle.setAttribute('aria-expanded', 'false');
        if (container) container.hidden = true;
        const icon = toggle.querySelector('use');
        if (icon) {
          icon.setAttribute('xlink:href', '/assets/img/sprite.svg#navigate_next');
        }
      });
    }

    // Reset sort to default
    state.sortOrder = 'asc';
    updateSortIndicators();

    // Update count display and reset table
    updateFilterCountDisplay();
    updateTable(true);
  };

  // Event listeners
  categoryCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', () => {
      checkbox.indeterminate = false;
      const childrenId = checkbox.dataset.childrenId;
      if (childrenId) {
        const container = document.getElementById(childrenId);
        if (container) {
          container.querySelectorAll('input[data-filter-type="sub-category"]').forEach((c) => {
            c.checked = checkbox.checked;
          });
        }
      }
      updateFilterCountDisplay();
      updateTable(true);
    });
  });

  subcategoryCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', () => {
      const parent = findParentCheckbox(checkbox);
      if (parent) syncParentStateFromChildren(parent);
      updateFilterCountDisplay();
      updateTable(true);
    });
  });

  if (sortHeader) {
    sortHeader.style.pointerEvents = 'auto';
    sortHeader.addEventListener('click', (event) => {
      event.preventDefault();
      state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
      updateSortIndicators();
      updateTable(false);
    });
    updateSortIndicators();
  }

  if (paginationList) {
    paginationList.addEventListener('click', (event) => {
      const target = event.target.closest('a');
      if (!target) return;

      if (target.classList.contains('usa-pagination__button')) {
        const newPage = parseInt(target.textContent, 10);
        if (!isNaN(newPage) && newPage !== state.currentPage) {
          state.currentPage = newPage;
          updateTable(false);
        }
      } else if (target.classList.contains('usa-pagination__previous-page') && state.currentPage > 1) {
        state.currentPage--;
        updateTable(false);
      } else if (target.classList.contains('usa-pagination__next-page')) {
        state.currentPage++;
        updateTable(false);
      }
    });
  }

  if (clearButton) {
    clearButton.addEventListener('click', clearFilters);
  }

  // Search functionality
  if (searchInput) {
    const applySearch = () => {
      const query = normalizeText(searchInput.value).toLowerCase();
      const filterPanelContainer = filterPanels || document.querySelector(filterPanelsSelector);
      
      if (!filterPanelContainer) return;

      categoryCheckboxes.forEach((parentCheckbox) => {
        const parentRow = parentCheckbox.closest('.taxonomy-filter-option-row');
        const parentLabel = parentRow ? parentRow.querySelector('label') : null;
        const parentText = normalizeText(parentLabel ? parentLabel.textContent : '').toLowerCase();
        const parentMatches = query.length === 0 || parentText.includes(query);

        const childrenId = parentCheckbox.dataset.childrenId;
        const childrenContainer = childrenId ? document.getElementById(childrenId) : null;
        let hasMatchingChild = false;

        if (childrenContainer) {
          const childRows = Array.from(childrenContainer.querySelectorAll('.usa-checkbox'));
          childRows.forEach((childRow) => {
            const childLabel = childRow.querySelector('label');
            const childText = normalizeText(childLabel ? childLabel.textContent : '').toLowerCase();
            const childMatches = query.length === 0 || childText.includes(query) || parentText.includes(query);

            if (childMatches) {
              hasMatchingChild = true;
              childRow.classList.remove('hide');
            } else {
              childRow.classList.add('hide');
            }
          });
        }

        const showParent = parentMatches || hasMatchingChild;
        if (parentRow) {
          showParent ? parentRow.classList.remove('hide') : parentRow.classList.add('hide');
        }

        if (childrenContainer) {
          const toggle = parentRow ? parentRow.querySelector('.taxonomy-children-toggle') : null;
          if (toggle && query.length > 0) {
            const shouldExpand = showParent && hasMatchingChild;
            childrenContainer.hidden = !shouldExpand;
            toggle.setAttribute('aria-expanded', String(shouldExpand));
            const icon = toggle.querySelector('use');
            if (icon) {
              icon.setAttribute('xlink:href',
                shouldExpand
                  ? '/assets/img/sprite.svg#expand_more'
                  : '/assets/img/sprite.svg#navigate_next'
              );
            }
          }
        }
      });
    };

    searchInput.addEventListener('input', () => {
      window.clearTimeout(state.debounceHandle);
      state.debounceHandle = window.setTimeout(applySearch, debounceMs);
    });

    applySearch();
  }

  // Filter panel collapsing
  const filterButtons = filterPanels ? filterPanels.querySelectorAll('.usa-sidenav__button') : [];
  const collapseAllFilters = () => {
    filterButtons.forEach((btn) => {
      const contentId = btn.getAttribute('data-content-id');
      if (!contentId) return;
      const content = document.getElementById(contentId);
      btn.setAttribute('aria-expanded', 'false');
      if (content) content.hidden = true;
    });
  };

  filterButtons.forEach((btn) => {
    btn.addEventListener('click', function () {
      const contentId = this.getAttribute('data-content-id');
      if (!contentId) return;
      const content = document.getElementById(contentId);
      const expanded = this.getAttribute('aria-expanded') === 'true';
      this.setAttribute('aria-expanded', String(!expanded));
      if (content) content.hidden = expanded;
    });
  });

  document.addEventListener('click', (event) => {
    if (filterPanels && !event.target.closest(filterPanelsSelector)) {
      collapseAllFilters();
    }
  });

  // Category children toggle
  const categoryToggles = filterPanels ? filterPanels.querySelectorAll('.taxonomy-children-toggle') : [];
  categoryToggles.forEach((toggle) => {
    toggle.addEventListener('click', (event) => {
      event.preventDefault();
      const contentId = toggle.getAttribute('data-content-id');
      if (!contentId) return;
      const container = document.getElementById(contentId);
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      if (container) container.hidden = expanded;
      const icon = toggle.querySelector('use');
      if (icon) {
        icon.setAttribute('xlink:href',
          expanded
            ? '/assets/img/sprite.svg#navigate_next'
            : '/assets/img/sprite.svg#expand_more'
        );
      }
    });
  });

  // Prevent propagation on checkboxes
  const checkboxes = filterPanels ? filterPanels.querySelectorAll('input[type="checkbox"]') : [];
  checkboxes.forEach((cb) => {
    cb.addEventListener('click', (e) => e.stopPropagation());
  });

  // Initialize state
  categoryCheckboxes.forEach((cb) => syncParentStateFromChildren(cb));
  updateFilterCountDisplay();
  updateTable(true);

  // Re-apply after other components load
  window.addEventListener('load', function applyFinalSort() {
    updateTable(true);
    window.removeEventListener('load', applyFinalSort);
  });
}

// Auto-initialize on DOM ready if we're on a page with the required elements
document.addEventListener('DOMContentLoaded', function () {
  if (document.querySelector('#taxonomy-gwo-table-body')) {
    initializeFilterTable();
  }
});
