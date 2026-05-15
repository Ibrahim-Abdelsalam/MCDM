"""Streamlit UI for the MCDM Decision Support System."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Support both relative imports (module) and absolute imports (script run)
try:
    from .config import BASE_DIR, DEFAULT_VIKOR_V
    from .core.company_manager import CompanyManager
    from .core.criteria import CriteriaConfig
    from .core.dataset_generator import DatasetGenerator
    from .core.solver_engine import MCDMSolverEngine
    from .core.weight_manager import WeightSchemeManager
    from .export.chart_generator import ChartGenerator
    from .export.excel_exporter import ExcelExporter
except ImportError:
    # Add parent to path when run as script via streamlit
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.config import BASE_DIR, DEFAULT_VIKOR_V
    from app.core.company_manager import CompanyManager
    from app.core.criteria import CriteriaConfig
    from app.core.dataset_generator import DatasetGenerator
    from app.core.solver_engine import MCDMSolverEngine
    from app.core.weight_manager import WeightSchemeManager
    from app.export.chart_generator import ChartGenerator
    from app.export.excel_exporter import ExcelExporter


def init_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "company_manager" not in st.session_state:
        st.session_state.company_manager = CompanyManager()
    if "weight_manager" not in st.session_state:
        st.session_state.weight_manager = WeightSchemeManager()
    if "dataset_generator" not in st.session_state:
        st.session_state.dataset_generator = DatasetGenerator()
    if "solver_engine" not in st.session_state:
        st.session_state.solver_engine = MCDMSolverEngine()
    if "excel_exporter" not in st.session_state:
        st.session_state.excel_exporter = ExcelExporter()
    if "chart_generator" not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()


def page_home() -> None:
    """Home page with system overview."""
    st.title("Home")
    
    st.markdown("""
    # Multi-Criteria Decision Support System (MCDM DSS)
    
    A bidirectional evaluation platform using **AHP**, **TOPSIS**, and **VIKOR** methods.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Supplier Analysis")
        supplier_count = len(st.session_state.company_manager.list_companies("supplier"))
        supplier_schemes = len(st.session_state.weight_manager.list_schemes("supplier"))
        st.metric("Companies", supplier_count)
        st.metric("Weight Schemes", supplier_schemes)
    
    with col2:
        st.subheader("Buyer Analysis")
        buyer_count = len(st.session_state.company_manager.list_companies("buyer"))
        buyer_schemes = len(st.session_state.weight_manager.list_schemes("buyer"))
        st.metric("Companies", buyer_count)
        st.metric("Weight Schemes", buyer_schemes)


def page_manage_companies() -> None:
    """Manage company records."""
    st.title("Manage Companies")
    
    entity_type = st.radio("Select entity type:", ["Supplier", "Buyer"], horizontal=True)
    entity_type_lower = entity_type.lower()
    
    tab_add, tab_view = st.tabs(["Add Company", "View / Remove"])
    
    with tab_add:
        st.subheader("Add New Company")
        company_name = st.text_input("Company Name:", key="company_name_input")
        
        criteria_names = CriteriaConfig.get_criteria_names(entity_type_lower)
        scores = {}
        
        st.write("Enter scores for each criterion (1–10):")
        for criterion_name in criteria_names:
            scores[criterion_name] = st.number_input(criterion_name, value=5, min_value=1, max_value=10, step=1, key=f"score_{criterion_name}")
        
        if st.button("Save Company", key="save_company_btn"):
            try:
                st.session_state.company_manager.add_company(entity_type_lower, company_name, scores)
                st.success(f"Company '{company_name}' saved successfully!")
            except Exception as e:
                st.error(f"Error saving company: {e}")
    
    with tab_view:
        st.subheader("View / Remove Companies")
        company_names = st.session_state.company_manager.list_companies(entity_type_lower)
        
        if company_names:
            selected_company = st.selectbox("Select a company:", company_names, key="select_company")
            
            if st.button("Remove Company", key="remove_company_btn"):
                try:
                    st.session_state.company_manager.remove_company(entity_type_lower, selected_company)
                    st.success(f"Company '{selected_company}' removed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error removing company: {e}")
            
            # Show all companies as table
            df = st.session_state.company_manager.load_all_as_dataframe(entity_type_lower)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No companies found.")


