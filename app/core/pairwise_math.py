"""Mathematical implementation of AHP and Fuzzy AHP weight calculation."""

from __future__ import annotations

import numpy as np


# Random Index (RI) values for n = 1 to 10
RI_TABLE = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49
}

def calculate_ahp_weights(matrix: np.ndarray, criteria_names: list[str]) -> tuple[dict[str, float], float]:
    """
    Calculate AHP weights from a pairwise comparison matrix and perform consistency check.
    
    Args:
        matrix: NxN numpy array of pairwise comparisons.
        criteria_names: List of N criteria names.
        
    Returns:
        tuple containing:
            - dict of {criterion_name: weight}
            - float value for Consistency Ratio (CR)
    """
    n = matrix.shape[0]
    
    # 1. Normalize the matrix
    col_sums = np.sum(matrix, axis=0)
    normalized_matrix = matrix / col_sums
    
    # 2. Calculate criteria weights (average of each row)
    weights_array = np.mean(normalized_matrix, axis=1)
    
    # 3. Calculate Consistency Ratio (CR)
    if n <= 2:
        cr = 0.0
    else:
        # Multiply original matrix by criteria weights
        weighted_sum = np.dot(matrix, weights_array)
        
        # Ratio of weighted sum / criteria weight
        ratios = weighted_sum / weights_array
        
        # Lambda max is the average of the ratios
        lambda_max = np.mean(ratios)
        
        # Consistency Index
        ci = (lambda_max - n) / (n - 1)
        
        # Random Index
        ri = RI_TABLE.get(n, 1.49) # Fallback to 1.49 for n >= 10
        
        cr = ci / ri if ri > 0 else 0.0
        
    weights_dict = {name: float(weights_array[i]) for i, name in enumerate(criteria_names)}
    
    return weights_dict, float(cr)


def _fuzzify_value(val: float) -> tuple[float, float, float]:
    """Convert crisp 1-9 scale value to triangular fuzzy number (l, m, u)."""
    # Exact 1 -> (1, 1, 1)
    if abs(val - 1.0) < 1e-5:
        return (1.0, 1.0, 1.0)
    
    # Handle > 1 values (e.g. 2, 3, 4, 5, 6, 7, 8, 9)
    if val > 1.0:
        return (val - 1.0, val, val + 1.0)
    
    # Handle reciprocal values (< 1)
    # If val = 1/x, then x = 1/val. The fuzzy number for x is (x-1, x, x+1).
    # The reciprocal fuzzy number is (1/(x+1), 1/x, 1/(x-1)).
    x = 1.0 / val
    return (1.0 / (x + 1.0), 1.0 / x, 1.0 / (x - 1.0))


def calculate_fahp_weights(matrix: np.ndarray, criteria_names: list[str]) -> dict[str, float]:
    """
    Calculate Fuzzy AHP weights using Buckley's Geometric Mean method.
    
    Args:
        matrix: NxN numpy array of crisp pairwise comparisons.
        criteria_names: List of N criteria names.
        
    Returns:
        dict of {criterion_name: normalized_crisp_weight}
    """
    n = matrix.shape[0]
    
    # Fuzzify the matrix
    # fuzzy_matrix[i, j] will be a tuple (l, m, u)
    fuzzy_matrix = np.zeros((n, n, 3))
    for i in range(n):
        for j in range(n):
            fuzzy_matrix[i, j] = _fuzzify_value(matrix[i, j])
            
    # Calculate geometric mean for each row
    geom_means = np.zeros((n, 3))
    for i in range(n):
        l_prod = np.prod(fuzzy_matrix[i, :, 0])
        m_prod = np.prod(fuzzy_matrix[i, :, 1])
        u_prod = np.prod(fuzzy_matrix[i, :, 2])
        
        geom_means[i, 0] = l_prod ** (1.0 / n)
        geom_means[i, 1] = m_prod ** (1.0 / n)
        geom_means[i, 2] = u_prod ** (1.0 / n)
        
    # Sum of geometric means
    sum_geom_means = np.sum(geom_means, axis=0) # [sum_l, sum_m, sum_u]
    
    # Reciprocal of the sum
    # Formula: (1/sum_u, 1/sum_m, 1/sum_l)
    sum_inv = np.array([
        1.0 / sum_geom_means[2],
        1.0 / sum_geom_means[1],
        1.0 / sum_geom_means[0]
    ])
    
    # Calculate fuzzy weights w_i = r_i * sum_inv
    # Lower = l * (1/sum_u), Middle = m * (1/sum_m), Upper = u * (1/sum_l)
    fuzzy_weights = np.zeros((n, 3))
    for i in range(n):
        fuzzy_weights[i, 0] = geom_means[i, 0] * sum_inv[0]
        fuzzy_weights[i, 1] = geom_means[i, 1] * sum_inv[1]
        fuzzy_weights[i, 2] = geom_means[i, 2] * sum_inv[2]
        
    # Defuzzification (Center of Area method)
    crisp_weights = np.zeros(n)
    for i in range(n):
        crisp_weights[i] = (fuzzy_weights[i, 0] + fuzzy_weights[i, 1] + fuzzy_weights[i, 2]) / 3.0
        
    # Normalize to ensure they sum to 1
    total_weight = np.sum(crisp_weights)
    normalized_weights = crisp_weights / total_weight
    
    weights_dict = {name: float(normalized_weights[i]) for i, name in enumerate(criteria_names)}
    return weights_dict
