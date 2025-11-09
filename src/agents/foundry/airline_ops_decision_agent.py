"""
Airline Operations Decision Agent Module.

This module implements the Decision Ops Agent that runs on Azure AI Foundry,
providing analytical tools for airline operations decision-making and executive insights.
"""

import asyncio
from datetime import datetime, timezone
from typing import Annotated, Dict, Any, List, Optional
from random import randint, uniform
import json

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity import AzureCliCredential
from pydantic import Field
import streamlit as st

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.settings import AZURE_AI_PROJECT_ENDPOINT, FOUNDRY_AGENT_ID
from utils.ml_logging import get_logger

logger = get_logger("agent_registry.foundry.airline_ops_decision_agent")


# ===============================
# AIRLINE OPERATIONS DECISION TOOLS
# ===============================


def calculate_kpi(
    metric_type: Annotated[
        str,
        Field(
            description="KPI type: on_time_performance, baggage_mttr, missed_connections, gate_utilization"
        ),
    ],
    data_points: Annotated[
        str, Field(description="JSON string with operational data points")
    ],
    time_period: Annotated[
        str, Field(description="Time period for calculation: hourly, daily, weekly")
    ] = "daily",
) -> str:
    """
    Calculate key performance indicators for airline operations.

    This function computes critical operational metrics including on-time performance,
    baggage mean time to resolution, missed connections, and gate utilization.

    :param metric_type: The type of KPI to calculate
    :param data_points: JSON formatted operational data
    :param time_period: Time period for the calculation
    :return: Calculated KPI with detailed breakdown
    """
    try:
        logger.info(f"Calculating {metric_type} KPI for {time_period} period")

        # Simulate realistic airline KPI calculations
        if metric_type == "on_time_performance":
            # On-time performance calculation
            base_performance = uniform(0.75, 0.95)
            result = {
                "metric": "On-Time Performance",
                "value": f"{base_performance:.1%}",
                "benchmark": "85%",
                "status": "above_benchmark"
                if base_performance > 0.85
                else "below_benchmark",
                "factors": [
                    "Weather delays: 15%",
                    "Crew delays: 8%",
                    "Aircraft maintenance: 12%",
                    "ATC delays: 10%",
                ],
                "period": time_period,
            }
        elif metric_type == "baggage_mttr":
            # Baggage Mean Time To Resolution
            mttr_minutes = randint(45, 180)
            result = {
                "metric": "Baggage MTTR",
                "value": f"{mttr_minutes} minutes",
                "benchmark": "90 minutes",
                "status": "above_benchmark"
                if mttr_minutes > 90
                else "within_benchmark",
                "trend": "improving" if mttr_minutes < 120 else "declining",
                "period": time_period,
            }
        elif metric_type == "missed_connections":
            # Missed connections rate
            missed_rate = uniform(0.02, 0.08)
            result = {
                "metric": "Missed Connections Rate",
                "value": f"{missed_rate:.2%}",
                "benchmark": "5%",
                "total_passengers_affected": randint(150, 500),
                "compensation_cost": f"${randint(50000, 200000):,}",
                "period": time_period,
            }
        elif metric_type == "gate_utilization":
            # Gate utilization efficiency
            utilization = uniform(0.60, 0.90)
            result = {
                "metric": "Gate Utilization",
                "value": f"{utilization:.1%}",
                "benchmark": "75%",
                "peak_hours_utilization": f"{uniform(0.85, 0.98):.1%}",
                "off_peak_utilization": f"{uniform(0.40, 0.65):.1%}",
                "period": time_period,
            }
        else:
            result = {"error": f"Unknown metric type: {metric_type}"}

        logger.info(f"Successfully calculated KPI: {result['metric']}")
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error calculating KPI: {str(e)}")
        return json.dumps({"error": f"KPI calculation failed: {str(e)}"})


