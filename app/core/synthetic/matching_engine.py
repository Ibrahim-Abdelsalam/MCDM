"""
Buyer-Supplier Matching Engine.

Implements an academically rigorous Capacity-Constrained Bipartite Matching Algorithm
(Two-Sided Utility Matching) to generate the relationship network.
"""

from __future__ import annotations

import datetime
import numpy as np
import pandas as pd

from . import config


class MatchingEngine:
    """Generates relationships using Capacity-Constrained Bi-directional Utility Matching."""

    def __init__(self, seed: int = config.DEFAULT_SEED):
        self.rng = np.random.default_rng(seed)

    def _generate_random_date(self, start_year: int, end_year: int) -> str:
        """Generates a random YYYY-MM-DD within the specified years."""
        start_date = datetime.date(start_year, 1, 1)
        end_date = datetime.date(end_year, 12, 31)
        days_between = (end_date - start_date).days
        random_days = self.rng.integers(0, days_between + 1)
        return (start_date + datetime.timedelta(days=int(random_days))).strftime("%Y-%m-%d")

    def _determine_quality_and_status(self, score: float) -> tuple[str, str]:
        """Maps final normalized synergy score to relationship quality and operational status."""
        if score >= 0.85:
            return "Excellent", "Active"
        elif score >= 0.65:
            return "Acceptable", "Active"
        elif score >= 0.50:
            return "Weak", "Under Review"
        elif score >= 0.40:
            return "Failed", "Terminated"
        else:
            return "Terminated", "Terminated"

    def _parse_payment_term(self, term: str) -> int:
        """Extracts days from 'Net 30', etc."""
        try:
            return int(term.split()[1])
        except (IndexError, ValueError):
            return 30

    def generate_relationships(
        self,
        buyers_df: pd.DataFrame,
        suppliers_df: pd.DataFrame,
        start_year: int = config.DEFAULT_YEAR_START,
        end_year: int = config.DEFAULT_YEAR_END
    ) -> pd.DataFrame:
        """
        Executes Capacity-Constrained Bipartite Matching based on Bi-Directional Utility.
        """
        # 1. Initialize Capacities based on scale
        buyer_capacities = {}
        for _, b in buyers_df.iterrows():
            min_sup, max_sup = config.AVG_RELATIONSHIPS_PER_BUYER.get(b["company_size"], (3, 10))
            buyer_capacities[b["entity_id"]] = self.rng.integers(min_sup, max_sup + 1)
            
        supplier_capacities = {}
        sup_cap_map = {"Small": (2, 8), "Medium": (5, 20), "Large": (15, 50), "Enterprise": (40, 100)}
        for _, s in suppliers_df.iterrows():
            min_b, max_b = sup_cap_map.get(s["company_size"], (5, 20))
            supplier_capacities[s["entity_id"]] = self.rng.integers(min_b, max_b + 1)

        # 2. Compute Global Edge Weights (Joint Synergy) for all valid pairs
        edges = []
        
        # Pre-group to avoid massive Cartesian products
        suppliers_by_industry = {ind: suppliers_df[suppliers_df["industry"] == ind] for ind in config.INDUSTRY_NAMES}
        
        for _, buyer in buyers_df.iterrows():
            buyer_id = buyer["entity_id"]
            buyer_ind = buyer["industry"]
            buyer_region = buyer["region"]
            buyer_size = buyer["company_size"]
            
            # Buyer Latents
            b_fin_health = buyer.get("financial_health", 0.0)
            b_strat_pos = buyer.get("strategic_positioning", 0.0)
            b_op_mat = buyer.get("operational_maturity", 0.0)
            
            # Filter compatible suppliers
            compatible_industries = config.INDUSTRY_COMPATIBILITY.get(buyer_ind, [buyer_ind])
            pool_dfs = [suppliers_by_industry[ind] for ind in compatible_industries if ind in suppliers_by_industry]
            if not pool_dfs:
                continue
            
            supplier_pool = pd.concat(pool_dfs)
            preferred_sizes = config.SIZE_COMPATIBILITY.get(buyer_size, [])
            
            for _, supplier in supplier_pool.iterrows():
                sup_id = supplier["entity_id"]
                
                # Supplier Latents
                s_op_cap = supplier.get("operational_capability", 0.0)
                s_comm_comp = supplier.get("commercial_competitiveness", 0.0)
                s_comp_post = supplier.get("compliance_posture", 0.0)
                
                # U_B: Utility of Supplier to Buyer
                u_b = (s_op_cap * 0.4) + (s_comm_comp * 0.4) + (s_comp_post * 0.2)
                if supplier["company_size"] in preferred_sizes:
                    u_b += 0.5 # Size match bonus
                    
                # U_S: Utility of Buyer to Supplier
                u_s = (b_fin_health * 0.4) + (b_strat_pos * 0.4) + (b_op_mat * 0.2)
                if supplier["region"] == buyer_region:
                    u_s += 0.5 # Geographical proximity bonus (lowers cost to serve)
                    
                # Joint Synergy (with unobserved stochastic noise)
                noise = self.rng.normal(0, 0.3)
                joint_synergy = u_b + u_s + noise
                
                edges.append({
                    "buyer_id": buyer_id,
                    "supplier_id": sup_id,
                    "synergy": joint_synergy,
                    "buyer_data": buyer,
                    "supplier_data": supplier
                })

        # 3. Greedy Capacity-Constrained Bipartite Matching
        # Sort all potential relationships globally by highest joint synergy
        edges.sort(key=lambda x: x["synergy"], reverse=True)
        
        relationships = []
        rel_counter = 1
        
        buyer_counts = {b: 0 for b in buyer_capacities.keys()}
        supplier_counts = {s: 0 for s in supplier_capacities.keys()}
        
        # Track raw synergies for scaling later
        accepted_synergies = []
        accepted_edges = []
        
        for edge in edges:
            b_id = edge["buyer_id"]
            s_id = edge["supplier_id"]
            
            # Check if both still have capacity
            if buyer_counts[b_id] < buyer_capacities[b_id] and supplier_counts[s_id] < supplier_capacities[s_id]:
                # Form the relationship
                buyer_counts[b_id] += 1
                supplier_counts[s_id] += 1
                accepted_edges.append(edge)
                accepted_synergies.append(edge["synergy"])

        # 4. Generate Operational Features from Formed Matches
        if not accepted_synergies:
            return pd.DataFrame()
            
        # Min-max scale synergies roughly to 0.1 - 0.95 for outcome mapping
        min_syn = min(accepted_synergies)
        max_syn = max(accepted_synergies)
        range_syn = max_syn - min_syn if max_syn > min_syn else 1
        
        for edge in accepted_edges:
            buyer = edge["buyer_data"]
            supplier = edge["supplier_data"]
            
            import datetime
            # Normalize score to determine categorical quality
            norm_score = 0.2 + 0.75 * ((edge["synergy"] - min_syn) / range_syn)
            quality, status = self.determine_quality_and_status(norm_score)
            
            # Start dates organically spread across 2018-2023
            min_s_year = max(start_year, int(buyer.get("creation_year", start_year)), int(supplier.get("creation_year", start_year)))
            
            # Deactivation handling (A1 Guard)
            b_deact = buyer.get("deactivation_year")
            s_deact = supplier.get("deactivation_year")
            b_deact_year = int(b_deact) if pd.notna(b_deact) and b_deact is not None else 2099
            s_deact_year = int(s_deact) if pd.notna(s_deact) and s_deact is not None else 2099
            
            max_s_year = min(end_year, b_deact_year, s_deact_year)
            
            if min_s_year > max_s_year:
                continue # Entities never overlapped in active timeframe
                
            # weighted randomly
            s_year = self.rng.integers(min_s_year, max_s_year + 1)
            
            if s_deact_year <= end_year or b_deact_year <= end_year:
                status = "Terminated"
                quality = "Terminated"
                # s_year is already guaranteed <= min(b_deact_year, s_deact_year)
            
            start_date_str = self._generate_random_date(s_year, s_year)
            start_dt = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            
            if status == "Terminated":
                # Ensure end date is strictly after start date (min 120 days)
                max_e_year = min(end_year, min(s_deact_year, b_deact_year))
                max_dt = datetime.datetime(max_e_year, 12, 31)
                max_days = (max_dt - start_dt).days
                
                # if already too close to horizon, push back start_dt
                if max_days < 120:
                    start_dt = max_dt - datetime.timedelta(days=120)
                    start_date_str = start_dt.strftime("%Y-%m-%d")
                    max_days = 120
                    
                dur = int(self.rng.integers(120, max(121, max_days + 1)))
                end_dt = start_dt + datetime.timedelta(days=dur)
                end_date = end_dt.strftime("%Y-%m-%d")
            else:
                end_date = ""
            
            contract_type = self.rng.choice(config.CONTRACT_TYPES)
            order_freq = self.rng.choice(config.ORDER_FREQUENCIES)
            
            base_val = {"Small": 50000, "Medium": 250000, "Large": 1000000, "Enterprise": 5000000}[buyer["company_size"]]
            contract_val = round(self.rng.normal(base_val, base_val * 0.2))
            
            agreed_lead = int(self.rng.choice([7, 14, 30, 45, 60, 90]))
            sup_op_cap = supplier.get("operational_capability", 0.0)
            actual_lead_offset = int(self.rng.normal(0, 5) - (sup_op_cap * 3))
            actual_lead = max(1, agreed_lead + actual_lead_offset)
            
            # Math tie actual lead time to delivery performance
            ratio = actual_lead / agreed_lead
            if ratio <= 1.0:
                delivery_perf = np.clip(7.0 + 5*(1 - ratio) + self.rng.normal(0, 0.5), 4.0, 10.0)
            else:
                delivery_perf = np.clip(7.0 - 12*(ratio - 1) + self.rng.normal(0, 0.5), 1.0, 6.5)
                if ratio > 1.3:
                    delivery_perf = np.clip(delivery_perf, 1.0, 4.5)
            delivery_perf = round(float(delivery_perf), 1)
            
            pay_term = self.rng.choice(config.PAYMENT_TERMS)
            agreed_days = self._parse_payment_term(pay_term)
            buyer_fin_health = buyer.get("financial_health", 0.0)
            actual_pay_days = max(1, int(self.rng.normal(agreed_days, 10) - (buyer_fin_health * 5)))
            
            dispute_count = max(0, int(self.rng.normal(5, 3) - (norm_score * 5)))
            if quality == "Excellent":
                dispute_count = min(dispute_count, int(self.rng.integers(0, 3)))
                
            order_changes = max(0, int(self.rng.normal(10, 5) - (buyer.get("operational_maturity", 0.0) * 3)))
            
            quality_perf = round(np.clip(self.rng.normal(6, 1.5) + sup_op_cap * 1.5, 1.0, 10.0), 1)
            collab_score = round(np.clip(norm_score * 10, 1.0, 10.0), 1)
            satisfaction = round(np.clip(norm_score * 10 + self.rng.normal(0, 1), 1.0, 10.0), 1)
            
            risk_lvl = "Low" if norm_score > 0.7 else ("Medium" if norm_score > 0.5 else "High")
            
            relationships.append({
                "relationship_id": f"REL-{rel_counter:06d}",
                "buyer_id": buyer["entity_id"],
                "supplier_id": supplier["entity_id"],
                "start_date": start_date_str,
                "end_date": end_date,
                "relationship_quality": quality,
                "relationship_status": status,
                "contract_type": contract_type,
                "annual_contract_value": contract_val,
                "order_frequency": order_freq,
                "agreed_lead_time": agreed_lead,
                "actual_lead_time": actual_lead,
                "delivery_performance": delivery_perf,
                "quality_performance": quality_perf,
                "payment_terms": pay_term,
                "actual_payment_days": actual_pay_days,
                "dispute_count": dispute_count,
                "order_change_frequency": order_changes,
                "collaboration_score": collab_score,
                "relationship_risk": risk_lvl,
                "relationship_satisfaction": satisfaction
            })
            rel_counter += 1
                
        return pd.DataFrame(relationships)

    # Alias for determine quality to allow self-calling
    determine_quality_and_status = _determine_quality_and_status
