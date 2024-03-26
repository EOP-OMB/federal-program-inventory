SELECT
	ts.fiscal_year,
	ts.cfda_number,
	SUM(ts.federal_action_obligation)
FROM rpt.transaction_search as ts
LEFT JOIN rpt.award_search as aw
ON ts.award_id = aw.award_id
WHERE aw.type IN ('07', '08', '02', '03', '04', '05', '06', '10', '09', '11')
AND ts.fiscal_year > 2020
GROUP BY
	ts.fiscal_year,
	ts.cfda_number;