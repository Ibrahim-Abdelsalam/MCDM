"""Fuzzy AHP (Fuzzy Analytic Hierarchy Process) MCDM solver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .criteria import CriteriaConfig
from .normalizer import Normalizer


@dataclass(frozen=True)
class TriangularFuzzyNumber:
    """Represent a triangular fuzzy number as lower, modal, and upper values."""

    lower: float
    modal: float
    upper: float

    def __post_init__(self) -> None:
        if self.lower <= 0 or self.modal <= 0 or self.upper <= 0:
            raise ValueError("Triangular fuzzy numbers must contain positive values.")
        if not self.lower <= self.modal <= self.upper:
            raise ValueError("Triangular fuzzy numbers must satisfy lower <= modal <= upper.")

    def reciprocal(self) -> "TriangularFuzzyNumber":
        """Return the fuzzy reciprocal (1/u, 1/m, 1/l)."""
        return TriangularFuzzyNumber(1.0 / self.upper, 1.0 / self.modal, 1.0 / self.lower)

    def defuzzify(self) -> float:
        """Defuzzify using the center-of-area method."""
        return (self.lower + self.modal + self.upper) / 3.0


class FuzzyAHPSolver:
    """Solve using Fuzzy AHP with Buckley's geometric mean weight estimation."""

    LINGUISTIC_SCALE: tuple[TriangularFuzzyNumber, ...] = (
        TriangularFuzzyNumber(1.0, 1.0, 1.0),
        TriangularFuzzyNumber(1.0, 2.0, 3.0),
        TriangularFuzzyNumber(2.0, 3.0, 4.0),
        TriangularFuzzyNumber(3.0, 4.0, 5.0),
        TriangularFuzzyNumber(4.0, 5.0, 6.0),
        TriangularFuzzyNumber(5.0, 6.0, 7.0),
    )

    def solve(
        self,
        weight_vector: dict[str, float],
        scores_df: pd.DataFrame,
        fuzzy_pairwise_matrix: list[list[tuple[float, float, float]]] | None = None,
    ) -> pd.DataFrame:
        """
        Solve using Fuzzy AHP.

        Args:
            weight_vector: dict mapping criterion names to weights. Used directly to
                infer a fuzzy pairwise matrix when an explicit matrix is not supplied.
            scores_df: DataFrame with ID column and criterion score columns.
            fuzzy_pairwise_matrix: optional square matrix of triangular fuzzy
                numbers in ``(lower, modal, upper)`` form.

        Returns:
            DataFrame with columns: [ID, FUZZY_AHP_Score, FUZZY_AHP_Rank]
        """
        criteria_names = [name for name in weight_vector if name in scores_df.columns]
        if not criteria_names:
            raise ValueError("No weighted criteria were found in the score dataframe.")

        if fuzzy_pairwise_matrix is None:
            matrix = self._build_matrix_from_weights(weight_vector, criteria_names)
        else:
            matrix = self._coerce_matrix(fuzzy_pairwise_matrix, len(criteria_names))

        fuzzy_weights = self._calculate_fuzzy_weights(matrix)
        normalized_weights = self._defuzzify_and_normalize(fuzzy_weights, criteria_names)

        normalized_scores_df = Normalizer.minmax_normalize(scores_df, CriteriaConfig)
        score_matrix = normalized_scores_df[criteria_names].to_numpy(dtype=float)
        weight_array = np.array([normalized_weights[name] for name in criteria_names], dtype=float)
        fuzzy_ahp_scores = score_matrix @ weight_array

        result = scores_df[["ID"]].copy()
        result["FUZZY_AHP_Score"] = fuzzy_ahp_scores
        result["FUZZY_AHP_Rank"] = result["FUZZY_AHP_Score"].rank(method="min", ascending=False).astype(int)
        return result.sort_values("FUZZY_AHP_Rank")

    def derive_weights(
        self,
        weight_vector: dict[str, float],
        criteria_names: Iterable[str] | None = None,
    ) -> dict[str, float]:
        """Return defuzzified, normalized Fuzzy AHP weights for inspection or reuse."""
        ordered_criteria = list(criteria_names or weight_vector.keys())
        if not ordered_criteria:
            raise ValueError("At least one criterion is required to derive Fuzzy AHP weights.")
        matrix = self._build_matrix_from_weights(weight_vector, ordered_criteria)
        fuzzy_weights = self._calculate_fuzzy_weights(matrix)
        return self._defuzzify_and_normalize(fuzzy_weights, ordered_criteria)

    def _build_matrix_from_weights(
        self,
        weight_vector: dict[str, float],
        criteria_names: list[str],
    ) -> list[list[TriangularFuzzyNumber]]:
        """Infer a reciprocal fuzzy comparison matrix from an existing weight vector."""
        crisp_weights = np.array([float(weight_vector[name]) for name in criteria_names], dtype=float)
        if np.any(crisp_weights < 0):
            raise ValueError("Fuzzy AHP weights must be non-negative.")
        if float(np.sum(crisp_weights)) <= 1e-10:
            raise ValueError("Fuzzy AHP weights cannot all be zero.")

        positive_floor = min((value for value in crisp_weights if value > 0), default=1e-9) * 1e-3
        crisp_weights = np.where(crisp_weights > 0, crisp_weights, positive_floor)

        matrix: list[list[TriangularFuzzyNumber]] = []
        for i, left_weight in enumerate(crisp_weights):
            row: list[TriangularFuzzyNumber] = []
            for j, right_weight in enumerate(crisp_weights):
                if i == j:
                    row.append(self.LINGUISTIC_SCALE[0])
                    continue

                ratio = float(left_weight / right_weight)
                if ratio >= 1.0:
                    row.append(self._ratio_to_tfn(ratio))
                else:
                    row.append(self._ratio_to_tfn(1.0 / ratio).reciprocal())
            matrix.append(row)
        return matrix

    def _ratio_to_tfn(self, ratio: float) -> TriangularFuzzyNumber:
        """Map a crisp importance ratio to the nearest supported linguistic TFN."""
        capped_ratio = min(max(ratio, 1.0), 7.0)
        return min(self.LINGUISTIC_SCALE, key=lambda tfn: abs(tfn.modal - capped_ratio))

    def _coerce_matrix(
        self,
        raw_matrix: list[list[tuple[float, float, float]]],
        expected_size: int,
    ) -> list[list[TriangularFuzzyNumber]]:
        """Validate and convert a raw tuple matrix to triangular fuzzy numbers."""
        if len(raw_matrix) != expected_size:
            raise ValueError("Fuzzy pairwise matrix size must match the number of active criteria.")

        matrix: list[list[TriangularFuzzyNumber]] = []
        for row in raw_matrix:
            if len(row) != expected_size:
                raise ValueError("Fuzzy pairwise matrix must be square.")
            matrix.append([TriangularFuzzyNumber(*values) for values in row])
        return matrix

    def _calculate_fuzzy_weights(
        self,
        matrix: list[list[TriangularFuzzyNumber]],
    ) -> list[TriangularFuzzyNumber]:
        """Calculate fuzzy weights using Buckley's geometric mean method."""
        size = len(matrix)
        geometric_means: list[TriangularFuzzyNumber] = []

        for row in matrix:
            lower_product = np.prod([value.lower for value in row])
            modal_product = np.prod([value.modal for value in row])
            upper_product = np.prod([value.upper for value in row])
            exponent = 1.0 / size
            geometric_means.append(
                TriangularFuzzyNumber(
                    float(lower_product ** exponent),
                    float(modal_product ** exponent),
                    float(upper_product ** exponent),
                )
            )

        sum_lower = sum(value.lower for value in geometric_means)
        sum_modal = sum(value.modal for value in geometric_means)
        sum_upper = sum(value.upper for value in geometric_means)

        return [
            TriangularFuzzyNumber(
                value.lower / sum_upper,
                value.modal / sum_modal,
                value.upper / sum_lower,
            )
            for value in geometric_means
        ]

    def _defuzzify_and_normalize(
        self,
        fuzzy_weights: list[TriangularFuzzyNumber],
        criteria_names: Iterable[str],
    ) -> dict[str, float]:
        """Convert fuzzy weights to crisp normalized criterion weights."""
        crisp_weights = np.array([value.defuzzify() for value in fuzzy_weights], dtype=float)
        weight_total = float(np.sum(crisp_weights))
        if weight_total <= 1e-10:
            raise ValueError("Defuzzified Fuzzy AHP weights cannot be normalized.")
        normalized = crisp_weights / weight_total
        return dict(zip(criteria_names, normalized))
