"""
Define measures as dicts (to me turned into Measure instances in the study def *and*
for use when drawing graphs)
"""
measures_dict = [
    dict(id="all_rate", numerator="long_covid", denominator="population", group_by=[]),
    dict(
        id="sex_rate",
        numerator="long_covid",
        denominator="population",
        group_by=["sex"],
    ),
    dict(
        id="age_group_rate",
        numerator="long_covid",
        denominator="population",
        group_by=["age_group"],
    ),
    dict(
        id="covid_record_rate",
        numerator="long_covid",
        denominator="population",
        group_by=["previous_covid"],
    ),
]