def detect_anomalies(
    operational_data: Annotated[
        str, Field(description="JSON string with current operational metrics")
    ],
    threshold_type: Annotated[
        str,
        Field(
            description="Anomaly detection type: sla_breach, performance_deviation, capacity_overrun"
        ),
    ] = "sla_breach",
) -> str:
    """
    Detect operational anomalies and SLA breaches in airline operations.

    This function identifies deviations from normal operational patterns and
    service level agreement violations requiring immediate attention.

    :param operational_data: Current operational metrics in JSON format
    :param threshold_type: Type of anomaly detection to perform
    :return: Detected anomalies with severity and recommended actions
    """
    try:
        logger.info(f"Detecting {threshold_type} anomalies in operational data")

        # Simulate realistic anomaly detection
        anomalies_detected = []

        if threshold_type == "sla_breach":
            # SLA breach detection
            if randint(1, 10) > 7:  # 30% chance of SLA breach
                anomalies_detected.append(
                    {
                        "type": "SLA Breach",
                        "severity": "High",
                        "description": "Baggage delivery time exceeded 90-minute SLA",
                        "affected_flights": randint(5, 15),
                        "impact": "Customer satisfaction risk",
                        "action_required": "Deploy additional baggage handlers",
                    }
                )

        elif threshold_type == "performance_deviation":
            # Performance deviation detection
            if randint(1, 10) > 6:  # 40% chance of performance issue
                anomalies_detected.append(
                    {
                        "type": "Performance Deviation",
                        "severity": "Medium",
                        "description": "On-time performance dropped 15% below baseline",
                        "root_cause": "Weather delays cascading through network",
                        "affected_routes": ["ORD-LAX", "JFK-MIA", "ATL-DFW"],
                        "action_required": "Implement delay recovery procedures",
                    }
                )

        elif threshold_type == "capacity_overrun":
            # Capacity overrun detection
            if randint(1, 10) > 8:  # 20% chance of capacity issue
                anomalies_detected.append(
                    {
                        "type": "Capacity Overrun",
                        "severity": "Critical",
                        "description": "Terminal capacity at 98% - potential bottleneck",
                        "location": "Terminal B, Gates 15-25",
                        "risk": "Flight delays and passenger congestion",
                        "action_required": "Activate contingency gate plan",
                    }
                )

        if not anomalies_detected:
            anomalies_detected.append(
                {
                    "status": "Normal Operations",
                    "message": "No significant anomalies detected",
                    "last_check": datetime.now(timezone.utc).isoformat(),
                }
            )

        result = {
            "anomaly_detection": threshold_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "anomalies": anomalies_detected,
            "total_count": len([a for a in anomalies_detected if "severity" in a]),
        }

        logger.info(
            f"Anomaly detection complete: {len(anomalies_detected)} items found"
        )
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        return json.dumps({"error": f"Anomaly detection failed: {str(e)}"})


