"""
Rating and Temporal Engine.

Generates multi-year, seasonal criterion scores based on latent factors,
incorporating persistence, drift, shocks, and seasonal patterns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


class RatingEngine:
    """Generates time-series criterion ratings and qualification gates."""

    def __init__(self, seed: int = config.DEFAULT_SEED):
        self.rng = np.random.default_rng(seed)

    def _get_base_score(self, entity: dict, criterion: str, entity_type: str) -> float:
        """Calculate the latent-driven base score for a criterion."""
        industry = entity["industry"]
        industry_profile = config.INDUSTRY_PROFILES[industry]
        
        # Determine latent factor contribution
        contribution = 0.0
        factors_map = config.SUPPLIER_LATENT_FACTORS if entity_type == "supplier" else config.BUYER_LATENT_FACTORS
        
        for factor_name, loadings in factors_map.items():
            if criterion in loadings:
                loading = loadings[criterion]
                factor_val = entity.get(factor_name, 0.0)
                contribution += loading * factor_val
                
        # Get industry tendencies
        tendencies = industry_profile[f"{entity_type}_weight_tendencies"].get(criterion, (5.5, 1.0))
        base_mean, _ = tendencies
        
        # Apply industry score adjustments
        adjustment = industry_profile.get("score_adjustments", {}).get(criterion, 0.0)
        
        # Check criterion type (invert contribution for cost so high capability = low cost)
        criteria_list = config.SUPPLIER_CRITERIA if entity_type == "supplier" else config.BUYER_CRITERIA
        crit_def = next(c for c in criteria_list if c["name"] == criterion)
        
        if crit_def["type"] == "cost":
            contribution = -contribution
            
        raw_base = base_mean + (contribution * 1.5) + adjustment
        return np.clip(raw_base, config.SCORE_MIN, config.SCORE_MAX)

    def generate(
        self,
        entities_df: pd.DataFrame,
        entity_type: str,
        start_year: int = config.DEFAULT_YEAR_START,
        end_year: int = config.DEFAULT_YEAR_END,
        granularity: str = config.GRANULARITY,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate criterion ratings for entities over time.
        
        Returns:
            ratings_df: DataFrame of ratings (granular).
            events_df: DataFrame of shock events.
        """
        criteria_list = config.SUPPLIER_CRITERIA if entity_type == "supplier" else config.BUYER_CRITERIA
        criteria_names = [c["name"] for c in criteria_list]
        gates = config.SUPPLIER_GATES if entity_type == "supplier" else config.BUYER_GATES
        gate_map = {g["linked_criterion"]: g for g in gates}
        
        ratings = []
        events = []
        
        periods = [1]
        if granularity == "quarterly":
            periods = [1, 2, 3, 4]
        elif granularity == "monthly":
            periods = list(range(1, 13))
            
        for _, entity in entities_df.iterrows():
            entity_id = entity["entity_id"]
            industry = entity["industry"]
            industry_profile = config.INDUSTRY_PROFILES[industry]
            peak_quarters = industry_profile.get("seasonal_peak_quarters", [])
            seasonal_pattern_key = config.get_seasonal_pattern(peak_quarters)
            seasonal_mults = config.SEASONAL_PATTERNS[seasonal_pattern_key]
            seasonal_amp = industry_profile.get("seasonal_amplitude", 0.0)
            
            # Base values per criterion
            base_scores = {c: self._get_base_score(entity, c, entity_type) for c in criteria_names}
            current_scores = base_scores.copy()
            
            ent_start = max(start_year, int(entity["creation_year"]))
            deact = entity.get("deactivation_year")
            ent_end = end_year if pd.isna(deact) or deact is None else int(deact)
            
            for year in range(ent_start, ent_end + 1):
                scenario_id = f"SCN-{year}-{industry[:3].upper()}"
                
                # Advance annual state
                for crit in criteria_names:
                    params = config.TEMPORAL_PARAMS[crit]
                    persistence = params["persistence"]
                    drift_std = params["drift_std"] * industry_profile.get("risk_volatility", 1.0)
                    
                    # Mean-reverting random walk
                    val_prev = current_scores[crit]
                    base_val = base_scores[crit]
                    
                    val_next = (val_prev * persistence) + (base_val * (1 - persistence))
                    val_next += self.rng.normal(0, drift_std)
                    
                    # Shocks
                    if self.rng.random() < params["shock_prob"]:
                        event_type = self.rng.choice(config.SHOCK_EVENT_TYPES)
                        s_min, s_max = params["shock_mag"]
                        shock_val = self.rng.uniform(s_min, s_max)
                        
                        # Apply polarity based on event type
                        if event_type in config.HARM_EVENTS:
                            shock_val = -abs(shock_val)
                        elif event_type in config.BENE_EVENTS:
                            shock_val = abs(shock_val)
                        # NEUT_EVENTS can stay as-is (random sign)
                        
                        # Invert impact for cost criteria (where lower is better, so a positive shock means score goes UP/better, which means raw goes DOWN)
                        crit_type = next((c["type"] for c in criteria_list if c["name"] == crit), "benefit")
                        raw_shift = -shock_val if crit_type == "cost" else shock_val
                        
                        val_next += raw_shift
                        events.append({
                            "entity_id": entity_id,
                            "year": year,
                            "event_type": event_type,
                            "impact_magnitude": round(shock_val, 2), # positive=beneficial, negative=harmful
                            "raw_value_shift": round(raw_shift, 2),
                            "affected_criterion": crit
                        })
                        
                    current_scores[crit] = np.clip(val_next, config.SCORE_MIN, config.SCORE_MAX)
                
                # Generate periods
                for p in periods:
                    for crit in criteria_names:
                        val = current_scores[crit]
                        
                        # Apply seasonality if applicable
                        if crit in config.SEASONAL_CRITERIA[entity_type] and granularity == "quarterly":
                            val += (seasonal_mults[p-1] * seasonal_amp * 10)
                            
                        # Small period noise
                        val += self.rng.normal(0, 0.15)
                        val = np.clip(val, config.SCORE_MIN, config.SCORE_MAX)
                        
                        # Evaluate Gate
                        gate_status = "N/A"
                        gate_status = None
                        if crit in gate_map:
                            # gate threshold is strictly < 4.0
                            if val < config.GATE_PASS_THRESHOLD:
                                gate_status = "fail"
                            else:
                                gate_status = "pass"
                                
                        # Calculate normalized rating properly (invert for cost)
                        crit_type = next(c["type"] for c in criteria_list if c["name"] == crit)
                        if crit_type == "cost":
                            norm_rating = (config.SCORE_MAX - val) / (config.SCORE_MAX - config.SCORE_MIN)
                        else:
                            norm_rating = (val - config.SCORE_MIN) / (config.SCORE_MAX - config.SCORE_MIN)
                                
                        data_source = self.rng.choice(config.DATA_SOURCES)
                        
                        ratings.append({
                            "entity_id": entity_id,
                            "year": year,
                            "period": p,
                            "criterion": crit,
                            "raw_value": round(val, 2),
                            "normalized_rating": round(norm_rating, 4),
                            "rating_scale": f"{config.SCORE_MIN}-{config.SCORE_MAX}",
                            "gate_status": gate_status,
                            "data_source": data_source,
                            "scenario_id": scenario_id,
                        })
                        
                # Re-evaluate qualification based on ANY gated criterion falling below 4.0
                is_qualified = True
                year_records = ratings[-len(periods) * len(criteria_names):]
                for r in year_records:
                    if r["gate_status"] == "fail":
                        is_qualified = False
                        break
                
                # Assign the qualification status back to all records for this year
                for r in year_records:
                    r["is_qualified"] = is_qualified
                        
        ratings_df = pd.DataFrame(ratings)
        events_df = pd.DataFrame(events)
        return ratings_df, events_df

    def aggregate_yearly(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates sub-annual ratings into yearly ratings for MCDM steps."""
        if ratings_df.empty:
            return ratings_df
            
        group_cols = ["entity_id", "year", "criterion", "rating_scale", "scenario_id"]
        
        # Mode function for categorical columns
        def get_mode(x):
            modes = x.dropna().mode()
            return modes.iloc[0] if not modes.empty else None
            
        yearly_df = ratings_df.groupby(group_cols, dropna=False).agg(
            raw_value=("raw_value", "mean"),
            normalized_rating=("normalized_rating", "mean"),
            gate_status=("gate_status", get_mode),
            data_source=("data_source", get_mode),
            is_qualified=("is_qualified", get_mode),
        ).reset_index()
        
        yearly_df["raw_value"] = yearly_df["raw_value"].round(2)
        yearly_df["normalized_rating"] = yearly_df["normalized_rating"].round(4)
        
        return yearly_df
