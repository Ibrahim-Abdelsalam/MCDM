"""
Business Variables Engine.

Generates raw operational metrics (defect rates, lead times, capacities, payment delays)
that mathematically correspond to the normalized 1-10 rating scores.
"""
import numpy as np
import pandas as pd

class BusinessVarsEngine:
    def __init__(self, seed=42):
        self.rng = np.random.default_rng(seed)
        
        # Baselines mapping
        self.LEAD_TIMES = {'FMCG': 14, 'Automotive': 30, 'Industrial Manufacturing': 35, 
                           'Pharmaceutical': 40, 'Food & Beverage': 12, 'Consumer Goods': 21, 'Packaging': 18}
        self.CAPACITY_UNITS = {'FMCG': 90000, 'Automotive': 20000, 'Industrial Manufacturing': 12000, 
                               'Pharmaceutical': 60000, 'Food & Beverage': 150000, 'Consumer Goods': 70000, 'Packaging': 120000}
        self.PAY_TERMS = {'FMCG': 45, 'Automotive': 60, 'Industrial Manufacturing': 60,
                          'Pharmaceutical': 60, 'Food & Beverage': 30, 'Consumer Goods': 45, 'Packaging': 45}
        self.FREQ_MULTS = {'Small': 24, 'Medium': 52, 'Large': 104, 'Enterprise': 156}
        self.MID_REV = {'$1M-5M': 2.2, '$5M-10M': 7.0, '$10M-25M': 16.0, '$25M-50M': 35.0, 
                        '$50M-100M': 70.0, '$100M-500M': 220.0, '$500M-1B': 700.0, '$1B+': 1800.0}

    def _inv(self, val):
        return (val - 1) / 9.0

    def generate_supplier_vars(self, suppliers_df: pd.DataFrame, supplier_ratings: pd.DataFrame, slim: bool = False) -> pd.DataFrame:
        rows = []
        sup_dict = suppliers_df.set_index('entity_id').to_dict('index')
        
        # Pivot ratings to have one row per entity-year
        if supplier_ratings.empty:
            return pd.DataFrame()
            
        pivoted = supplier_ratings.pivot_table(index=['entity_id', 'year'], columns='criterion', values='raw_value').reset_index()
        
        for _, row in pivoted.iterrows():
            e = row['entity_id']
            y = int(row['year'])
            if e not in sup_dict:
                continue
            meta = sup_dict[e]
            ind = meta['industry']
            
            sq = self._inv(row.get('Quality Performance', 5.0))
            sd = self._inv(row.get('Delivery Performance', 5.0))
            sf = self._inv(row.get('Flexibility', 5.0))
            sfin = self._inv(row.get('Financial Stability', 5.0))
            stc = self._inv(row.get('Technical Capability / Process Capability', 5.0))
            scomp = self._inv(row.get('Compliance and Sustainability', 5.0))
            scost = row.get('Cost / Price Competitiveness', 5.0)
            
            defect = float(np.clip(0.002 + 0.07 * (1 - sq)**2 * np.exp(self.rng.normal(0, 0.1)), 0.0005, 0.12))
            fpy = float(np.clip(1 - defect * (2.2 + self.rng.normal(0, 0.1)), 0.6, 0.999))
            otd = float(np.clip(0.55 + 0.44 * sd**0.9 + self.rng.normal(0, 0.01), 0.5, 0.995))
            lt = self.LEAD_TIMES.get(ind, 30) * (1 + 0.5 * (1 - sd)) * np.exp(self.rng.normal(0, 0.04))
            ltv = lt * (0.05 + 0.35 * (1 - sd)) * np.exp(self.rng.normal(0, 0.1))
            
            cap0 = meta['employee_count'] * self.CAPACITY_UNITS.get(ind, 50000) / 100
            cap = cap0 * (1.03 ** max(0, y - 2018)) * np.exp(self.rng.normal(0, 0.03))
            
            util = float(np.clip(0.92 - 0.42 * sf + self.rng.normal(0, 0.02), 0.4, 0.98))
            moq = max(1, cap / 12 * (0.003 + 0.03 * (1 - sf)))
            
            cost_idx = 100 * (0.8 + 0.4 * (scost - 1) / 9) * np.exp(self.rng.normal(0, 0.01))
            cv = float(np.clip(0.01 + 0.06 * (1 - sfin) + 0.02 * (1 - stc), 0.005, 0.15))
            
            frs = float(np.clip(5 + 85 * (1 - sfin) + self.rng.normal(0, 2), 0, 100))
            flex = float(np.clip(100 * (0.2 + 0.75 * sf) + self.rng.normal(0, 1.5), 0, 100))
            
            erp = int(np.clip(round(row.get('Systems Integration', 5.0) / 2.5 + self.rng.normal(0, 0.15)), 0, 4))
            cpk = float(np.clip(0.6 + 1.2 * stc + self.rng.normal(0, 0.04), 0.5, 2.2))
            
            esg = float(np.clip(100 * (0.1 + 0.88 * scomp) + self.rng.normal(0, 1.5), 0, 100))
            hse = float(np.clip(100 * (0.55 * scomp + 0.25 * sq + 0.2 * stc) + 12, 0, 100))
            
            q_raw = row.get('Quality Performance', 5.0)
            cert = 'Not certified / lapsed' if q_raw < 4 else 'In progress' if q_raw < 5.5 else 'ISO 9001' if q_raw < 7.5 else 'ISO 9001 + industry standard'
            
            record = {
                "entity_id": e, "year": y,
                "defect_rate": round(defect, 4),
                "on_time_delivery_rate": round(otd, 4), "average_lead_time_days": round(lt, 1),
                "lead_time_variability_days": round(ltv, 1), "production_capacity_units": int(cap),
                "MOQ_units": int(moq), "capacity_utilization": round(util, 3),
                "unit_cost_index": round(cost_idx, 1), "cost_variability": round(cv, 4),
                "financial_risk_score": round(frs, 1), "flexibility_score": round(flex, 1),
                "ERP_integration_level": erp, "technical_capability_cpk": round(cpk, 2),
                "ESG_compliance": round(esg, 1), "HSE_compliance": round(hse, 1),
                "quality_certification_status": cert
            }
            if not slim:
                record["first_pass_yield"] = round(fpy, 4)
            rows.append(record)
            
        df = pd.DataFrame(rows)
        if not slim and "first_pass_yield" in df.columns:
            # Reorder so first_pass_yield is after defect_rate for backwards compatibility
            cols = list(df.columns)
            cols.remove("first_pass_yield")
            defect_idx = cols.index("defect_rate")
            cols.insert(defect_idx + 1, "first_pass_yield")
            df = df[cols]
        return df

    @staticmethod
    def to_slim_supplier_vars(df: pd.DataFrame) -> pd.DataFrame:
        """Filter out redundant first_pass_yield and years_experience."""
        drop_cols = ["first_pass_yield", "years_experience"]
        return df.drop(columns=[c for c in drop_cols if c in df.columns]).copy()


    def generate_buyer_vars(self, buyers_df: pd.DataFrame, buyer_ratings: pd.DataFrame, slim: bool = False) -> pd.DataFrame:
        rows = []
        buy_dict = buyers_df.set_index('entity_id').to_dict('index')
        
        if buyer_ratings.empty:
            return pd.DataFrame()
            
        pivoted = buyer_ratings.pivot_table(index=['entity_id', 'year'], columns='criterion', values='raw_value').reset_index()
        
        for _, row in pivoted.iterrows():
            e = row['entity_id']
            y = int(row['year'])
            if e not in buy_dict:
                continue
            meta = buy_dict[e]
            ind = meta['industry']
            size = meta['company_size']
            
            sdem = self._inv(row.get('Demand Stability & Predictability', 5.0))
            sfin = self._inv(row.get('Financial Stability & Creditworthiness', 5.0))
            spay = self._inv(row.get('Payment Performance', 5.0))
            svol = self._inv(row.get('Order Volume & Growth Potential', 5.0))
            sresp = self._inv(row.get('Responsiveness & Collaboration', 5.0))
            
            growth = -0.04 + 0.22 * svol + (-0.03 if y == 2020 else 0.0) + self.rng.normal(0, 0.02)
            rev = self.MID_REV.get(meta['annual_revenue_band'], 50.0)
            if y > 2018:
                rev = rev * (1 + growth)
                
            fa = float(np.clip(0.50 + 0.45 * sdem + self.rng.normal(0, 0.015), 0.4, 0.98))
            delay = float(max(0, 2 + 35 * (1 - spay)**1.6 + self.rng.normal(0, 1.0)))
            ovr = float(np.clip(0.005 + 0.22 * (1 - spay)**1.5, 0, 0.5))
            
            comp = row.get('Compliance & Regulatory Standards', 5.0)
            
            record = {
                "entity_id": e, "year": y,
                "annual_order_volume_usd": int(rev * 1e6 * (0.03 + 0.10 * svol)),
                "order_frequency_per_year": int(self.FREQ_MULTS.get(size, 52) * (0.6 + 0.8 * sdem)),
                "forecast_accuracy": round(fa, 3),
                "average_payment_days": round(self.PAY_TERMS.get(ind, 45) + delay, 1),
                "payment_delay_days": round(delay, 1),
                "credit_limit_usd": int(rev * 1e6 * (0.02 + 0.06 * sfin)),
                "overdue_ratio": round(ovr, 4), "revenue_usd_m": round(rev, 2),
                "revenue_growth": round(growth, 4),
                "financial_risk_score": round(float(np.clip(5 + 85 * (1 - sfin), 0, 100)), 1),
                "communication_response_time_hours": round(float(2 + 70 * (1 - sresp)**1.6), 1),
                "ERP_integration_level": int(np.clip(round(row.get('Technical Sophistication (Systems)', 5.0) / 2.5), 0, 4)),
                "compliance_status": 'Non-compliant' if comp < 4 else 'Minor findings' if comp < 6.5 else 'Compliant',
                "reputation_score": round(float(np.clip(100 * self._inv(row.get('Market Reputation & Brand Impact', 5.0)), 0, 100)), 1)
            }
            if not slim:
                record["forecast_error"] = round(1 - fa, 3)
            rows.append(record)
            
        df = pd.DataFrame(rows)
        if not slim and "forecast_error" in df.columns:
            # Reorder so forecast_error is immediately after forecast_accuracy
            cols = list(df.columns)
            cols.remove("forecast_error")
            acc_idx = cols.index("forecast_accuracy")
            cols.insert(acc_idx + 1, "forecast_error")
            df = df[cols]
        return df

    @staticmethod
    def to_slim_buyer_vars(df: pd.DataFrame) -> pd.DataFrame:
        """Filter out redundant forecast_error."""
        return df.drop(columns=[c for c in ["forecast_error"] if c in df.columns]).copy()


