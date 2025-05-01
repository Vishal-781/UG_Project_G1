import json
import matplotlib.pyplot as plt

# File paths for the JSON data
file_paths = [
    "results/cumulative_results_40000.json",
    "results/cumulative_result_30000.json",
    "results/cumulative_results_20000.json",
    "results/cumulative_results_10000.json",
    "results/cumulative_results_50000.json",
    "results/cumulative_results_60000.json",
    "results/cumulative_results_70000.json",
    "results/cumulative_results_823000.json"
]

TOTAL_IPS = 82230  # Total number of IPs

def load_and_combine_data(file_paths):
    """Load data from multiple JSON files and combine durations."""
    combined_durations = []
    
    for file_path in file_paths:
        with open(file_path, "r") as f:
            data = json.load(f)
            # Extract durations (second element of each entry)
            durations = [entry[1] for entry in data]
            combined_durations.extend(durations)
    
    return combined_durations

def plot_percentage_ips(durations):
    """Plot remaining percentage of IPs over time."""
    # Sort durations
    sorted_durations = sorted(durations)
    
    # Generate cumulative percentage
    cumulative_ips = list(range(1, len(sorted_durations) + 1))
    remaining_ips = [TOTAL_IPS - ip for ip in cumulative_ips]
    remaining_percentages = [(ip / TOTAL_IPS) * 100 for ip in remaining_ips]
    
    # Create scale points (10, 20, ..., 60 seconds)
    scale_points = list(range(10, 61, 10))
    
    # Filter data for scale points
    filtered_durations = [d for d in sorted_durations if d <= max(scale_points)]
    filtered_percentages = remaining_percentages[:len(filtered_durations)]
    
    # Plot the graph
    plt.figure(figsize=(12, 6))
    plt.plot(filtered_durations, filtered_percentages, color='blue')
    plt.title("Remaining Percentage of IPs Over Time")
    plt.xlabel("Duration (seconds)")
    plt.ylabel("Remaining Percentage of IPs (%)")
    plt.xticks(scale_points)  # Set x-axis scale to 10, 20, ..., 60
    plt.grid(True)
    plt.tight_layout()
    
    # Save and show the graph
    plt.savefig("remaining_ips_graph.png", dpi=300)
    print("Graph saved as 'remaining_ips_graph.png'.")
    plt.show()

# Main execution
if __name__ == "__main__":
    # Load and combine data from all files
    combined_durations = load_and_combine_data(file_paths)
    
    # Plot remaining percentage of IPs over time
    plot_percentage_ips(combined_durations)