def forecast_impact(
    disruption_type: Annotated[
        str,
        Field(
            description="Type of disruption: weather_delay, gate_closure, crew_shortage, equipment_failure"
        ),
    ],
    scope: Annotated[
        str,
        Field(
            description="Scope of impact: single_flight, hub_operations, network_wide"
        ),
    ],
    duration_hours: Annotated[
        int, Field(description="Expected duration of disruption in hours")
    ] = 2,
) -> str:
    """
    Forecast downstream impact of operational disruptions.

    This function predicts the cascading effects of operational disruptions
    on flights, passengers, and overall network performance.

    :param disruption_type: The type of operational disruption
    :param scope: The operational scope affected
    :param duration_hours: Expected duration of the disruption
    :return: Impact forecast with mitigation recommendations
    """
    try:
        logger.info(
            f"Forecasting impact of {disruption_type} over {duration_hours} hours"
        )

        # Calculate impact based on disruption type and scope
        impact_multiplier = {
            "single_flight": 1.0,
            "hub_operations": 3.5,
            "network_wide": 8.0,
        }

        base_impact = duration_hours * impact_multiplier.get(scope, 1.0)

        if disruption_type == "weather_delay":
            affected_flights = int(base_impact * randint(8, 15))
            passenger_impact = affected_flights * randint(120, 180)
            cost_estimate = affected_flights * randint(15000, 35000)

        elif disruption_type == "gate_closure":
            affected_flights = int(base_impact * randint(3, 8))
            passenger_impact = affected_flights * randint(150, 200)
            cost_estimate = affected_flights * randint(8000, 20000)

        elif disruption_type == "crew_shortage":
            affected_flights = int(base_impact * randint(2, 6))
            passenger_impact = affected_flights * randint(100, 160)
            cost_estimate = affected_flights * randint(25000, 45000)

        else:  # equipment_failure
            affected_flights = int(base_impact * randint(1, 4))
            passenger_impact = affected_flights * randint(140, 190)
            cost_estimate = affected_flights * randint(30000, 60000)

        # Generate mitigation strategies
        mitigation_strategies = {
            "weather_delay": [
                "Pre-position aircraft at alternate airports",
                "Implement flexible crew scheduling",
                "Activate passenger rebooking protocols",
            ],
            "gate_closure": [
                "Redirect to available gates in adjacent terminals",
                "Negotiate temporary gate usage agreements",
                "Implement remote boarding procedures",
            ],
            "crew_shortage": [
                "Deploy reserve crew from nearby bases",
                "Negotiate crew overtime arrangements",
                "Consider aircraft swaps to optimize crew utilization",
            ],
            "equipment_failure": [
                "Deploy backup equipment immediately",
                "Coordinate with maintenance for rapid repair",
                "Consider equipment substitution from other locations",
            ],
        }

        forecast = {
            "disruption_analysis": {
                "type": disruption_type,
                "scope": scope,
                "duration_hours": duration_hours,
                "severity": "High"
                if affected_flights > 20
                else "Medium"
                if affected_flights > 10
                else "Low",
            },
            "impact_forecast": {
                "affected_flights": affected_flights,
                "passenger_impact": passenger_impact,
                "estimated_cost": f"${cost_estimate:,}",
                "recovery_time": f"{duration_hours + randint(1, 4)} hours",
                "network_delay_propagation": f"{randint(15, 45)}%",
            },
            "mitigation_strategies": mitigation_strategies.get(disruption_type, []),
            "priority_actions": [
                "Activate incident command center",
                "Notify affected passengers immediately",
                "Coordinate with ground operations",
            ],
            "forecast_confidence": "85%",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Impact forecast complete: {affected_flights} flights affected")
        return json.dumps(forecast, indent=2)

    except Exception as e:
        logger.error(f"Error forecasting impact: {str(e)}")
        return json.dumps({"error": f"Impact forecast failed: {str(e)}"})


def simulate_scenario(
    scenario_type: Annotated[
        str,
        Field(
            description="Scenario to simulate: gate_closure, runway_closure, weather_event, crew_disruption"
        ),
    ],
    parameters: Annotated[
        str, Field(description="JSON string with scenario parameters")
    ],
    simulation_duration: Annotated[
        int, Field(description="Simulation duration in hours")
    ] = 4,
) -> str:
    """
    Run what-if simulations for operational scenarios.

    This function simulates various operational scenarios to predict outcomes
    and test different response strategies before implementation.

    :param scenario_type: The type of scenario to simulate
    :param parameters: Scenario-specific parameters in JSON format
    :param simulation_duration: Duration of the simulation in hours
    :return: Simulation results with multiple outcome scenarios
    """
    try:
        logger.info(
            f"Running {scenario_type} simulation for {simulation_duration} hours"
        )

        # Generate simulation scenarios
        scenarios = {
            "best_case": {
                "probability": "25%",
                "flight_delays": randint(5, 15),
                "passenger_satisfaction": uniform(0.75, 0.90),
                "cost_impact": randint(50000, 150000),
                "recovery_time": f"{simulation_duration - 1} hours",
            },
            "most_likely": {
                "probability": "50%",
                "flight_delays": randint(15, 35),
                "passenger_satisfaction": uniform(0.60, 0.80),
                "cost_impact": randint(150000, 350000),
                "recovery_time": f"{simulation_duration + 1} hours",
            },
            "worst_case": {
                "probability": "25%",
                "flight_delays": randint(35, 60),
                "passenger_satisfaction": uniform(0.40, 0.65),
                "cost_impact": randint(350000, 750000),
                "recovery_time": f"{simulation_duration + 3} hours",
            },
        }

        # Add scenario-specific impacts
        scenario_specific = {
            "gate_closure": {
                "key_metrics": ["gate_utilization", "passenger_flow", "ground_time"],
                "critical_factors": [
                    "alternative_gate_availability",
                    "passenger_walking_distance",
                    "baggage_handling_capacity",
                ],
            },
            "runway_closure": {
                "key_metrics": [
                    "flight_frequency",
                    "airspace_capacity",
                    "fuel_consumption",
                ],
                "critical_factors": [
                    "alternate_runway_capacity",
                    "air_traffic_rerouting",
                    "ground_holding_procedures",
                ],
            },
            "weather_event": {
                "key_metrics": ["visibility", "wind_conditions", "precipitation"],
                "critical_factors": [
                    "forecast_accuracy",
                    "equipment_capabilities",
                    "crew_duty_limits",
                ],
            },
            "crew_disruption": {
                "key_metrics": [
                    "crew_availability",
                    "duty_time_compliance",
                    "reserve_activation",
                ],
                "critical_factors": [
                    "reserve_crew_location",
                    "duty_time_remaining",
                    "training_currency",
                ],
            },
        }

        simulation_result = {
            "simulation_metadata": {
                "scenario_type": scenario_type,
                "duration_hours": simulation_duration,
                "run_timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence_level": "High",
            },
            "scenario_outcomes": scenarios,
            "scenario_specifics": scenario_specific.get(scenario_type, {}),
            "recommendations": [
                f"Monitor {scenario_type} conditions closely",
                "Prepare contingency resources in advance",
                "Establish clear communication protocols",
                "Review and activate relevant response procedures",
            ],
            "key_decision_points": [
                "Resource allocation timing",
                "Passenger communication strategy",
                "Recovery procedure activation",
                "Escalation threshold triggers",
            ],
        }

        logger.info(f"Simulation complete for scenario: {scenario_type}")
        return json.dumps(simulation_result, indent=2)

    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        return json.dumps({"error": f"Scenario simulation failed: {str(e)}"})


def generate_exec_brief(
    situation_data: Annotated[
        str, Field(description="JSON string with current situation data")
    ],
    brief_type: Annotated[
        str,
        Field(
            description="Type of brief: operational_summary, risk_assessment, decision_support"
        ),
    ] = "operational_summary",
    audience_level: Annotated[
        str, Field(description="Target audience: executive, operations, ground_crew")
    ] = "executive",
) -> str:
    """
    Generate executive-level briefings with charts and recommendations.

    This function produces concise, actionable executive summaries with supporting
    metrics and visual elements for rapid decision-making.

    :param situation_data: Current operational situation in JSON format
    :param brief_type: Type of executive briefing to generate
    :param audience_level: Target audience level for the briefing
    :return: Executive briefing with key insights and recommendations
    """
    try:
        logger.info(f"Generating {brief_type} briefing for {audience_level} audience")

        current_time = datetime.now(timezone.utc)

        # Generate executive briefing content
        if brief_type == "operational_summary":
            brief = {
                "executive_summary": {
                    "title": "Airline Operations Status Brief",
                    "timestamp": current_time.isoformat(),
                    "overall_status": "Normal Operations"
                    if randint(1, 10) > 3
                    else "Disrupted Operations",
                    "key_metrics": {
                        "on_time_performance": f"{uniform(0.75, 0.95):.1%}",
                        "active_flights": randint(450, 650),
                        "passenger_satisfaction": f"{uniform(0.70, 0.90):.1%}",
                        "cost_performance": "Within budget"
                        if randint(1, 10) > 4
                        else "Above budget",
                    },
                },
                "critical_alerts": [
                    "Weather watch: Thunderstorms forecasted for Hub operations 14:00-18:00",
                    "Gate utilization: Terminal B approaching capacity limits",
                ],
                "performance_trends": {
                    "past_24h": "Stable operations with minor delays",
                    "forecast_next_6h": "Potential weather impact on Eastern routes",
                    "weekly_comparison": "Performance 5% above last week",
                },
            }

        elif brief_type == "risk_assessment":
            brief = {
                "risk_assessment": {
                    "title": "Operational Risk Analysis",
                    "assessment_time": current_time.isoformat(),
                    "overall_risk_level": "Medium" if randint(1, 10) > 6 else "Low",
                    "risk_factors": [
                        {
                            "factor": "Weather conditions",
                            "severity": "High",
                            "probability": "70%",
                        },
                        {
                            "factor": "Crew availability",
                            "severity": "Low",
                            "probability": "15%",
                        },
                        {
                            "factor": "Equipment status",
                            "severity": "Medium",
                            "probability": "25%",
                        },
                    ],
                    "financial_exposure": f"${randint(500000, 2000000):,}",
                    "passenger_impact": f"{randint(2000, 8000)} passengers potentially affected",
                },
                "mitigation_status": {
                    "active_measures": [
                        "Weather monitoring enhanced",
                        "Standby crew activated",
                    ],
                    "recommended_actions": [
                        "Pre-position recovery aircraft",
                        "Activate passenger communications",
                    ],
                },
            }

        else:  # decision_support
            brief = {
                "decision_support": {
                    "title": "Strategic Decision Briefing",
                    "decision_timeline": "Immediate action required"
                    if randint(1, 10) > 7
                    else "Strategic planning",
                    "options_analysis": [
                        {
                            "option": "Continue normal operations",
                            "pros": ["Minimal cost impact", "No passenger disruption"],
                            "cons": ["Risk of cascade delays"],
                            "cost_estimate": "$50,000",
                        },
                        {
                            "option": "Implement proactive delays",
                            "pros": [
                                "Better resource allocation",
                                "Reduced cascade risk",
                            ],
                            "cons": ["Immediate passenger impact", "Revenue loss"],
                            "cost_estimate": "$200,000",
                        },
                    ],
                    "recommendation": "Implement proactive delays with enhanced passenger communication",
                }
            }

        # Add audience-specific content
        if audience_level == "executive":
            brief["executive_actions"] = [
                "Review and approve recommended mitigation measures",
                "Authorize additional resource deployment if needed",
                "Approve passenger communication strategy",
            ]
        elif audience_level == "operations":
            brief["operational_tasks"] = [
                "Execute approved contingency procedures",
                "Monitor key performance indicators",
                "Coordinate with ground teams and crew",
            ]

        brief["chart_data"] = {
            "performance_chart": "On-time performance trend (24h)",
            "cost_chart": "Operational cost breakdown",
            "passenger_chart": "Passenger satisfaction metrics",
        }

        brief["next_brief_scheduled"] = (
            current_time.replace(minute=0, second=0) + datetime.timedelta(hours=2)
        ).isoformat()

        logger.info(f"Executive briefing generated successfully: {brief_type}")
        return json.dumps(brief, indent=2)

    except Exception as e:
        logger.error(f"Error generating executive brief: {str(e)}")
        return json.dumps({"error": f"Executive brief generation failed: {str(e)}"})


# ===============================
# AIRLINE DECISION AGENT SETUP
# ===============================


def setup_airline_decision_agent() -> None:
    """
    Initialize the Airline Operations Decision Agent.

    This function creates a ChatAgent configured with airline operations decision tools
    for analytical insights, forecasting, and executive reporting.

    :return: None
    :raises: Exception if agent creation fails
    """
    if "airline_decision_agent" not in st.session_state:
        try:
            # Create the decision agent with all airline operations tools
            st.session_state.airline_decision_agent = ChatAgent(
                chat_client=AzureAIAgentClient(
                    endpoint=AZURE_AI_PROJECT_ENDPOINT,
                    credential=AzureCliCredential(),
                    agent_id=FOUNDRY_AGENT_ID,
                ),
                name="AirlineDecisionOpsAgent",
                description="Airline Operations Decision Agent specialized in analytical insights, forecasting, and executive reporting for rapid decision-making.",
                instructions="""You are an expert Airline Operations Decision Agent with advanced analytical capabilities.

Your primary role is to:
1. Calculate and interpret key performance indicators (KPIs) for airline operations
2. Detect operational anomalies and SLA breaches requiring immediate attention  
3. Forecast the downstream impact of operational disruptions
4. Run what-if simulations to test response strategies
5. Generate executive-level briefings with actionable insights

CORE TOOLS AVAILABLE:
- calculate_kpi: Compute on-time %, baggage MTTR, missed connections, gate utilization
- detect_anomalies: Identify operational deviations and SLA violations  
- forecast_impact: Predict cascading effects of disruptions
- simulate_scenario: Run what-if analyses for decision support
- generate_exec_brief: Create executive summaries with charts and recommendations

OUTPUT STYLE:
- Provide data-driven insights with specific metrics
- Include confidence levels and risk assessments
- Offer clear, actionable recommendations
- Support findings with quantitative analysis
- Format responses for executive-level consumption

When analyzing operational data, always consider:
- Impact on passenger experience and satisfaction
- Financial implications and cost optimization
- Resource allocation efficiency
- Regulatory compliance and safety requirements
- Network-wide effects of local disruptions""",
                tools=[
                    calculate_kpi,
                    detect_anomalies,
                    forecast_impact,
                    simulate_scenario,
                    generate_exec_brief,
                ],
            )
            logger.info("Airline Operations Decision Agent created successfully")

        except Exception as e:
            logger.error(f"Failed to create Airline Decision Agent: {str(e)}")
            st.session_state.airline_decision_agent = None
            raise


def initialize_airline_decision_services() -> None:
    """
    Initialize all Airline Decision Agent services.

    This function orchestrates the initialization of the decision agent
    and should be called during application startup.

    :return: None
    :raises: Exception if initialization fails
    """
    try:
        logger.info("Initializing Airline Decision Agent services")
        setup_airline_decision_agent()
        logger.info(
            "Airline Decision Agent services initialization completed successfully"
        )
    except Exception as e:
        logger.error(f"Airline Decision Agent services initialization failed: {str(e)}")
        raise


def get_airline_decision_agent() -> Optional[ChatAgent]:
    """
    Get the initialized Airline Decision Agent from session state.

    This function retrieves the decision agent instance from session state
    if it has been properly initialized and is available for use.

    :return: The Airline Decision Agent instance, or None if not available
    :raises: None - function handles missing agent gracefully
    """
    try:
        return st.session_state.get("airline_decision_agent")
    except Exception as e:
        logger.error(f"Error retrieving Airline Decision Agent: {str(e)}")
        return None


def is_airline_decision_agent_available() -> bool:
    """
    Check if the Airline Decision Agent is properly initialized and available.

    This function verifies the availability of the decision agent in session state
    to ensure it can be used for processing analytical requests.

    :return: True if the agent is available, False otherwise
    :raises: None - function handles errors gracefully
    """
    try:
        return st.session_state.get("airline_decision_agent") is not None
    except Exception as e:
        logger.error(f"Error checking Airline Decision Agent availability: {str(e)}")
        return False
