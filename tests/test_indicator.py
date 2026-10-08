import json

from app.agents.indicator import IndicatorConceptualizationAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "indicators": [
                    {
                        "code": "IND-001",
                        "topic": "Economy",
                        "section_responsibility": "Statistical Portfolio Planning",
                        "theme": "Population",
                        "sub_theme": "Demographics",
                        "name": "Population Growth Rate",
                        "name_ar": "معدل النمو السكاني",
                        "description": "This indicator measures the average annual rate of change in population.",
                        "importance_objective_use": "This indicator tracks population dynamics.",
                        "international_standards": "UN Principles and Recommendations",
                        "available_breakdown": "Broken down by region",
                        "special_aggregates": "N/A",
                        "keywords": ["population", "growth"],
                        "statistical_population": "The statistical population covers all usual residents.",
                        "geographic_coverage": "Geographical coverage includes the Emirate of Abu Dhabi.",
                        "reference_period": "The reference period for the data is the previous year.",
                        "release_date": "Within 12 months after the reference period",
                        "measurement_unit": "Percent",
                        "scale": "N/A",
                        "base_period": "N/A",
                        "publication_frequency": "Annual",
                        "available_periodicity": "Annual",
                        "methodology": "See methodologies page on SCAD's official website",
                        "data_sources": ["census"],
                        "calculation_method": "growth rate formula",
                        "seasonally_adjusted": "N/A",
                        "chain_linking": "N/A",
                        "time_series": "Dataset starts from 2010",
                        "data_coherence_comparability": "Consistent over time.",
                        "data_validation_editing": "Data is validated.",
                        "data_accuracy_errors": "Sampling and non-sampling errors.",
                        "last_methodology_revision": "To be determined",
                        "language": "English, Arabic",
                        "indicator_ownership": "Statistics Centre - Abu Dhabi (SCAD)",
                        "focal_contact": "Statistics Centre - Abu Dhabi (SCAD)",
                        "mode_of_dissemination": "SCAD website",
                        "data_accessibility": "PDF, MS Excel",
                        "target_audience": "General Public",
                        "last_update": "To be determined",
                        "additional_comments": "<<SCAD to complete>>",
                        "indicators_with_common_sub_theme": ["Population size"],
                        "copyright_usage": "© SCAD, for public usage",
                    }
                ],
                "traceability": [
                    {"indicator": "Population Growth Rate", "methodology_section": "1", "source_ref": "UN principles"}
                ],
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_indicator_agent():
    agent = IndicatorConceptualizationAgent(FakeLLM())
    result = agent.run(
        {
            "objective": "Population",
            "standardized_methodology": {"methodology": {"sections": []}},
            "scad_input_analysis": {},
            "clarification": {},
        }
    )
    assert result.status == "succeeded"
    assert len(result.outputs["indicators"]) == 1
    indicator = result.outputs["indicators"][0]
    assert indicator["name"] == "Population Growth Rate"
    assert indicator["code"] == "IND-001"
    assert indicator["measurement_unit"] == "Percent"
    assert indicator["statistical_population"].startswith("The statistical population covers")
    assert indicator["data_sources"] == ["census"]
    assert len(result.outputs["traceability"]) == 1


def test_indicator_agent_coerces_string_list_fields():
    class StringListLLM(FakeLLM):
        def chat(self, system_prompt, user_prompt, max_tokens=None):
            data = json.loads(super().chat(system_prompt, user_prompt, max_tokens))
            data["indicators"][0]["keywords"] = "population"
            data["indicators"][0]["data_sources"] = "census"
            return json.dumps(data)

    agent = IndicatorConceptualizationAgent(StringListLLM())
    result = agent.run({"objective": "Population"})
    assert result.status == "succeeded"
    indicator = result.outputs["indicators"][0]
    assert indicator["keywords"] == ["population"]
    assert indicator["data_sources"] == ["census"]
