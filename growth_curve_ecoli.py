import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Streamlit App Title
st.title("Multi-Plot OD600 Growth Curve Visualization")

# **User input fields (All time data in MINUTES)**
default_time_input = "0,30,60,90,120,150,180, 1440; 0,30,60,90,120,150,180,1440"  # Time in minutes
default_density_input = "0.038, 0.042, 0.066, 0.112, 0.2, 0.3, 0.37, 2.6; 0.062, 0.072, 0.110, 0.184, 0.278, 0.424, 0.516, 2.188"
default_trend_time_input = "30,60,90,120,150; 30,60,90,120,150"
default_std_dev_input = "0.005,0.01,0.02,0.03,0.04,0.05,0.06; 0.006,0.012,0.022,0.032,0.042,0.052,0.062"
default_dataset_names = "Sample C (LB + ara + Glu); Sample E (LB)"

time_input = st.text_area("Enter time points in minutes (semicolon-separated sets):", default_time_input)
density_input = st.text_area("Enter OD600 values for multiple datasets (semicolon-separated sets):", default_density_input)
trend_time_input = st.text_area("Enter time points for trendline calculation in minutes (semicolon-separated sets):", default_trend_time_input)
std_dev_input = st.text_area("Enter standard deviations for OD600 (semicolon-separated sets, optional):", default_std_dev_input)
dataset_names_input = st.text_area("Enter dataset names (semicolon-separated, optional):", default_dataset_names)

# **Checkbox to toggle trendlines**
show_trendlines = st.checkbox("Show Trend Lines", value=True)

# **Define color map for multiple plots**
colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown', 'pink', 'gray']

# **Button to update the graph**
if st.button("Update Graph"):

    try:
        # **Convert inputs to numpy arrays**
        time_sets = [np.array([float(x.strip()) for x in dataset.split(",")]) for dataset in time_input.split(";")]
        density_sets = [np.array([float(x.strip()) for x in dataset.split(",")]) for dataset in density_input.split(";")]
        trend_time_sets = [np.array([float(x.strip()) for x in dataset.split(",")]) for dataset in trend_time_input.split(";")]

        # **Check if standard deviations are provided**
        std_dev_sets = []
        if std_dev_input.strip():
            std_dev_sets = [np.array([float(x.strip()) for x in dataset.split(",")]) for dataset in std_dev_input.split(";")]

        # **Check if dataset names are provided**
        dataset_names = dataset_names_input.split(";") if dataset_names_input.strip() else [f"Dataset {i+1}" for i in range(len(time_sets))]

        # **Ensure proper dataset alignment**
        if len(time_sets) != len(density_sets) or len(time_sets) != len(trend_time_sets):
            st.error("Error: Each dataset must have the same number of time, density, and trendline sets.")
        elif std_dev_sets and len(std_dev_sets) != len(density_sets):
            st.error("Error: If provided, standard deviations must match the number of OD600 datasets.")
        elif len(dataset_names) != len(density_sets):
            st.error("Error: Number of dataset names must match the number of datasets.")
        else:
            fig, ax = plt.subplots(figsize=(8, 5))

            # **Loop through multiple datasets**
            for i, (time_values, od600_values, trend_time_points, dataset_name) in enumerate(zip(time_sets, density_sets, trend_time_sets, dataset_names)):

                # **Extract corresponding OD600 values for trendline points**
                trend_indices = np.isin(time_values, trend_time_points)
                trend_od600_values = od600_values[trend_indices]

                if len(trend_od600_values) != len(trend_time_points):
                    st.error(f"Error: The selected trendline time points do not match valid OD600 data points in dataset {dataset_name}.")
                    continue

                # **Calculate ln(OD600) for selected trendline points**
                ln_y_trend = np.log(trend_od600_values)

                # **Compute slope (growth rate) using (ln(N2) - ln(N1)) / (t2 - t1) in minutes**
                m = (ln_y_trend[-1] - ln_y_trend[0]) / (trend_time_points[-1] - trend_time_points[0])

                # **Compute intercept for y = mx + b -> b = ln(N1) - m * t1**
                b = ln_y_trend[0] - m * trend_time_points[0]

                # **Generate the trendline based on the growth rate**
                trendline_y = np.exp(m * trend_time_points + b)  # Convert back from ln scale

                # **Compute doubling time (Td) using Td = ln(2) / m in minutes**
                Td = (np.log(2) / m) if m > 0 else None

                # **Check if standard deviations exist for this dataset**
                std_devs = std_dev_sets[i] if std_dev_sets else None

                # **Add scatter plot with error bars if available**
                if std_devs is not None and len(std_devs) == len(od600_values):
                    ax.errorbar(time_values, od600_values, yerr=std_devs, fmt='o', color=colors[i % len(colors)], capsize=5, label=f'{dataset_name} (Observed)')
                else:
                    ax.scatter(time_values, od600_values, color=colors[i % len(colors)], label=f'{dataset_name} (Observed)')

                # **Add the calculated trendline if checkbox is checked**
                if show_trendlines:
                    ax.plot(trend_time_points, trendline_y, linestyle='--', color=colors[i % len(colors)], label=f'{dataset_name} Trend (m={m:.4f})')

                # **Display the computed doubling time**
                if Td:
                    st.success(f"**{dataset_name} Doubling Time (Td): {Td:.2f} minutes**")
                else:
                    st.warning(f"{dataset_name}: Growth rate is non-positive; doubling time cannot be calculated.")

            # **Set log scale for Y-axis and define limits**
            ax.set_yscale("log")
            ax.set_ylim(0.01, 6)  # Minimum OD600 at 0.01, maximum capped at 6
            ax.set_xlim(-50, None)  # Slight offset on X-axis

            # **Labels and title with increased font sizes**
            ax.set_xlabel("Time (minutes)", fontsize=14, fontweight='bold')
            ax.set_ylabel("OD600", fontsize=14, fontweight='bold')
            ax.set_title("OD600 Growth Curve", fontsize=16, fontweight='bold')

            # **Customize legend and grid**
            ax.legend(fontsize=10, frameon=True, loc='upper left', bbox_to_anchor=(1.05, 1))
            ax.grid(True, which="both", linestyle="--", linewidth=0.5)

            # **Show the plot in Streamlit**
            st.pyplot(fig)

    except ValueError:
        st.error("Error: Please ensure all inputs are valid numbers and properly formatted.")