def page_manage_weights() -> None:
    """Manage weight schemes."""
    st.title("Manage Weight Schemes")
    
    entity_type = st.radio("Select entity type:", ["Supplier", "Buyer"], horizontal=True, key="weights_entity_type")
    entity_type_lower = entity_type.lower()
    
    tab_create, tab_view = st.tabs(["Create Scheme", "View / Delete"])
    
    with tab_create:
        st.subheader("Create New Weight Scheme")
        scheme_name = st.text_input("Scheme Name:", key="scheme_name_input")
        
        criteria_names = CriteriaConfig.get_criteria_names(entity_type_lower)
        weights = {}
        
        st.write("Enter weights for each criterion (0–10):")
        for criterion_name in criteria_names:
            weights[criterion_name] = st.number_input(criterion_name, value=1.0, min_value=0.0, step=0.1, key=f"weight_{criterion_name}")
        
        # Show normalized weights preview
        total_weight = sum(weights.values())
        if total_weight > 0:
            st.write("**Normalized weights (preview):**")
            normalized = {k: v / total_weight for k, v in weights.items()}
            for criterion_name, norm_weight in normalized.items():
                percentage = norm_weight * 100
                st.write(f"{criterion_name}: {percentage:.1f}%")
        
        if st.button("Save Scheme", key="save_scheme_btn"):
            try:
                st.session_state.weight_manager.save_scheme(entity_type_lower, scheme_name, weights)
                st.success(f"Scheme '{scheme_name}' saved successfully!")
            except Exception as e:
                st.error(f"Error saving scheme: {e}")
    
    with tab_view:
        st.subheader("View / Delete Weight Schemes")
        scheme_names = st.session_state.weight_manager.list_schemes(entity_type_lower)
        
        if scheme_names:
            selected_scheme = st.selectbox("Select a scheme:", scheme_names, key="select_scheme")
            
            if st.button("Delete Scheme", key="delete_scheme_btn"):
                try:
                    st.session_state.weight_manager.delete_scheme(entity_type_lower, selected_scheme)
                    st.success(f"Scheme '{selected_scheme}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting scheme: {e}")
        else:
            st.info("No weight schemes found.")


def page_generate_data() -> None:
    """Generate synthetic test data."""
    st.title("Generate Test Data")
    
    entity_type = st.radio("Select entity type:", ["Supplier", "Buyer"], horizontal=True, key="gen_entity_type")
    entity_type_lower = entity_type.lower()
    
    n_entities = st.number_input("Number of entities:", value=100, min_value=10, max_value=10000, step=10)
    seed = st.number_input("Random seed (optional):", value=None, min_value=0, step=1)
    
    if st.button("Generate Dataset", key="generate_btn"):
        try:
            with st.spinner("Generating dataset..."):
                dataset = st.session_state.dataset_generator.generate(entity_type_lower, n_entities, seed=seed)
            st.success(f"Generated {n_entities} {entity_type_lower} records!")
            
            st.write("**Preview (first 5 rows):**")
            st.dataframe(dataset.head(), use_container_width=True)
        except Exception as e:
            st.error(f"Error generating dataset: {e}")


