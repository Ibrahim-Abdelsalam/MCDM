"""
Company Factory.

Generates scalable, realistic entity profiles (buyers and suppliers) with correlated
attributes and latent capability factors.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


class CompanyFactory:
    """Generates scalable company profiles with latent factors."""

    def __init__(self, seed: int = config.DEFAULT_SEED):
        """Initialize the factory with a random seed."""
        self.rng = np.random.default_rng(seed)

    def _generate_name(self, entity_type: str) -> str:
        """Generate a realistic company name."""
        prefix = self.rng.choice(config.COMPANY_NAME_PREFIXES)
        suffix = self.rng.choice(config.COMPANY_NAME_SUFFIXES[entity_type])
        legal_form = self.rng.choice(config.COMPANY_NAME_LEGAL_FORMS)
        return f"{prefix} {suffix} {legal_form}"

    def _get_revenue_and_employees(self, size: str) -> tuple[str, int]:
        """Get correlated revenue band and employee count for a given size."""
        size_data = config.COMPANY_SIZES[size]
        revenue_band = self.rng.choice(size_data["revenue_bands"])
        min_emp, max_emp = size_data["employee_range"]
        employee_count = int(self.rng.integers(min_emp, max_emp + 1))
        return revenue_band, employee_count

    def _get_region_and_country(self, industry: str) -> tuple[str, str]:
        """Get a region and country, weighted by industry primary regions."""
        industry_data = config.INDUSTRY_PROFILES[industry]
        # 80% chance to be in a primary region for the industry, 20% any region
        if self.rng.random() < 0.8:
            region = self.rng.choice(industry_data["primary_regions"])
        else:
            region = self.rng.choice(list(config.REGIONS.keys()))
        
        country = self.rng.choice(config.REGIONS[region])
        return region, country

    def _generate_latent_factors(self, entity_type: str, size: str) -> dict[str, float]:
        """
        Generate latent factors (e.g. operational_capability) based on size.
        Uses a standard normal base + size adjustments.
        """
        if entity_type == "supplier":
            factor_names = list(config.SUPPLIER_LATENT_FACTORS.keys())
        else:
            factor_names = list(config.BUYER_LATENT_FACTORS.keys())
            
        factors = {}
        for fname in factor_names:
            base_val = self.rng.normal(0, 1.0)
            adjustment = config.SIZE_FACTOR_ADJUSTMENTS[size].get(fname, 0.0)
            factors[fname] = base_val + adjustment
            
        return factors

    def generate(
        self, 
        entity_type: str, 
        n: int, 
        start_year: int = config.DEFAULT_YEAR_START
    ) -> pd.DataFrame:
        """
        Generate N companies of the given entity_type.
        
        Returns a DataFrame containing standard attributes plus latent factors.
        """
        if entity_type not in ["supplier", "buyer"]:
            raise ValueError("entity_type must be 'supplier' or 'buyer'")
            
        prefix = "SUP" if entity_type == "supplier" else "BUY"
        records = []
        
        for i in range(1, n + 1):
            entity_id = f"{prefix}-{i:05d}"
            
            # Select industry uniformly (could be weighted in future)
            industry = self.rng.choice(config.INDUSTRY_NAMES)
            industry_data = config.INDUSTRY_PROFILES[industry]
            
            # Select size based on industry distribution
            sizes = list(industry_data["typical_company_sizes"].keys())
            size_probs = list(industry_data["typical_company_sizes"].values())
            # Ensure probabilities sum to 1
            size_probs = [p / sum(size_probs) for p in size_probs]
            size = self.rng.choice(sizes, p=size_probs)
            
            rev_band, emp_count = self._get_revenue_and_employees(size)
            region, country = self._get_region_and_country(industry)
            
            # Age and creation year
            # Older companies tend to be larger
            base_age = {"Small": 5, "Medium": 15, "Large": 30, "Enterprise": 50}[size]
            years_in_op = int(max(1, self.rng.normal(base_age, base_age * 0.4)))
            creation_year = start_year - years_in_op
            
            # Segments
            strat_seg = self.rng.choice(config.STRATEGIC_SEGMENTS)
            risk_seg = self.rng.choice(config.RISK_SEGMENTS)
            
            # Latent factors
            latent_factors = self._generate_latent_factors(entity_type, size)
            
            is_active = self.rng.random() > 0.05
            active_status = "Active" if is_active else "Inactive"
            deactivation_year = None if is_active else int(self.rng.integers(start_year + 1, 2024))

            record = {
                "entity_id": entity_id,
                "company_name": self._generate_name(entity_type),
                "entity_type": entity_type,
                "industry": industry,
                "country": country,
                "region": region,
                "company_size": size,
                "annual_revenue_band": rev_band,
                "employee_count": emp_count,
                "years_in_operation": years_in_op,
                "strategic_segment": strat_seg,
                "risk_segment": risk_seg,
                "creation_year": creation_year,
                "active_status": active_status,
                "deactivation_year": deactivation_year,
            }
            record.update(latent_factors)
            records.append(record)
            
        df = pd.DataFrame(records)
        df['deactivation_year'] = df['deactivation_year'].astype('Int64')
        return df