def page_run_analysis() -> None:
    """Run MCDM analysis."""
    st.title("Run Analysis")
    
    st.subheader("Step 1: Select Entity Type")
    entity_type = st.radio("Entity type:", ["Supplier", "Buyer"], horizontal=True, key="run_entity_type")
    entity_type_lower = entity_type.lower()
    
    st.subheader("Step 2: Select Data Source")
    data_source = st.radio("Data source:", ["Real Companies", "Generated Dataset"], horizontal=True)
    
    company_count = len(st.session_state.company_manager.list_companies(entity_type_lower))
    dataset_path = st.session_state.dataset_generator._dataset_path(entity_type_lower)
    
    if data_source == "Real Companies":
        if company_count == 0:
            st.warning(f"No {entity_type_lower} companies found. Please add companies first.")
            return
        st.info(f"{company_count} companies loaded.")
        scores_df = st.session_state.company_manager.load_all_as_dataframe(entity_type_lower)
    else:
        if not dataset_path.exists():
            st.warning(f"No generated dataset found. Please generate data first.")
            return
        import pandas as pd
        scores_df = pd.read_csv(dataset_path)
        st.info(f"Dataset with {len(scores_df)} records loaded.")
    
    st.subheader("Step 3: Select Weight Schemes")
    available_schemes = st.session_state.weight_manager.list_schemes(entity_type_lower)
    if not available_schemes:
        st.warning("No weight schemes found. Please create at least one scheme.")
        return
    
    selected_schemes = st.multiselect("Choose weight schemes:", available_schemes)
    if not selected_schemes:
        st.warning("Please select at least one weight scheme.")
        return
    
    st.subheader("Step 4: Select MCDM Methods")
    methods = []
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.checkbox("AHP", value=True):
            methods.append("AHP")
    with col2:
        if st.checkbox("TOPSIS", value=True):
            methods.append("TOPSIS")
    with col3:
        if st.checkbox("VIKOR", value=True):
            methods.append("VIKOR")
    
    if not methods:
        st.warning("Please select at least one method.")
        return
    
    # Show v parameter only if VIKOR is selected
    v_param = DEFAULT_VIKOR_V
    if "VIKOR" in methods:
        st.subheader("Step 5: VIKOR Parameter")
        v_param = st.number_input("v parameter (0=regret-averse, 0.5=balanced, 1=utility-focused):", value=DEFAULT_VIKOR_V, min_value=0.0, max_value=1.0, step=0.01)
    
    if st.button("Run Analysis", key="run_analysis_btn"):
        try:
            with st.spinner("Running analysis..."):
                analysis_results = {}
                for scheme_name in selected_schemes:
                    for method in methods:
                        result = st.session_state.solver_engine.run_analysis(
                            entity_type_lower,
                            scores_df,
                            [scheme_name],
                            [method],
                            v=v_param,
                        )
                        key = f"{method}_{scheme_name.replace(' ', '_').replace('-', '_')[:20].lower()}"
                        analysis_results[key] = result
                
                st.success("Analysis complete!")
                
                # Show summary table
                st.subheader("Summary - Top 5 Results")
                import pandas as pd
                
                # Reorganize results for display and export
                display_results = {}
                summary_data = []
                
                for key, result_df in analysis_results.items():
                    # Find the rank and score columns (they have the key in their name)
                    rank_cols = [col for col in result_df.columns if "Rank" in col]
                    score_cols = [col for col in result_df.columns if "Score" in col]
                    
                    if rank_cols and score_cols:
                        rank_col = rank_cols[0]
                        score_col = score_cols[0]
                        
                        # Get top 5 by rank
                        top_5 = result_df.nsmallest(5, rank_col)
                        
                        # Prepare for display
                        for _, row in top_5.iterrows():
                            method_name = key.split("_")[0]
                            scheme_name = "_".join(key.split("_")[1:])
                            summary_data.append({
                                "Method": method_name,
                                "Scheme": scheme_name,
                                "Rank": int(row[rank_col]),
                                "Company_ID": str(row["ID"]),
                                "Score": f"{float(row[score_col]):.4f}",
                            })
                        
                        # Prepare for export (create a clean dataframe with ID, Score, Rank)
                        export_df = result_df[["ID", score_col, rank_col]].copy()
                        export_df.columns = ["ID", "Score", "Rank"]
                        display_results[key] = export_df
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True)
                
                # Generate and display charts
                st.subheader("Visualizations")
                chart_paths = st.session_state.chart_generator.generate_all_charts(display_results, entity_type_lower)
                for chart_path in chart_paths:
                    if chart_path.exists():
                        st.image(str(chart_path), use_container_width=True)
                
                # Generate and offer Excel export
                st.subheader("Export Results")
                excel_path = st.session_state.excel_exporter.export(entity_type_lower, display_results)
                with open(excel_path, "rb") as f:
                    st.download_button(
                        label="Download Excel Report",
                        data=f.read(),
                        file_name=excel_path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
        
        except Exception as e:
            st.error(f"Error running analysis: {e}")


def main() -> None:
    """Main Streamlit app."""
    st.set_page_config(page_title="MCDM DSS", layout="wide")
    init_session_state()
    
    pages = {
        "Home": page_home,
        "Manage Companies": page_manage_companies,
        "Manage Weight Schemes": page_manage_weights,
        "Generate Test Data": page_generate_data,
        "Run Analysis": page_run_analysis,
    }
    
    page = st.sidebar.radio("Navigation:", list(pages.keys()))
    pages[page]()


if __name__ == "__main__":
    main()
